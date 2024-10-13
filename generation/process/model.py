import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import requests
import click
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
from sklearn.multioutput import MultiOutputClassifier

def process_model():
  df = pd.read_csv("sample/low-skies-tags.csv")

  contents = []
  for _, row in df.iterrows():
    readme_text_res = requests.get(row["readme_url"])

    if readme_text_res.status_code != 200:
      click.echo(f"Skipping ship {row['identifier']} as it does not have a valid README")
      contents.append(None)
      continue

    contents.append(f"{row["title"]}\n{readme_text_res.text}")

  df.insert(3, "content", contents)

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
  
  click.echo(homo_y)

  # Split the dataset into training and testing sets
  X_train, X_test, y_train, y_test = train_test_split(X, homo_y, random_state=42)

  # Initialize and train the classifier
  clf = SVC()
  multi_clf = MultiOutputClassifier(clf, n_jobs=2)
  multi_clf.fit(X, y)

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

  def predict_category(text):
    """
    Predict the category of a given text using the trained classifier.
    """
    text_vec = vectorizer.transform([text])
    prediction = multi_clf.predict(text_vec)
    return prediction[0]

  # Example usage
  sample_text = "INSERT TEST HERE"
  predicted_category = predict_category(sample_text)
  print(f'The predicted category is: {predicted_category}')
