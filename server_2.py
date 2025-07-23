import time, uuid, random, csv, io, sqlite3
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_socketio import SocketIO, emit
from threading import Thread, RLock

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

def init_db():
    conn = sqlite3.connect("cluster.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS event_logs (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  message TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS utilization_history (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  utilization REAL
                )""")
    conn.commit()
    conn.close()

def insert_event_log(message):
    conn = sqlite3.connect("cluster.db")
    c = conn.cursor()
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(get_current_timestamp()))
    c.execute("INSERT INTO event_logs (timestamp, message) VALUES (?, ?)", (ts, message))
    conn.commit()
    conn.close()

def insert_utilization(ts, utilization):
    conn = sqlite3.connect("cluster.db")
    c = conn.cursor()
    ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    c.execute("INSERT INTO utilization_history (timestamp, utilization) VALUES (?, ?)", (ts_str, utilization))
    conn.commit()
    conn.close()

nodes = {}  
event_log = []  
utilization_history = []  
nodes_lock = RLock()
pod_id_lock = RLock()
pod_id_counter = 0

DEFAULT_NODE_CPU = 8
DEFAULT_NODE_MEMORY = 16 
DEFAULT_POD_MEMORY = 4   
#
# Auto-scaling & Health Monitoring Parameters:
AUTO_SCALE_THRESHOLD = 0.8      # 80% CPU utilization threshold
AUTO_SCALE_COOLDOWN = 60        # seconds between auto-scale actions
last_auto_scale_time = 0
HEARTBEAT_THRESHOLD = 15        # seconds without heartbeat before marking node as failed
HEALTH_CHECK_INTERVAL = 5       # interval for health checks
SCHEDULING_ALGORITHMS = ['first_fit', 'best_fit', 'worst_fit']

# ----------------------------------
# Utility Functions
# ----------------------------------
def get_current_timestamp():
    return time.time()

def log_event_func(event):
    """Logs an event in memory and inserts it into the DB."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(get_current_timestamp()))
    entry = f"[{timestamp}] {event}"
    with nodes_lock:
        event_log.append(entry)
        if len(event_log) > 50:
            event_log.pop(0)
    insert_event_log(event)

def record_utilization():
    while True:
        time.sleep(10)
        util = get_cluster_utilization() * 100  # as a percentage
        ts = get_current_timestamp()
        with nodes_lock:
            utilization_history.append((ts, util))
            if len(utilization_history) > 50:
                utilization_history.pop(0)
        insert_utilization(ts, util)

def get_cluster_utilization():
    total_cpu = 0
    used_cpu = 0
    with nodes_lock:
        for node in nodes.values():
            if node["status"] == "active":
                total_cpu += node["cpu_total"]
                used_cpu += (node["cpu_total"] - node["cpu_available"])
    return 0.0 if total_cpu == 0 else used_cpu / total_cpu

# ----------------------------------
# Extended Scheduling (Phase 1 Enhancements)
# ----------------------------------
def schedule_pod(pod, scheduling_algorithm):
    """
    Schedules a pod onto a node if sufficient CPU and memory are available.
    Additionally, ensures the node's network_group matches the pod's network_group.
    If the pod has "node_affinity" specified, only nodes of that type are considered.
    """
    candidate = None
    with nodes_lock:
        eligible = [
            node for node in nodes.values()
            if node["status"] == "active" and 
               node["cpu_available"] >= pod["cpu"] and 
               node["memory_available"] >= pod["memory"] and 
               node.get("network_group", "default") == pod.get("network_group", "default")
        ]
        # If the pod specifies node affinity (i.e. a desired node_type), apply that filter.
        if "node_affinity" in pod:
            affinity = pod["node_affinity"]
            eligible = [node for node in eligible if node.get("node_type", "balanced") == affinity]
        if not eligible:
            return False, None
        if scheduling_algorithm == "first_fit":
            candidate = eligible[0]
        elif scheduling_algorithm == "best_fit":
            candidate = min(eligible, key=lambda n: (n["cpu_available"] - pod["cpu"]) + (n["memory_available"] - pod["memory"]))
        elif scheduling_algorithm == "worst_fit":
            candidate = max(eligible, key=lambda n: n["cpu_available"] + n["memory_available"])
        if candidate:
            candidate["pods"].append(pod)
            candidate["cpu_available"] -= pod["cpu"]
            candidate["memory_available"] -= pod["memory"]
            log_event_func(f"Pod {pod['pod_id']} scheduled on node {candidate['node_id']} using {scheduling_algorithm}")
            return True, candidate["node_id"]
    return False, None

