from pyairtable import Api
import os
from urllib.parse import urlparse
import requests
from slack_sdk import WebClient
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
import psycopg
from time import sleep, time
from joblib import Parallel, delayed
import json

def make_ship_args(ship):
  arg = (ship["id"], ship["fields"]["identifier"], ship["fields"]["readme_url"], ship["fields"]["repo_url"],
                  ship["fields"]["title"], ship["fields"]["screenshot_url"], ship["fields"]["hours"],
                  ship["fields"]["entrant__slack_id"][0], ship["fields"]["slack_username"])

  return arg

def download_ships(reset):
  api = Api(os.environ['AIRTABLE_API_KEY'], endpoint_url="https://middleman.hackclub.com/airtable")
  ships_table = api.table(os.environ['AIRTABLE_BASE'], os.environ['AIRTABLE_TABLE'])

  slack = WebClient(token=os.environ["SLACK_API_KEY"])

  rate_limit_handler = RateLimitErrorRetryHandler(max_retry_count=5)

  slack.retry_handlers.append(rate_limit_handler)

  print("Downloading ships from Airtable...")
  fields = ["identifier", "title", "readme_url", "repo_url", "screenshot_url", "hours", "entrant__slack_id"]
  formula_conditions = ["{hidden} = FALSE()", "{project_source} = \"high_seas\"", "{ship_status} = \"shipped\"", "{has_ysws_submission_id} = TRUE()"]
  for field in fields:
    formula_conditions.append("AND({" + field + "} != BLANK(), {" + field + "} != \"\")")
  
  formula = f"AND({", ".join(formula_conditions)})" 
  all_ships = ships_table.all(formula=formula, fields=fields, max_records=100 if os.environ["DEV"] == "TRUE" else None)

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
          'X-GitHub-Api-Version': "2022-11-28",
          'Authorization': f"Bearer {os.environ["GITHUB_TOKEN"]}"
        }
        repo_info_req = requests.get(f"https://api.github.com/repos/{path[1]}/{path[2]}", headers=headers)
        while repo_info_req.status_code == 429 or repo_info_req.status_code == 403:
          reset_time = repo_info_req.headers["x-ratelimit-reset"]
          time_left = reset_time - time()
          print(f"github ratelimited... waiting {time_left} seconds")
          sleep(time_left)

          repo_info_req = requests.get(f"https://api.github.com/repos/{path[1]}/{path[2]}", headers=headers)

        repo_info = repo_info_req.json()
        branch = repo_info['default_branch'] if "default_branch" in repo_info else "main"
        readme_url = f"https://raw.githubusercontent.com/{path[1]}/{path[2]}/{branch}/README.md"
      elif len(path) > 3:
        # File url
        if path[3] == "blob":
          readme_url = f"https://raw.githubusercontent.com/{path[1]}/{path[2]}/{path[4]}/{path[5]}"

    if readme_url in readme_urls:
      print(f"Skipping ship record {ship['id']} since it is already included")
      continue

    readme_urls.append(readme_url)

    ship_dict = dict(ship)
    ship_dict["fields"]["readme_url"] = readme_url

    user_info = slack.users_info(user=str(ship.get("fields").get("entrant__slack_id")[0]))
    ship_dict["fields"]["slack_username"] = user_info["user"]["name"]

    fixed_ships.append(ship_dict)

  print(f"Done with ships ({len(fixed_ships)} ships)")
  if reset:
    # with psycopg.connect(os.environ["DB_URI"]) as conn:
    #   with conn.cursor() as cur:
    #     cur.execute("DELETE FROM similarity")
    #     cur.execute("DELETE FROM ships")

    #     args_result = Parallel(n_jobs=10)(delayed(make_ship_args)(ship) for ship in fixed_ships)
    #     args = list(args_result)
        
    #     cur.execute("INSERT INTO ships (id, filtered) VALUES ('HIGH_SEAS_ISLAND', true)")
    #     cur.executemany("""
    #                   INSERT INTO ships (id, ship_id, readme_url, repo_url, title, screenshot_url, hours, slack_id, slack_username)
    #                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    #                   """, args)
        
    #   conn.commit()

    json.dump(fixed_ships, open("data/ships.json", "w"))
  else:
    return fixed_ships

  

