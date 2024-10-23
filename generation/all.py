from shutil import rmtree
from os.path import exists

from download.ships import download_ships
from process.similarity import process_similarity
from process.graph import process_graph
from process.model import process_model
from process.combined_keywords import process_combined_keywords
from process.clusters import process_clusters

def run_all():
  if exists("../frontend/public/data"):
    rmtree("../frontend/public/data")
  if exists("data"):
    rmtree("data")

  download_ships()

  process_model()
  process_combined_keywords()
  
  process_similarity()
  process_graph()
  process_clusters()
  