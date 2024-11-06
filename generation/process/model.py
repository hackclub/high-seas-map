import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import requests
import click
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.multioutput import MultiOutputClassifier
from os.path import exists
import json
from pickle import dump

def process_model():
  if not exists("sample/all_ships_tags.csv"):
    click.echo("Sample data to train model missing.")
    return
  df = pd.read_csv("sample/all_ships_tags.csv")

  contents = []
  if not exists("data/sample_contents.json"):
    with click.progressbar(df.iterrows(), label="Downloading README contents") as bar:
      for _, row in bar:
        readme_text_res = requests.get(row["readme_url"])

        if readme_text_res.status_code != 200:
          click.echo(f"Skipping ship {row['identifier']} as it does not have a valid README")
          contents.append("")
          continue

        contents.append(f"{row['title']}\n{readme_text_res.text}")
    
    contents_file = open('data/sample_contents.json', 'w', encoding='utf-8')
    contents_file.write(json.dumps(contents))
  else:
    click.echo("Using pre-downloaded README contents")
    contents_file = open('data/sample_contents.json', 'r', encoding='utf-8')
    contents = json.loads(contents_file.read())
  
  df.insert(3, "content", contents)
  df.drop(df[df.content == ""].index)

  # Initialize TF-IDF Vectorizer
  vectorizer = TfidfVectorizer(stop_words='english', max_df=0.7)

  # Transform the text data to feature vectors
  X = vectorizer.fit_transform(df['content'])

  # Labels
  y = list(map(lambda t: t.split(","), df['tags']))

  maxlabels = 1
  for ship in y:
    if len(ship) > maxlabels:
      maxlabels = len(ship)

  homo_y = y
  for ship in homo_y:
    for i in range(maxlabels - len(ship)):
      ship.append("")

  # Split the dataset into training and testing sets
  X_train, X_test, y_train, y_test = train_test_split(X, homo_y, train_size=0.5)

  # Initialize and train the classifier
  # clf = SVC(kernel="rbf", C=543)
  clf = LogisticRegression(C=1e20)
  multi_clf = MultiOutputClassifier(clf, n_jobs=2)
  multi_clf.fit(X_train, y_train)

  with open("data/model.pkl", "wb") as f:
    dump(multi_clf, f, protocol=5)

  with open("data/vectorizer.pkl", "wb") as f:
    dump(vectorizer, f, protocol=5)

  # Predict on the test set
  # y_pred = multi_clf.predict(X_test)

  all_tags = []
  for taglist in df["tags"]:
    for tag in taglist.split(","):
      if tag not in all_tags:
        all_tags.append(tag)

  # Evaluate the performance
  # accuracy = accuracy_score(y_test, y_pred)
  # report = classification_report(y_test, y_pred)

  # print(f'Accuracy: {accuracy:.4f}')
  # print('Classification Report:')
  # print(report)
