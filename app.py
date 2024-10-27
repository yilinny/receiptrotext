from flask import Flask, request, render_template
import os
from google.cloud import vision
from google.cloud.vision import Image
from dotenv import load_dotenv
import difflib
import re

# Load environment variables from .env file
load_dotenv()

# Access the GOOGLE_APPLICATION_CREDENTIALS variable
google_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

app = Flask(__name__)

# Set up the upload folder
UPLOAD_FOLDER = "uploads"  # Make sure this folder exists
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize the Vision API client
client = vision.ImageAnnotatorClient()


@app.route("/")
def upload_form():
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part"

    file = request.files["file"]

    if file.filename == "":
        return "No selected file"

    # Save the uploaded file to the server
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)
    
    try:
        # Process the image using Google Cloud Vision
        result = process_image(file_path)

        # Delete the file after processing
        os.remove(file_path)

        return result

    except Exception as e:
        # Ensure the file is removed in case of any error
        os.remove(file_path)
        return str(e)


def process_image(image_path):
    # image to text
    # Load the image
    with open(image_path, "rb") as img_file:
        content = img_file.read()

    image = Image(content=content)

    # Call the Vision API
    response = client.text_detection(image=image)
    texts = response.text_annotations

    # Handle potential errors
    if response.error.message:
        raise Exception(f"{response.error.message}")

    # Return detected texts
    data = "\n".join([text.description for text in texts])
    return categorize_data(texts)


def check_similarity(text, template, percent):

    if len(text) > len(template):
        return False
    # percent - based on length of word and importance
    if difflib.SequenceMatcher(None, text.upper(), template.upper()).ratio() >= percent:
        return True
    else:
        return False


pattern = r"(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+)\.com"


def categorize_data(texts):  
    output = {
        "supplier": [texts[1].description],
        "total": [],
        "date": [],
    }  # guess first word as company name lol
    i = 0
    for i, word in enumerate(texts):
        check = word.description
        
        if check_similarity(
            check, "total", 0.8
        ):  # for similarity in case one letter of total cut off
            for a in range(1, min(5, len(texts) - i)): #5 accounts for $SGD
                try:
                    amount = float(texts[i + a].description)
                    output["total"].append(amount)
                    break
                except ValueError:
                    continue

        elif check_similarity(check, "date", 0.75):
            output["date"].append(texts[i + 1].description)

    return output


if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)


'''def extract_middle_part(url):
    # Regex pattern to extract the middle part of the domain
    """Extract the middle part of the given URL."""
    match = re.search(pattern, url)
    if match:
        return match.group(1)  # Return the captured group (the middle part)
    return False  # Return None if no match is found
'''
