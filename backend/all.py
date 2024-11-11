from shutil import rmtree
from os.path import exists

from download.ships import download_ships
from process.similarity import process_similarity
from process.graph import process_graph
def run_all():
  if exists("data"):
    rmtree("data")

  download_ships()
  process_similarity()
  process_graph()
  