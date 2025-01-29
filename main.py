from fastapi import FastAPI, Response, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
import os
import psycopg
import gc
import json

from all import run_all
from download.ships import download_ships
from process.similarity import process_similarity
from process.graph import process_graph

class Auth(BaseModel):
  token: str

# load_dotenv()

api = FastAPI()
app = FastAPI()

app.mount("/api", api)
app.mount("/", StaticFiles(directory="dist", html=True))

def start_scheduler():
  print("scheduler starting")
  scheduler = BackgroundScheduler()
  scheduler.add_job(run_all, 'interval', hours=24)
  scheduler.start()

  if os.path.exists("data/nodes.json"):
    nodes = json.load(open("data/nodes.json"))

    if "HIGH_SEAS_ISLAND" not in nodes:
      run_all()

def on_starting(server):
  if not os.path.exists("data"):
    os.mkdir("data")

  if os.environ["DEV"] == "FALSE":
    p = Thread(target=start_scheduler)
    p.start()

@api.get("/ships")
def ships():
  # with psycopg.connect(os.environ["DB_URI"]) as conn:
  #   with conn.cursor() as cur:
  #     cur.execute("SELECT (id, ship_id, readme_url, repo_url, title, screenshot_url, hours, slack_id, slack_username, x_pos, y_pos) FROM ships WHERE filtered = true")
  #     ships = cur.fetchall()

  ships = json.load(open("data/ships.json"))
  filtered = json.load(open("data/filtered_ships.json"))
  nodes = json.load(open("data/nodes.json"))

  if len(ships) == 0:
    return None
  
  nice_ships = {
    'HIGH_SEAS_ISLAND': {
      'x_pos': float(nodes["HIGH_SEAS_ISLAND"][0]),
      'y_pos': float(nodes["HIGH_SEAS_ISLAND"][1])
    }
  }
  for ship in ships:
    id = ship["id"]

    # make sure it has a location
    if id in nodes and id in filtered:
      nice_ships[id] = {
        "identifier": ship["fields"]["identifier"],
        "readme_url": ship["fields"]["readme_url"],
        "repo_url": ship["fields"]["repo_url"],
        "title": ship["fields"]["title"],
        "screenshot_url": ship["fields"]["screenshot_url"],
        "hours": float(ship["fields"]["hours"] or 0),
        "slack_id": ship["fields"]["entrant__slack_id"][0],
        "slack_username": ship["fields"]["slack_username"],
        "x_pos": float(nodes[id][0]),
        "y_pos": float(nodes[id][1]),
      }

  return nice_ships

@api.post("/refresh/all")
def refresh_all(auth: Auth, response: Response):
  if auth.token != os.environ["REFRESH_TOKEN"]:
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return None
  
  run_all()
  gc.collect()
  return None

@api.post("/refresh/ships")
def refresh_ships(auth: Auth, response: Response):
  if auth.token != os.environ["REFRESH_TOKEN"]:
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return None
  
  download_ships(reset=True)
  gc.collect()
  return None

@api.post("/refresh/similarity")
def refresh_similarity(auth: Auth, response: Response):
  if auth.token != os.environ["REFRESH_TOKEN"]:
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return None
  
  process_similarity(None)
  gc.collect()
  return None

@api.post("/refresh/graph")
def refresh_graph(auth: Auth, response: Response):
  if auth.token != os.environ["REFRESH_TOKEN"]:
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return None
  
  process_graph(None, None)
  gc.collect()
  return None