# ----------------------------------
# Background Tasks
# ----------------------------------
def auto_scale_cluster():
    global last_auto_scale_time
    while True:
        time.sleep(HEALTH_CHECK_INTERVAL)
        util = get_cluster_utilization()
        now = get_current_timestamp()
        if (util >= AUTO_SCALE_THRESHOLD) and ((now - last_auto_scale_time) >= AUTO_SCALE_COOLDOWN):
            node_id = str(uuid.uuid4())
            # For demonstration, we randomly assign a node_type and network_group.
            node_type = random.choice(["high_cpu", "high_mem", "balanced"])
            network_group = random.choice(["default", "isolated"])
            with nodes_lock:
                nodes[node_id] = {
                    "node_id": node_id,
                    "cpu_total": DEFAULT_NODE_CPU,
                    "cpu_available": DEFAULT_NODE_CPU,
                    "memory_total": DEFAULT_NODE_MEMORY,
                    "memory_available": DEFAULT_NODE_MEMORY,
                    "node_type": node_type,
                    "network_group": network_group,
                    "pods": [],
                    "last_heartbeat": get_current_timestamp(),
                    "status": "active",
                    "simulate_heartbeat": True
                }
            log_event_func(f"Auto-scaled: Added node {node_id} ({DEFAULT_NODE_CPU} CPU, {DEFAULT_NODE_MEMORY}GB, Type: {node_type}, Network Group: {network_group})")
            last_auto_scale_time = now

def health_monitor():
    while True:
        time.sleep(HEALTH_CHECK_INTERVAL)
        now = get_current_timestamp()
        failed = []
        with nodes_lock:
            for nid, node in list(nodes.items()):
                if node["status"] == "active" and (now - node["last_heartbeat"]) > HEARTBEAT_THRESHOLD:
                    node["status"] = "failed"
                    log_event_func(f"Health Monitor: Node {nid} marked as FAILED")
                    failed.append(nid)
        for nid in failed:
            reschedule_pods_from_failed_node(nid)
            socketio.emit("alert", {"msg": f"Node {nid} failed!"})

def reschedule_pods_from_failed_node(node_id):
    with nodes_lock:
        failed_node = nodes.get(node_id)
        if not failed_node:
            return
        pods_to_reschedule = failed_node.get("pods", [])
        failed_node["pods"] = []
    for pod in pods_to_reschedule:
        scheduled, new_nid = schedule_pod(pod, "first_fit")
        if scheduled:
            log_event_func(f"Rescheduled pod {pod['pod_id']} from node {node_id} to node {new_nid}")
        else:
            log_event_func(f"Reschedule failure: Pod {pod['pod_id']} from node {node_id} not placed")

def simulate_heartbeat_thread():
    while True:
        time.sleep(7)
        with nodes_lock:
            for node in nodes.values():
                if node.get("simulate_heartbeat", False):
                    node["last_heartbeat"] = get_current_timestamp()

def simulate_pod_usage():
    with nodes_lock:
        for node in nodes.values():
            if node["status"] == "active":
                for pod in node["pods"]:
                    pod["cpu_usage"] = round(random.uniform(0.5, 1.0) * pod["cpu"], 2)

