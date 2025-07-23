Cluster Simulation Framework
Overview
The Cluster Simulation Framework is a Python-based tool designed to simulate a distributed computing cluster. It provides a Flask-based API server, a CLI client for interacting with the cluster, a node simulator for sending heartbeats, and an advanced web-based dashboard for real-time monitoring. The framework supports node management, pod scheduling with multiple algorithms, auto-scaling, health monitoring, and a Chaos Monkey feature to simulate failures.
Features

Node Management: Add, remove, and list nodes with specified CPU and memory capacities.
Pod Scheduling: Launch pods with resource requirements and choose from first_fit, best_fit, or worst_fit scheduling algorithms.
Auto-Scaling: Automatically adds nodes when CPU utilization exceeds 80%.
Health Monitoring: Detects node failures via heartbeat timeouts and reschedules pods from failed nodes.
Chaos Monkey: Randomly kills nodes or pods to simulate failures.
Real-Time Dashboard: Visualizes cluster state, node details, CPU distribution, utilization history, and a 3D node graph using ECharts.
Event Logging: Logs events to an SQLite database and displays them in the dashboard.
Utilization Tracking: Records and visualizes cluster utilization over time.
Network Groups and Node Affinity: Supports network group isolation and node affinity for pod scheduling.

Requirements

Python 3.8+

Dependencies (install via requirements.txt):
pip install flask flask-socketio requests argparse sqlite3


Optional: Web browser for accessing the dashboard.


Project Structure
cluster_simulation/
├── client.py           # CLI client for interacting with the cluster
├── node.py             # Node simulator for sending heartbeats
├── server.py           # Flask API server and dashboard
├── cluster.db          # SQLite database for event logs and utilization history
├── requirements.txt    # Python dependencies
└── README.md           # This file

Setup

Clone the Repository:
git clone <repository-url>
cd cluster_simulation


Install Dependencies:
pip install -r requirements.txt


Run the Server:
python server.py

The server runs on http://localhost:5000 by default.

Access the Dashboard: Open a web browser and navigate to http://localhost:5000/dashboard.


Usage
CLI Client (client.py)
The CLI client provides commands to manage the cluster:
python client.py --server http://localhost:5000 <command>

Available commands:

Add a Node:
python client.py --server http://localhost:5000 add_node --cpu 8 --memory 16


Launch a Pod:
python client.py --server http://localhost:5000 launch_pod --cpu_required 2 --memory_required 4 --scheduling_algorithm first_fit --network_group default


List Nodes:
python client.py --server http://localhost:5000 list_nodes


Trigger Chaos Monkey:
python client.py --server http://localhost:5000 chaos_monkey



Node Simulator (node.py)
Simulates a node sending heartbeats to the server:
python node.py --server http://localhost:5000 --node_id <node-id> --interval 7

Replace <node-id> with the ID returned when adding a node.
Dashboard

URL: http://localhost:5000/dashboard
Features:
View active/total nodes, cluster utilization, and node details.
Add nodes or launch pods via modals.
Monitor real-time CPU distribution (pie chart) and utilization history (line chart).
Visualize nodes in a 3D graph using ECharts.
View event logs and download cluster reports as CSV.
Toggle dark mode and trigger Chaos Monkey events.



API Endpoints

POST /add_node: Add a node with specified CPU, memory, node type, and network group.
POST /remove_node: Remove a node by ID.
POST /toggle_simulation: Enable/disable heartbeat simulation for a node.
GET /list_nodes: List all nodes and their details.
POST /launch_pod: Launch a pod with resource requirements and scheduling preferences.
POST /heartbeat: Update a node's heartbeat timestamp.
POST /chaos_monkey: Trigger a random failure (node or pod).
GET /download_report: Download a CSV report of the cluster state.
GET /logs: Retrieve recent event logs.
GET /utilization_history: Retrieve utilization history.
GET /dashboard: Access the web-based dashboard.

Database
The framework uses an SQLite database (cluster.db) to store:

Event Logs: Timestamped events (e.g., node additions, pod scheduling).
Utilization History: Timestamped cluster utilization data.

Notes

The dashboard uses Bootstrap, AdminLTE, Chart.js, and ECharts for visualization.
Heartbeat simulation is enabled by default for auto-added nodes.
Chaos Monkey randomly kills either a node or a pod with a 50% probability.
The server runs background tasks for health monitoring, auto-scaling, and state broadcasting via Socket.IO.

Future Enhancements

Add authentication for the dashboard and API.
Implement advanced pod scheduling policies (e.g., priority-based).
Enhance Chaos Monkey with configurable failure patterns.
Add support for container orchestration features (e.g., pod dependencies).

License
This project is licensed under the MIT License.
