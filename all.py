from download.ships import download_ships
from process.similarity import process_similarity
from process.graph import process_graph
def run_all():
  download_ships()
  process_similarity()
  process_graph()
  