def chaos_monkey():
    with nodes_lock:
        if not nodes:
            log_event_func("Chaos Monkey: No nodes available")
            return {"message": "No nodes to target"}
        if random.random() < 0.5:
            active_nodes = [n for n in nodes.values() if n["status"] == "active"]
            if active_nodes:
                target = random.choice(active_nodes)
                target["status"] = "failed"
                target["simulate_heartbeat"] = False
                log_event_func(f"Chaos Monkey: Node {target['node_id']} was killed")
                return {"message": f"Chaos Monkey killed node {target['node_id']}"}
            else:
                log_event_func("Chaos Monkey: No active nodes to kill")
                return {"message": "No active nodes to kill"}
        else:
            nodes_with_pods = [n for n in nodes.values() if n["pods"]]
            if nodes_with_pods:
                target_node = random.choice(nodes_with_pods)
                target_pod = random.choice(target_node["pods"])
                target_node["cpu_available"] += target_pod["cpu"]
                target_node["memory_available"] += target_pod["memory"]
                target_node["pods"].remove(target_pod)
                log_event_func(f"Chaos Monkey: Pod {target_pod['pod_id']} on node {target_node['node_id']} was killed")
                return {"message": f"Chaos Monkey killed pod {target_pod['pod_id']} on node {target_node['node_id']}"}
            else:
                log_event_func("Chaos Monkey: No pods to kill")
                return {"message": "No pods to kill"}

def broadcast_state():
    while True:
        time.sleep(3)
        with nodes_lock:
            simulate_pod_usage()
            state = {
                "nodes": list(nodes.values()),
                "logs": event_log[-50:],
                "history": [{"timestamp": ts, "utilization": util} for ts, util in utilization_history]
            }
        socketio.emit("state_update", state)

# ----------------------------------
# API Endpoints
# ----------------------------------
@app.route('/add_node', methods=['POST'])
def add_node_endpoint():
    data = request.get_json()
    if not data or "cpu" not in data:
        return jsonify({"error": "Missing CPU core specification"}), 400
    cpu = data["cpu"]
    memory = data.get("memory", DEFAULT_NODE_MEMORY)
    node_type = data.get("node_type", "balanced")
    network_group = data.get("network_group", "default")
    node_id = str(uuid.uuid4())
    with nodes_lock:
        nodes[node_id] = {
            "node_id": node_id,
            "cpu_total": cpu,
            "cpu_available": cpu,
            "memory_total": memory,
            "memory_available": memory,
            "node_type": node_type,
            "network_group": network_group,
            "pods": [],
            "last_heartbeat": get_current_timestamp(),
            "status": "active",
            "simulate_heartbeat": True
        }
    log_event_func(f"Added node {node_id} with {cpu} CPU, {memory}GB Memory, Type: {node_type}, Network Group: {network_group}")
    return jsonify({"message": "Node added successfully", "node_id": node_id}), 200

@app.route('/remove_node', methods=['POST'])
def remove_node_endpoint():
    data = request.get_json()
    if not data or "node_id" not in data:
        return jsonify({"error": "Missing node_id"}), 400
    node_id = data["node_id"]
    with nodes_lock:
        if node_id in nodes:
            del nodes[node_id]
            log_event_func(f"Removed node {node_id}")
            return jsonify({"message": f"Node {node_id} removed"}), 200
        else:
            return jsonify({"error": "Node not found"}), 404

@app.route('/toggle_simulation', methods=['POST'])
def toggle_simulation_endpoint():
    data = request.get_json()
    if not data or "node_id" not in data or "simulate" not in data:
        return jsonify({"error": "Missing node_id or simulate flag"}), 400
    node_id = data["node_id"]
    simulate = bool(data["simulate"])
    with nodes_lock:
        node = nodes.get(node_id)
        if node:
            node["simulate_heartbeat"] = simulate
            log_event_func(f"Simulation for node {node_id} set to {simulate}")
            return jsonify({"message": f"Node {node_id} simulation set to {simulate}"}), 200
        else:
            return jsonify({"error": "Node not found"}), 404

@app.route('/list_nodes', methods=['GET'])
def list_nodes_endpoint():
    with nodes_lock:
        node_list = list(nodes.values())
    return jsonify({"nodes": node_list}), 200

