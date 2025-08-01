import requests
from bs4 import BeautifulSoup
import re

def get_repo_data(repo_url):
    """
    Fetches and extracts data from a given GitHub repository URL.

    Args:
        repo_url: The URL of the GitHub repository.

    Returns:
        A dictionary containing the repository's data, or None if an error occurs.
    """
    try:
        response = requests.get(repo_url)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract repository name
        repo_name = soup.find('a', {'data-pjax': '#repo-content-pjax-container'}).text.strip()


        # Extract number of commits
        commits_element = soup.find('li', string=lambda text: text and "commits" in text)
        num_commits = 0
        if commits_element:
            commits_text = commits_element.text.strip()
            commits_match = re.search(r'([\d,]+)\s+commits?', commits_text)
            if commits_match:
              num_commits = int(commits_match.group(1).replace(',', ''))
        

        # Extract number of branches
        branches_element = soup.find('a', href=re.compile(r'/branches$'))
        if branches_element:
          branches_text = branches_element.text.strip()
          num_branches = int(re.search(r'([\d,]+)', branches_text).group(1).replace(',', '')) if re.search(r'([\d,]+)', branches_text) else 0
        else:
          num_branches = 0

        # Extract number of releases
        releases_element = soup.find('a', href=re.compile(r'/releases$'))
        if releases_element:
          releases_text = releases_element.text.strip()
          num_releases = int(re.search(r'([\d,]+)', releases_text).group(1).replace(',', '')) if re.search(r'([\d,]+)', releases_text) else 0
        else:
          num_releases = 0
        
        # Extract number of contributors
        contributors_element = soup.find('a', href=re.compile(r'/contributors$'))
        if contributors_element:
          contributors_text = contributors_element.text.strip()
          num_contributors = int(re.search(r'([\d,]+)', contributors_text).group(1).replace(',', '')) if re.search(r'([\d,]+)', contributors_text) else 0
        else:
          num_contributors = 0

        # Extract Readme content
        readme_div = soup.find('article', class_='markdown-body entry-content container-lg')
        readme_content = readme_div.text.strip() if readme_div else "No Readme"

        repo_data = {
            'name': repo_name,
            'url': repo_url,
            'commits': num_commits,
            'branches': num_branches,
            'releases': num_releases,
            'contributors': num_contributors,
            'readme_content': readme_content,
        }
        return repo_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {repo_url}: {e}")
        return None
    except AttributeError as e:
        print(f"Error parsing data for {repo_url}: {e}")
        return None


def get_user_repositories(username):
    """
    Fetches a list of repository URLs for a given GitHub username.
    """
    url = f"https://github.com/{username}?tab=repositories"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        repo_elements = soup.find_all('a', itemprop='name codeRepository')
        repo_urls = [f"https://github.com{element['href']}" for element in repo_elements]
        return repo_urls
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repositories for {username}: {e}")
        return []

def save_to_text(data, output_file):
    """Saves the scraped data to a text file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("GitHub Repositories Data\n\n")

        for repo in data:
            f.write(f"Repository: {repo['name']}\n")
            f.write(f"URL: {repo['url']}\n")
            f.write(f"Commits: {repo['commits']}\n")
            f.write(f"Branches: {repo['branches']}\n")
            f.write(f"Releases: {repo['releases']}\n")
            f.write(f"Contributors: {repo['contributors']}\n\n")
            f.write(f"README Content:\n{repo['readme_content']}\n\n==========\n\n")

def main():
    """
    Main function to extract and print data for repositories of a given GitHub user.
    """
    username = "sr2echa"  # Replace with the desired GitHub username
    repositories = get_user_repositories(username)

    all_repo_data = []
    for repo_url in repositories:
        repo_data = get_repo_data(repo_url)
        if repo_data:
            all_repo_data.append(repo_data)

    # Save the extracted data to a text file
    save_to_text(all_repo_data, "output_github.txt")
    print(f"Data saved to output_github.txt")

if __name__ == "__main__":
    main()
