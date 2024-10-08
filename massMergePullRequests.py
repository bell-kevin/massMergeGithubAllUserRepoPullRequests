import requests
import time

# Personal access token
# Replace 'your-token' with your GitHub personal access token
headers = {'Authorization': 'token your-token'}

def get_all_pages(url):
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to get data from {url}. HTTP status code: {response.status_code}. Message: {response.text}")
            break
        yield response.json()
        if 'next' in response.links.keys():
            url = response.links['next']['url']
        else:
            break

# Measure the start time
start_time = time.time()

# Get all repositories for the authenticated user
all_repos = []
for repos in get_all_pages('https://api.github.com/user/repos'):
    all_repos.extend(repos)

# Initialize a counter for successful merges
successful_merges = 0

for repo in all_repos:
    repo_name = repo['name']
    # Get all pull requests
    for prs in get_all_pages(f'https://api.github.com/repos/bell-kevin/{repo_name}/pulls'):
        # Check if the request was successful
        if 'message' in prs:
            print(f"Failed to get pull requests for repository {repo_name}. Message: {prs['message']}")
            continue

        # Merge each pull request
        for pr in prs:
            pr_number = pr['number']
            merge_url = f'https://api.github.com/repos/bell-kevin/{repo_name}/pulls/{pr_number}/merge'
            merge_response = requests.put(merge_url, headers=headers)
            
            # Check if the merge was successful
            if merge_response.status_code != 200:
                print(f"Failed to merge pull request #{pr_number} in repository {repo_name}. Message: {merge_response.text}")
            else:
                print(f"Successfully merged pull request #{pr_number} in repository {repo_name}")
                successful_merges += 1  # Increment the counter for successful merges

# Measure the end time
end_time = time.time()

# Calculate the total execution time
execution_time = end_time - start_time
minutes, seconds = divmod(execution_time, 60)
print(f"Total program execution time: {int(minutes)} minutes and {seconds:.2f} seconds")

# Print the total number of successful merges
print(f"Total successful merges: {successful_merges}")
