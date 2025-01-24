from fastapi import FastAPI, Response, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
import os
import psycopg
import gc

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

  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT (x_pos, y_pos) FROM ships WHERE id = 'HIGH_SEAS_ISLAND'")
      island = cur.fetchone()

      if island == None:
        run_all()

def on_starting(server):
  if os.environ["DEV"] == "FALSE":
    p = Thread(target=start_scheduler)
    p.start()

@api.get("/ships")
def ships():
  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT (id, ship_id, readme_url, repo_url, title, screenshot_url, hours, slack_id, slack_username, x_pos, y_pos) FROM ships WHERE filtered = true")
      ships = cur.fetchall()

  if len(ships) == 0:
    return None
  
  nice_ships = {}
  for row in ships:
    ship = row[0]

    # make sure it has a location
    if ship[9] != None:
      nice_ships[ship[0]] = {
        "identifier": ship[1],
        "readme_url": ship[2],
        "repo_url": ship[3],
        "title": ship[4],
        "screenshot_url": ship[5],
        "hours": float(ship[6] or 0),
        "slack_id": ship[7],
        "slack_username": ship[8],
        "x_pos": float(ship[9]),
        "y_pos": float(ship[10]),
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
