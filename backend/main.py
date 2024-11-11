from dotenv import load_dotenv
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
import json
import os

from all import run_all
from download.ships import download_ships
from process.similarity import process_similarity
from process.graph import process_graph

class Auth(BaseModel):
  token: str

load_dotenv()

app = FastAPI()

cors_origins = [
  "http://localhost:3000",
  "https://high-seas-map.vercel.app"
]

app.add_middleware(
  CORSMiddleware,
  allow_origins=cors_origins,
  allow_methods=["*"],
  allow_headers=["*"]
)

def start_scheduler():
  print("scheduler starting")
  scheduler = BackgroundScheduler()
  scheduler.add_job(run_all, 'interval', hours=24)
  scheduler.start()

  if not os.path.exists("data/nodes.json"):
    run_all()

def on_starting(server):
  p = Thread(target=start_scheduler)
  p.start()

@app.get("/ships")
def ships():
  if not os.path.exists("data/filtered_ships.json"):
    return None

  ships_file = open("data/filtered_ships.json", "r")
  return json.load(ships_file)

@app.get("/nodes")
def ships():
  if not os.path.exists("data/nodes.json"):
    return None

  ships_file = open("data/nodes.json", "r")
  return json.load(ships_file)

@app.post("/refresh/all")
def refresh_all(auth: Auth, response: Response):
  if auth.token != os.environ["REFRESH_TOKEN"]:
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return None
  
  run_all()
  return None

@app.post("/refresh/ships")
def refresh_all(auth: Auth, response: Response):
  if auth.token != os.environ["REFRESH_TOKEN"]:
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return None
  
  download_ships()
  return None

@app.post("/refresh/similarity")
def refresh_all(auth: Auth, response: Response):
  if auth.token != os.environ["REFRESH_TOKEN"]:
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return None
  
  process_similarity()
  return None

@app.post("/refresh/graph")
def refresh_all(auth: Auth, response: Response):
  if auth.token != os.environ["REFRESH_TOKEN"]:
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return None
  
  process_graph()
  return None
