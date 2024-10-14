import click
from dotenv import load_dotenv

from download.ships import download_ships
from process.similarity import process_similarity
from process.keywords import process_keywords
from process.graph import process_graph
from process.model import process_model
from process.clusters import process_clusters
from process.model_keywords import process_model_keywords
from all import run_all

load_dotenv()

@click.group()
def root():
	pass

@root.command()
def all():
	run_all()

@root.group()
def download():
	pass

@download.command()
def ships():
	download_ships()
	
@root.group()
def process():
	pass

@process.command()
def similarity():
	process_similarity()

@process.command()
def keywords():
	process_keywords()
	
@process.command()
def graph():
	process_graph()
	
@process.command()
def model():
	process_model()
	
@process.command()
def clusters():
	process_clusters()
	
@process.command()
def model_keywords():
	process_model_keywords()

@root.group()
def query():
	pass

if __name__ == '__main__':
	root()


