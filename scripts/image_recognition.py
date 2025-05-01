import os
from google.cloud import vision
from google.cloud.vision_v1 import types
import glob

def initialize_client():
    """
    Initialize the Google Cloud Vision client.
    Make sure to set the GOOGLE_APPLICATION_CREDENTIALS environment variable
    to the path of your credentials JSON file before running this script.
    """
    client = vision.ImageAnnotatorClient()
    return client

def detect_text(client, image_path):
    """
    Detect text in the given image using Google Cloud Vision API.
    
    Args:
        client: The initialized Google Cloud Vision client.
        image_path: Path to the image file.
    
    Returns:
        Detected text as a string, or empty string if no text is detected.
    """
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    image = types.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    if texts:
        return texts[0].description
    return ""

def process_images(input_dir, output_file):
    """
    Process all images in the input directory, detect text, and save results to output file.
    
    Args:
        input_dir: Directory containing images to process.
        output_file: File path to save the extracted text.
    """
    client = initialize_client()
    image_files = glob.glob(os.path.join(input_dir, "*.png")) + glob.glob(os.path.join(input_dir, "*.jpg"))
    results = []
    
    for image_path in image_files:
        print(f"Processing {image_path}...")
        text = detect_text(client, image_path)
        if text:
            results.append(f"Image: {os.path.basename(image_path)}\nText:\n{text}\n{'-'*50}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(results))
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    input_directory = "../REMimagesMeroitic"
    output_file = "../data/meroitic_image_text.txt"
    process_images(input_directory, output_file)
