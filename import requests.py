import requests

TOKEN = "" # clickup Token

headers = {"Authorization": TOKEN}

teams = requests.get(
    "https://api.clickup.com/api/v2/team",
    headers=headers
).json()

for team in teams["teams"]:
    team_id = team["id"]

    spaces = requests.get(
        f"https://api.clickup.com/api/v2/team/{team_id}/space",
        headers=headers
    ).json()

    for space in spaces["spaces"]:
        lists = requests.get(
            f"https://api.clickup.com/api/v2/space/{space['id']}/list",
            headers=headers
        ).json()

        for lst in lists["lists"]:
            print(lst["name"], "→", lst["id"])