@app.route('/launch_pod', methods=['POST'])
def launch_pod_endpoint():
    data = request.get_json()
    if not data or "cpu_required" not in data:
        return jsonify({"error": "Missing pod CPU requirement"}), 400
    cpu_required = data["cpu_required"]
    memory_required = data.get("memory_required", DEFAULT_POD_MEMORY)
    scheduling_algorithm = data.get("scheduling_algorithm", "first_fit").lower()
    if scheduling_algorithm not in SCHEDULING_ALGORITHMS:
        scheduling_algorithm = "first_fit"
    network_group = data.get("network_group", "default")
    # Optional: Node affinity for pod scheduling
    node_affinity = data.get("node_affinity", None)
    global pod_id_counter
    with pod_id_lock:
        pod_id_counter += 1
        pod_id = f"pod_{pod_id_counter}"
    pod = {
        "pod_id": pod_id,
        "cpu": cpu_required,
        "memory": memory_required,
        "network_group": network_group,
        "cpu_usage": 0
    }
    if node_affinity:
        pod["node_affinity"] = node_affinity
    scheduled, assigned_node_id = schedule_pod(pod, scheduling_algorithm)
    if scheduled:
        return jsonify({
            "message": "Pod launched successfully",
            "pod_id": pod_id,
            "assigned_node": assigned_node_id,
            "scheduling_algorithm": scheduling_algorithm
        }), 200
    else:
        return jsonify({"error": "No available node with sufficient resources"}), 400

@app.route('/heartbeat', methods=['POST'])
def heartbeat_endpoint():
    data = request.get_json()
    if not data or "node_id" not in data:
        return jsonify({"error": "Missing node_id"}), 400
    node_id = data["node_id"]
    with nodes_lock:
        node = nodes.get(node_id)
        if node:
            node["last_heartbeat"] = get_current_timestamp()
            if node["status"] == "failed":
                node["status"] = "active"
                log_event_func(f"Node {node_id} reactivated after heartbeat")
            return jsonify({"message": "Heartbeat updated"}), 200
        else:
            return jsonify({"error": "Unknown node_id"}), 404

@app.route('/chaos_monkey', methods=['POST'])
def chaos_monkey_endpoint():
    result = chaos_monkey()
    return jsonify(result), 200

@app.route('/download_report', methods=['GET'])
def download_report_endpoint():
    with nodes_lock:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Node ID", "CPU Total", "CPU Available", "Memory Total (GB)", "Memory Available (GB)", "Status", "Node Type", "Network Group", "Pods"])
        for node in nodes.values():
            pods_desc = "; ".join([f"{p['pod_id']} (CPU:{p['cpu']}, Mem:{p['memory']})" for p in node["pods"]])
            writer.writerow([node["node_id"], node["cpu_total"], node["cpu_available"],
                             node.get("memory_total", DEFAULT_NODE_MEMORY), node.get("memory_available", DEFAULT_NODE_MEMORY),
                             node["status"], node.get("node_type", "balanced"), node.get("network_group", "default"), pods_desc])
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode("utf-8")),
                         mimetype="text/csv",
                         as_attachment=True,
                         download_name="cluster_report.csv")

@app.route('/logs', methods=['GET'])
def logs_endpoint():
    with nodes_lock:
        return jsonify({"logs": event_log}), 200

@app.route('/utilization_history', methods=['GET'])
def utilization_history_endpoint():
    with nodes_lock:
        history = [{"timestamp": ts, "utilization": util} for ts, util in utilization_history]
    return jsonify({"history": history}), 200

