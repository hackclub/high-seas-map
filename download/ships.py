from pyairtable import Api
import os
from urllib.parse import urlparse
import requests
from slack_sdk import WebClient
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
import psycopg

def download_ships():
  api = Api(os.environ['AIRTABLE_API_KEY'])
  ships_table = api.table(os.environ['AIRTABLE_BASE'], os.environ['AIRTABLE_TABLE'])

  slack = WebClient(token=os.environ["SLACK_API_KEY"])

  rate_limit_handler = RateLimitErrorRetryHandler(max_retry_count=1)

  slack.retry_handlers.append(rate_limit_handler)

  print("Downloading ships from Airtable...")
  fields = ["identifier", "title", "readme_url", "repo_url", "screenshot_url", "hours", "entrant__slack_id"]
  all_ships = ships_table.all(formula="AND(AND({hidden} = FALSE(), {project_source} = \"high_seas\"), {ship_status} = \"shipped\")", fields=fields)

  if os.environ["DEV"] == "TRUE":
    all_ships = all_ships[0:100]

  fixed_ships = []
  readme_urls = []
  for ship in all_ships:
    missing_fields = []
    for field in fields:
      if field not in ship["fields"]:
        missing_fields.append(field)
    
    if len(missing_fields) > 0:
      print(f"Skipping ship record {ship['id']} since it does not have field(s): {", ".join(missing_fields)}")
      continue
    
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

    user_info = slack.users_info(user=str(ship.get("fields").get("entrant__slack_id")[0]))
    ship_dict["fields"]["slack_username"] = user_info["user"]["name"]

    fixed_ships.append(ship_dict)

  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      cur.execute("DELETE FROM similarity")
      cur.execute("DELETE FROM ships")

      args = []
      for ship in fixed_ships:
        args.append((ship["id"], ship["fields"]["identifier"], ship["fields"]["readme_url"], ship["fields"]["repo_url"],
                          ship["fields"]["title"], ship["fields"]["screenshot_url"], ship["fields"]["hours"],
                          ship["fields"]["entrant__slack_id"][0], ship["fields"]["slack_username"]))
      
      cur.execute("INSERT INTO ships (id, filtered) VALUES ('HIGH_SEAS_ISLAND', true)")
      cur.executemany("""
                    INSERT INTO ships (id, ship_id, readme_url, repo_url, title, screenshot_url, hours, slack_id, slack_username)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, args)
      
    conn.commit()

  print("Done with ships")

