from pprint import pprint
import requests
import os
import math
import time
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
    token = arguments["--token"][0]
    org = arguments["--org"][0]

    os.environ["GH_USERNAME"] = username
    os.environ["GH_ACCESS_TOKEN"] = token

    request_org(org)


def make_request(endpoint):

    response = requests.get(
        endpoint,
        auth=(os.environ["GH_USERNAME"], os.environ["GH_ACCESS_TOKEN"])
    )

    if response.status_code == requests.codes.ok:
        return response
    else:
        raise RequestError(f"HTTP response failure: {response}")


def request_all_orgs():
    endpoint = f"{ALL_ORG_ENDPOINT}"

    # paging is dome via the link header

    # cache current page in /tmp/_current_page

    # since query param is the id of te last org seen via API


def request_org(org):
    endpoint = f"{ORG_ENDPOINT}/{org}"
    spinner.start()
    response = make_request(endpoint)
    data = response.json()
    spinner.stop()

    repo_endpoint = data["repos_url"]

    print("---")
    print(data["login"])
    print(f'Description: {data["description"]}')
    print(f'Public Repos: {data["public_repos"]}')
    print("...")
    print('Getting repo stats...')

    get_repo_with_most_open_issues(repo_endpoint, data["public_repos"])


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

    stats_sorted = sorted(stats, reverse=True, key=itemgetter("open_issues"))
    print(f"Repo with most open issues: {stats_sorted[0]['full_name']}: {stats_sorted[0]['open_issues']}")
    print("License breakdown:")
    for k, v in licenses.items():
        print(f"{k}: {v}")