# ----------------------------------
# Advanced Dashboard Endpoint
# ----------------------------------
@app.route('/dashboard')
def dashboard_endpoint():
    advanced_dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Insane Cluster Dashboard</title>
      <!-- jQuery -->
      <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
      <!-- Bootstrap 4.6 -->
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
      <!-- AdminLTE -->
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/css/adminlte.min.css">
      <script src="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/js/adminlte.min.js"></script>
      <!-- Font Awesome -->
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
      <!-- Chart.js -->
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <!-- ECharts and ECharts-GL for 3D charts -->
      <script src="https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/echarts-gl/dist/echarts-gl.min.js"></script>
      <!-- Socket.IO client -->
      <script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
      <style>
        #log-panel { height: 200px; overflow-y: scroll; background: #f4f6f9; padding: 10px; border: 1px solid #ddd; }
        #nodeGraph { height: 400px; }
        .dark-mode { background-color: #343a40 !important; color: #f8f9fa !important; }
      </style>
    </head>
    <body class="hold-transition sidebar-mini">
      <div class="wrapper">
        <!-- Navbar -->
        <nav class="main-header navbar navbar-expand navbar-white navbar-light">
          <ul class="navbar-nav">
            <li class="nav-item">
              <a class="nav-link" data-widget="pushmenu" href="#" role="button"><i class="fas fa-bars"></i></a>
            </li>
            <li class="nav-item d-none d-sm-inline-block">
              <a href="/dashboard" class="nav-link">Dashboard</a>
            </li>
          </ul>
          <ul class="navbar-nav ml-auto">
            <!-- Dark Mode Toggle -->
            <li class="nav-item">
              <button id="dark-toggle" class="btn btn-outline-dark nav-link">Dark Mode</button>
            </li>
            <li class="nav-item">
              <button id="chaos-btn" class="btn btn-danger nav-link">Chaos Monkey</button>
            </li>
            <li class="nav-item">
              <a href="/download_report" class="btn btn-success nav-link" target="_blank">Download Report</a>
            </li>
          </ul>
        </nav>
        <!-- Sidebar -->
        <aside class="main-sidebar sidebar-dark-primary elevation-4">
          <a href="/dashboard" class="brand-link">
            <i class="fas fa-server brand-image img-circle elevation-3"></i>
            <span class="brand-text font-weight-light">Insane Cluster</span>
          </a>
          <div class="sidebar">
            <nav class="mt-2">
              <ul class="nav nav-pills nav-sidebar flex-column" role="menu">
                <li class="nav-item">
                  <a href="/dashboard" class="nav-link active">
                    <i class="nav-icon fas fa-tachometer-alt"></i>
                    <p>Dashboard</p>
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </aside>
        <!-- Content Wrapper -->
        <div class="content-wrapper">
          <!-- Content Header -->
          <div class="content-header">
            <div class="container-fluid">
              <div class="row mb-2">
                <div class="col-sm-6">
                  <h1 class="m-0">Cluster Overview</h1>
                </div>
                <div class="col-sm-6 text-right">
                  <button id="refresh-btn" class="btn btn-secondary">Refresh Now</button>
                </div>
              </div>
            </div>
          </div>
          <!-- Main Content -->
          <section class="content">
            <div class="container-fluid">
              <!-- Overview Cards -->
              <div class="row">
                <div class="col-lg-4 col-6">
                  <div class="small-box bg-info">
                    <div class="inner">
                      <h3 id="active-nodes">0</h3>
                      <p>Active Nodes</p>
                    </div>
                    <div class="icon">
                      <i class="fas fa-server"></i>
                    </div>
                  </div>
                </div>
                <div class="col-lg-4 col-6">
                  <div class="small-box bg-success">
                    <div class="inner">
                      <h3 id="utilization">0%</h3>
                      <p>Cluster Utilization</p>
                    </div>
                    <div class="icon">
                      <i class="fas fa-chart-line"></i>
                    </div>
                  </div>
                </div>
                <div class="col-lg-4 col-6">
                  <div class="small-box bg-warning">
                    <div class="inner">
                      <h3 id="total-nodes">0</h3>
                      <p>Total Nodes</p>
                    </div>
                    <div class="icon">
                      <i class="fas fa-list"></i>
                    </div>
                  </div>
                </div>
              </div>
              <!-- Node Details Table -->
              <div class="card">
                <div class="card-header">
                  <h3 class="card-title">Node Details</h3>
                  <div class="card-tools">
                    <button class="btn btn-primary btn-sm" data-toggle="modal" data-target="#addNodeModal">Add Node</button>
                    <button class="btn btn-primary btn-sm" data-toggle="modal" data-target="#launchPodModal">Launch Pod</button>
                  </div>
                </div>
                <div class="card-body table-responsive p-0">
                  <table class="table table-hover" id="nodes-table">
                    <thead>
                      <tr>
                        <th>Node ID</th>
                        <th>Type</th>
                        <th>CPU (Total/Avail)</th>
                        <th>Mem (Total/Avail)</th>
                        <th>Status</th>
                        <th>Pods</th>
                        <th>Sim</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <!-- Filled by JavaScript -->
                    </tbody>
                  </table>
                </div>
              </div>
              <!-- Charts Row -->
              <div class="row">
                <div class="col-md-6">
                  <div class="card card-outline card-success">
                    <div class="card-header">
                      <h3 class="card-title">CPU Distribution</h3>
                    </div>
                    <div class="card-body">
                      <canvas id="cpuChart" style="height:200px"></canvas>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="card card-outline card-info">
                    <div class="card-header">
                      <h3 class="card-title">Utilization History</h3>
                    </div>
                    <div class="card-body">
                      <canvas id="utilChart" style="height:200px"></canvas>
                    </div>
                  </div>
                </div>
              </div>
              <!-- 3D Node Graph -->
              <div class="card">
                <div class="card-header">
                  <h3 class="card-title">3D Node Graph</h3>
                </div>
                <div class="card-body">
                  <div id="nodeGraph" style="height:400px;"></div>
                </div>
              </div>
              <!-- Event Log -->
              <div class="card">
                <div class="card-header">
                  <h3 class="card-title">Event Log</h3>
                </div>
                <div class="card-body">
                  <div id="log-panel"></div>
                </div>
              </div>
            </div>
          </section>
        </div>
        <!-- Footer -->
        <footer class="main-footer">
          <strong>&copy; 2025 Insane Cluster Dashboard.</strong> All rights reserved.
        </footer>
      </div>

      <!-- Modals -->
      <!-- Add Node Modal -->
      <div class="modal fade" id="addNodeModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h4 class="modal-title">Add Node</h4>
              <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
              <form id="addNodeForm">
                <div class="form-group">
                  <label for="cpuInput">CPU Cores</label>
                  <input type="number" class="form-control" id="cpuInput" placeholder="e.g., 8" required>
                </div>
                <div class="form-group">
                  <label for="memoryInput">Memory (GB)</label>
                  <input type="number" class="form-control" id="memoryInput" placeholder="e.g., 16" required>
                </div>
                <div class="form-group">
                  <label for="nodeTypeInput">Node Type</label>
                  <select id="nodeTypeInput" class="form-control">
                    <option value="balanced" selected>Balanced</option>
                    <option value="high_cpu">High CPU</option>
                    <option value="high_mem">High Memory</option>
                  </select>
                </div>
                <div class="form-group">
                  <label for="nodeGroupInput">Network Group</label>
                  <input type="text" class="form-control" id="nodeGroupInput" placeholder="default">
                </div>
                <button type="submit" class="btn btn-success">Add Node</button>
              </form>
            </div>
          </div>
        </div>
      </div>
      <!-- Launch Pod Modal -->
      <div class="modal fade" id="launchPodModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h4 class="modal-title">Launch Pod</h4>
              <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
              <form id="launchPodForm">
                <div class="form-group">
                  <label for="cpuRequired">CPU Required</label>
                  <input type="number" class="form-control" id="cpuRequired" placeholder="e.g., 2" required>
                </div>
                <div class="form-group">
                  <label for="memoryRequired">Memory Required (GB)</label>
                  <input type="number" class="form-control" id="memoryRequired" placeholder="e.g., 4">
                </div>
                <div class="form-group">
                  <label for="schedulingAlgorithm">Scheduling Algorithm</label>
                  <select class="form-control" id="schedulingAlgorithm">
                    <option value="first_fit">First Fit</option>
                    <option value="best_fit">Best Fit</option>
                    <option value="worst_fit">Worst Fit</option>
                  </select>
                </div>
                <div class="form-group">
                  <label for="networkGroup">Network Group</label>
                  <input type="text" class="form-control" id="networkGroup" placeholder="default">
                </div>
                <div class="form-group">
                  <label for="nodeAffinity">Node Affinity (Optional)</label>
                  <select class="form-control" id="nodeAffinity">
                    <option value="" selected>Any</option>
                    <option value="high_cpu">High CPU</option>
                    <option value="high_mem">High Memory</option>
                    <option value="balanced">Balanced</option>
                  </select>
                </div>
                <button type="submit" class="btn btn-primary">Launch Pod</button>
              </form>
            </div>
          </div>
        </div>
      </div>
      <!-- Settings Modal (Future use) -->
      <div class="modal fade" id="settingsModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h4 class="modal-title">Advanced Settings</h4>
              <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
              <p>Configure thresholds, heartbeat intervals, etc.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Dashboard JavaScript -->
      <script>
        var socket = io();
        socket.on("state_update", function(state) {
          updateDashboard(state);
          updateNodeGraph(state.nodes);
        });

        function updateDashboard(state) {
          var nodes = state.nodes;
          var totalCPU = 0, activeCount = 0;
          var tbody = "";
          var usedCPUs = [];
          nodes.forEach(function(node) {
            totalCPU += node.cpu_total;
            if (node.status === "active") activeCount++;
            usedCPUs.push({ node_id: node.node_id, used: node.cpu_total - node.cpu_available });
            var pods = "";
            if (node.pods.length > 0) {
              node.pods.forEach(function(pod) {
                pods += pod.pod_id + " (CPU:" + pod.cpu + ", Mem:" + pod.memory + ")<br>";
              });
            } else {
              pods = "None";
            }
            var simEnabled = node.simulate_heartbeat;
            var simBtnLabel = simEnabled ? "Disable" : "Enable";
            var nextSim = simEnabled ? "false" : "true";
            tbody += "<tr>";
            tbody += "<td>" + node.node_id + "</td>";
            tbody += "<td>" + (node.node_type || "balanced") + "</td>";
            tbody += "<td>" + node.cpu_total + " / " + node.cpu_available + "</td>";
            tbody += "<td>" + node.memory_total + " / " + node.memory_available + " GB</td>";
            tbody += "<td>" + node.status + "</td>";
            tbody += "<td>" + pods + "</td>";
            tbody += "<td><button class='btn btn-info btn-sm toggle-btn' data-node='" + node.node_id + "' data-simulate='" + nextSim + "'>" + simBtnLabel + "</button></td>";
            tbody += "<td><button class='btn btn-danger btn-sm remove-btn' data-node='" + node.node_id + "'>Remove</button></td>";
            tbody += "</tr>";
          });
          $("#nodes-table tbody").html(tbody);
          $("#active-nodes").text(activeCount);
          $("#total-nodes").text(nodes.length);
          var util = 0;
          if (totalCPU > 0) {
            var used = nodes.reduce((acc, node) => acc + (node.cpu_total - node.cpu_available), 0);
            util = Math.round((used / totalCPU) * 100);
          }
          $("#utilization").text(util + "%");
          updatePieChart(usedCPUs);
          $("#log-panel").html(state.logs.join("<br>"));
          var labels = [], datapoints = [];
          state.history.forEach(function(point) {
            var d = new Date(point.timestamp * 1000);
            labels.push(d.toLocaleTimeString());
            datapoints.push(point.utilization.toFixed(2));
          });
          updateLineChart(labels, datapoints);
        }

        // Pie Chart using Chart.js
        var pieCtx = document.getElementById("cpuChart").getContext("2d");
        var cpuPieChart = new Chart(pieCtx, {
          type: "pie",
          data: { labels: [], datasets: [{ data: [], backgroundColor: [] }] },
          options: { responsive: true, plugins: { legend: { position: "bottom" } } }
        });
        function updatePieChart(dataArr) {
          var labels = [], data = [], colors = [];
          dataArr.forEach(function(item, index) {
            labels.push(item.node_id.substring(0,8));
            data.push(item.used);
            colors.push("hsl(" + ((index*50)%360) + ",70%,60%)");
          });
          cpuPieChart.data.labels = labels;
          cpuPieChart.data.datasets[0].data = data;
          cpuPieChart.data.datasets[0].backgroundColor = colors;
          cpuPieChart.update();
        }

        // Line Chart using Chart.js
        var lineCtx = document.getElementById("utilChart").getContext("2d");
        var utilLineChart = new Chart(lineCtx, {
          type: "line",
          data: { labels: [], datasets: [{ label: "Utilization (%)", data: [], fill: false, borderColor: "#3b8bba", tension: 0.1 }] },
          options: { responsive: true, plugins: { legend: { position: "bottom" } } }
        });
        function updateLineChart(labels, datapoints) {
          utilLineChart.data.labels = labels;
          utilLineChart.data.datasets[0].data = datapoints;
          utilLineChart.update();
        }

        // 3D Node Graph using ECharts
        var nodeGraphChart = echarts.init(document.getElementById("nodeGraph"));
        function updateNodeGraph(nodesData) {
          var dataArr = [];
          nodesData.forEach(function(node) {
            // Random coordinates for demo purposes.
            var x = Math.random() * 100;
            var y = Math.random() * 100;
            var z = Math.random() * 100;
            var color = node.status === "active" ? "#28a745" : "#dc3545";
            dataArr.push([x, y, z, node.node_id, color]);
          });
          var option = {
            tooltip: {
              formatter: function(params) {
                return "Node: " + params.data[3] + "<br/>Coords: (" + params.data[0].toFixed(1) + ", " + params.data[1].toFixed(1) + ", " + params.data[2].toFixed(1) + ")";
              }
            },
            xAxis3D: {},
            yAxis3D: {},
            zAxis3D: {},
            grid3D: { viewControl: { projection: "orthographic", autoRotate: true } },
            series: [{
              type: "scatter3D",
              symbolSize: 20,
              data: dataArr,
              itemStyle: {
                color: function(params) { return params.data[4]; }
              }
            }]
          };
          nodeGraphChart.setOption(option);
        }

        // Event Handlers
        $(document).on("click", ".remove-btn", function() {
          var node_id = $(this).data("node");
          $.ajax({ url: "/remove_node", type: "POST", contentType: "application/json", data: JSON.stringify({ node_id: node_id }) });
        });
        $(document).on("click", ".toggle-btn", function() {
          var node_id = $(this).data("node");
          var simulate = $(this).data("simulate");
          $.ajax({ url: "/toggle_simulation", type: "POST", contentType: "application/json", data: JSON.stringify({ node_id: node_id, simulate: simulate }) });
        });
        $("#addNodeForm").submit(function(e) {
          e.preventDefault();
          var cpu = $("#cpuInput").val();
          var mem = $("#memoryInput").val();
          var nodeType = $("#nodeTypeInput").val();
          var nodeGroup = $("#nodeGroupInput").val() || "default";
          $.ajax({
            url: "/add_node",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ cpu: parseInt(cpu), memory: parseInt(mem), node_type: nodeType, network_group: nodeGroup }),
            success: function() { $("#addNodeModal").modal("hide"); }
          });
        });
        $("#launchPodForm").submit(function(e) {
          e.preventDefault();
          var cpuReq = $("#cpuRequired").val();
          var memReq = $("#memoryRequired").val();
          var sched = $("#schedulingAlgorithm").val();
          var netGrp = $("#networkGroup").val() || "default";
          var nodeAffinity = $("#nodeAffinity").val();
          var payload = {
              cpu_required: parseInt(cpuReq),
              memory_required: memReq ? parseInt(memReq) : 4,
              scheduling_algorithm: sched,
              network_group: netGrp
          };
          if (nodeAffinity) { payload["node_affinity"] = nodeAffinity; }
          $.ajax({
            url: "/launch_pod",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(payload),
            success: function() { $("#launchPodModal").modal("hide"); }
          });
        });
        $("#chaos-btn").click(function() {
          $.ajax({ url: "/chaos_monkey", type: "POST", success: function(result) { alert(result.message); } });
        });
        $("#dark-toggle").click(function() {
          $("body").toggleClass("dark-mode");
        });
      </script>
    </body>
    </html>
    """
    return render_template_string(advanced_dashboard_html)

# ----------------------------------
# Background Tasks Startup
# ----------------------------------
def background_tasks():
    Thread(target=health_monitor, daemon=True).start()
    Thread(target=auto_scale_cluster, daemon=True).start()
    Thread(target=simulate_heartbeat_thread, daemon=True).start()
    Thread(target=record_utilization, daemon=True).start()
    Thread(target=broadcast_state, daemon=True).start()

if __name__ == '__main__':
    init_db()  # Initialize the persistent SQLite database
    background_tasks()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)