import requests
from urllib.parse import urlparse, parse_qs

# Personal access token
headers = {'Authorization': 'token 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'}

def get_all_pages(url):
    while url:
        response = requests.get(url, headers=headers)
        yield response.json()
        if 'next' in response.links.keys():
            url = response.links['next']['url']
        else:
            break

# Get all repositories for the authenticated user
all_repos = []
for repos in get_all_pages('https://api.github.com/user/repos'):
    all_repos.extend(repos)

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