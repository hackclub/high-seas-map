import json
from pyairtable import Api
import os
from urllib.parse import urlparse
import requests

def download_ships():
  api = Api(os.environ['AIRTABLE_API_KEY'])
  ships_table = api.table(os.environ['AIRTABLE_BASE'], os.environ['AIRTABLE_TABLE'])

  print("Downloading ships from Airtable...")
  all_ships = ships_table.all(formula="AND(AND({hidden} = FALSE(), {project_source} = \"high_seas\"), {ship_status} = \"shipped\")", fields=["identifier", "title", "readme_url", "repo_url", "screenshot_url", "hours"])

  fixed_ships = []
  readme_urls = []
  for ship in all_ships:
    readme_url = str(ship.get("fields").get("readme_url"))

    if readme_url == "None":
      print(f"Skipping ship record {ship['id']} since it does not have a README URL")
      continue

    parsed_url = urlparse(readme_url)
    if parsed_url.netloc == "github.com":
      path = parsed_url.path.split("/")
      # Repo url
      if len(path) == 3:
        headers = {
          'Accept': 'application/vnd.github+json',
          'X-GitHub-Api-Version': "2022-11-28"
        }
        repo_info_req = requests.get(f"https://api.github.com/repos/{path[1]}/{path[2]}", headers=headers)
        repo_info = repo_info_req.json()
        branch = repo_info['default_branch'] if "default_branch" in repo_info else "main"
        readme_url = f"https://raw.githubusercontent.com/{path[1]}/{path[2]}/{branch}/README.md"
      elif len(path) > 3:
        # File url
        if path[3] == "blob":
          readme_url = f"https://raw.githubusercontent.com/{path[1]}/{path[2]}/{path[4]}/README.md"

    if readme_url in readme_urls:
      print(f"Skipping ship record {ship['id']} since it is already included")
      continue

    readme_urls.append(readme_url)

    ship_dict = dict(ship)
    ship_dict["fields"]["readme_url"] = readme_url
    fixed_ships.append(ship_dict)

  shipsJson = json.dumps(fixed_ships)

  if not os.path.exists("data"):
    os.mkdir("data")
  
  file = open('data/ships.json', 'w', encoding='utf-8')
  file.write(shipsJson)

