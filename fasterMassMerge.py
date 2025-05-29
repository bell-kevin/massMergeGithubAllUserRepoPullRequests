import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---- CONFIGURATION ----
# IMPORTANT: Insert your GitHub Personal Access Token below
GITHUB_TOKEN = ''  # <-- Place your token here as a string, e.g. 'ghp_XXXXXXXXXXXXXXXXXXXX'
GITHUB_USER = 'bell-kevin'
MAX_WORKERS = 10  # Adjust as needed (10-20 is usually safe)
BASE_URL = 'https://api.github.com'
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

# ---- GLOBAL SESSION ----
session = requests.Session()
session.headers.update(HEADERS)

def handle_rate_limit(response):
    """Detect and wait out GitHub API rate limits."""
    if response.status_code == 403:
        if 'X-RateLimit-Remaining' in response.headers and response.headers['X-RateLimit-Remaining'] == '0':
            reset_time = int(response.headers['X-RateLimit-Reset'])
            sleep_time = max(reset_time - int(time.time()), 0) + 1
            print(f"[RATE LIMIT] Hit GitHub rate limit. Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
            return True
    return False

def get_with_retry(url, method='GET', **kwargs):
    """Performs a GET/PUT with retry logic for rate limiting."""
    while True:
        if method == 'GET':
            response = session.get(url, **kwargs)
        elif method == 'PUT':
            response = session.put(url, **kwargs)
        else:
            raise ValueError("Unsupported HTTP method")
        
        if handle_rate_limit(response):
            continue  # Try again after sleeping
        
        return response

def get_all_pages(url):
    """Generator for all paginated results."""
    while url:
        response = get_with_retry(url, method='GET')
        if response.status_code != 200:
            print(f"[ERROR] Failed to get data from {url}. HTTP status code: {response.status_code}. Message: {response.text}")
            break
        yield response.json()
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            break

def get_all_repos():
    all_repos = []
    for repos in get_all_pages(f'{BASE_URL}/user/repos'):
        all_repos.extend(repos)
    return all_repos

def get_pull_requests(repo_name):
    prs = []
    url = f'{BASE_URL}/repos/{GITHUB_USER}/{repo_name}/pulls?state=open'
    for page in get_all_pages(url):
        prs.extend(page)
    return repo_name, prs

def merge_pull_request(repo_name, pr_number):
    merge_url = f'{BASE_URL}/repos/{GITHUB_USER}/{repo_name}/pulls/{pr_number}/merge'
    response = get_with_retry(merge_url, method='PUT')
    if response.status_code == 200:
        return True, repo_name, pr_number
    else:
        print(f"[ERROR] Failed to merge PR #{pr_number} in repo {repo_name}: {response.text}")
        return False, repo_name, pr_number

def main():
    if not GITHUB_TOKEN:
        print("ERROR: Please set your GitHub token in the GITHUB_TOKEN variable at the top of this script.")
        return

    start_time = time.time()
    successful_merges = 0

    print("Fetching repositories...")
    all_repos = get_all_repos()
    print(f"Found {len(all_repos)} repositories.")

    all_prs = []
    print("Fetching open pull requests from all repositories...")
    # Fetch PRs in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_repo = {executor.submit(get_pull_requests, repo['name']): repo['name'] for repo in all_repos}
        for future in as_completed(future_to_repo):
            repo_name, prs = future.result()
            if prs:
                all_prs.extend([(repo_name, pr['number']) for pr in prs])

    print(f"Found {len(all_prs)} open pull requests to merge.")

    # Merge PRs in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        merge_futures = [executor.submit(merge_pull_request, repo_name, pr_number) for repo_name, pr_number in all_prs]
        for future in as_completed(merge_futures):
            success, repo_name, pr_number = future.result()
            if success:
                print(f"Successfully merged PR #{pr_number} in repo {repo_name}")
                successful_merges += 1

    end_time = time.time()
    minutes, seconds = divmod(end_time - start_time, 60)
    print(f"\nTotal program execution time: {int(minutes)} minutes and {seconds:.2f} seconds")
    print(f"Total successful merges: {successful_merges}")

if __name__ == "__main__":
    main()
