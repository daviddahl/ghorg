from pprint import pprint
import requests
import os
import math
import time
import json
from operator import itemgetter

from halo import Halo


GITHUB_API_ENDPOINT = "https://api.github.com"
ORG_ENDPOINT = f"{GITHUB_API_ENDPOINT}/orgs"
ALL_ORG_ENDPOINT = f"{GITHUB_API_ENDPOINT}/organizations"

spinner = Halo(text='Loading', spinner='dots')


class RequestError(Exception):
    pass


def ghorg(arguments):
    """
    entrypoint for Github organization queries
    """
    username = arguments["--username"][0]
    token = arguments["--token"]
    org = arguments["--org"][0]

    os.environ["GH_USERNAME"] = username
    if isinstance(token, list):
        os.environ["GH_ACCESS_TOKEN"] = token[0]
    else:
        os.environ["GH_ACCESS_TOKEN"] = token

    if org == "*":
        request_all_orgs()
    else:
        request_org(org)


def make_request(endpoint):
    response = requests.get(
        endpoint,
        auth=(os.environ["GH_USERNAME"], os.environ["GH_ACCESS_TOKEN"])
    )

    if response.status_code == requests.codes.ok:
        return response
    else:
        errors = json.loads(response.content)
        pprint(errors)
        raise RequestError(f"HTTP request failure")


def request_all_orgs():
    # TODO: check for the since_id in /tmp/__ghorg_paging

    f = open("/tmp/__ghorg_paging", "r")
    lines = f.readlines()

    try:
        since_id = int(lines[0])
    except:
        since_id = None

    if since_id is None:
        endpoint = f"{ALL_ORG_ENDPOINT}"
    else:
        endpoint = f"{ALL_ORG_ENDPOINT}?since={since_id}"

    print(endpoint)
    request_orgs_page(endpoint)


def save_id(since_id):

    f = open("/tmp/__ghorg_paging", "w")
    f.truncate(0)
    f.writelines([str(since_id)])
    f.close()


def request_orgs_page(endpoint):
    print(f"requesting orgs page: {endpoint}")
    response = make_request(endpoint)

    for org in response.json():
        since_id = request_org(org["login"])
        save_id(since_id)

    endpoint = f"{ALL_ORG_ENDPOINT}?since={since_id}"
    request_orgs_page(endpoint)


def request_org(org):
    endpoint = f"{ORG_ENDPOINT}/{org}"
    spinner.start()
    response = make_request(endpoint)
    data = response.json()
    spinner.stop()

    repo_endpoint = data["repos_url"]

    print("---")
    print(f'Org: {data["repos_url"]}')
    print(f'Description: {data["description"]}')
    print(f'Public Repos: {data["public_repos"]}')
    print('\nGetting repo stats...')

    get_repo_with_most_open_issues(repo_endpoint, data["public_repos"])

    return data["id"]


def request_repos(endpoint, num_repos):
    """
    Get all of an orgs' public repose as a JSON Array
    """
    pages = 1
    pages_fetched = 1
    if num_repos > 100:
        pages = math.ceil((int(num_repos) / 100))

    print(f"Pages to fetch: {pages}")

    get_another_page = True

    repos = []
    while get_another_page:
        spinner.start()
        response = make_request(f"{endpoint}?page={pages_fetched}&per_page=100")
        repos.extend(response.json())
        time.sleep(1)
        pages_fetched = pages_fetched + 1
        spinner.stop()
        spinner.succeed()

        if pages_fetched > pages:
            get_another_page = False

    return repos


def get_repo_with_most_open_issues(endpoint, num_repos):
    """
    Find the repo with the most open issues
    """
    stats = []
    licenses = {}
    lic_list = []

    print("Requesting repos from API...")
    repos = request_repos(endpoint, num_repos)

    for repo in repos:
        lic = repo.get("license")
        lic_list.append(repo.get("license"))
        try:
            lic_key = lic.get("key")
            try:
                test = licenses[lic_key]
                licenses[lic_key] = licenses[lic_key] + 1
            except KeyError as ex:
                licenses[lic_key] = 1
        except:
            pass

        stats.append(
            {
                "id": repo["id"],
                "full_name": repo["full_name"],
                "open_issues": int(repo["open_issues"]),
                "html_url": repo["html_url"]
            }
        )

    stats_sorted = sorted(
        stats,
        reverse=True,
        key=itemgetter("open_issues")
    )
    try:
        print(f"\nRepo with most open issues: \n  {stats_sorted[0]['html_url']}\n    Open issues: {stats_sorted[0]['open_issues']}")
    except IndexError as ex:
        print("Could not determine repo with most open issues! (An error occurred)")
        # NOTE: since_id: 1849 caused this
    print("\nAll Repos License breakdown:")

    for k, v in licenses.items():
        print(f"{k}: {v}")
