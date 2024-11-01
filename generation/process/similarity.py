import json
from os.path import exists
import click

def process_similarity():
	if not exists("data/labels.json"):
		click.echo("Labels not generated. Please run `python main.py process labels` first.")
		return

	labels_file = open('data/labels.json', 'r', encoding='utf-8')
	labels = json.loads(labels_file.read())

	indices = {}

	with click.progressbar(labels, label="Generating similarity indices...") as bar:	
		for shipA in bar:
			for shipB in labels:
				if shipA == shipB:
					continue

				intersection = set(labels[shipA]).intersection(set(labels[shipB]))
				union = set(labels[shipA]).union(set(labels[shipB]))

				jaccard = len(intersection) / len(union)

				indices[shipA + "-" + shipB] = jaccard

	similarityIndicesFile = open('data/similarity_indices.json', 'w', encoding='utf-8')
	similarityIndicesFile.write(json.dumps(indices))

	return indices