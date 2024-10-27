from google.cloud import vision
from dotenv import load_dotenv
import os
import difflib

# Load environment variables from .env file
load_dotenv()

# Access the GOOGLE_APPLICATION_CREDENTIALS variable
google_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Initialize the Vision API client
client = vision.ImageAnnotatorClient()


def check_similarity(text, template):
    if difflib.SequenceMatcher(None, text.upper(), template.upper()).ratio() >= 0.8:
        return True
    else:
        return False


def process_image(image_path):
    # Load the image
    with open(image_path, "rb") as img_file:
        content = img_file.read()

    image = vision.Image(content=content)
    # Call the Vision API
    response = client.text_detection(image=image)
    texts = response.text_annotations
    # full_text_annotations: pages --> list of block --> list of paragraph --> list of words(letters)
    i = 0
    for word in texts:
        if check_similarity(
            word.description, "total"
        ):  # for similarity in case one letter of total cut off
            for a in range(1, 5):  # 5 is arbitary, should be length of texts - i:
                amount = texts[i + a].description
                try:
                    float(amount)
                    print(amount)
                    break
                except:
                    continue

        i += 1
        # if total not found
    # Handle potential errors
    if response.error.message:
        raise Exception(f"{response.error.message}")

    text = "\n".join([text.description for text in texts])
    return text


# Call the function to process the image and save the result
process_image("./test2.jpg")
