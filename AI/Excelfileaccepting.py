import os
import pandas as pd
import json
import time
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

# Initialize the Client
client = genai.Client(api_key=GEMINI_API_KEY)

def wait_for_files_active(files):
    """Waits for the given files to be active."""
    print("Waiting for file processing...")
    for f in files:
        # In the new SDK, we fetch the file by its name
        file_ref = client.files.get(name=f.name)
        while file_ref.state == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(5)
            file_ref = client.files.get(name=f.name)
        if file_ref.state != "ACTIVE":
            raise Exception(f"File {file_ref.name} failed to process")
    print("...all files ready\n")

# Function to handle file upload and data extraction
def handle_file_upload(file_path):
    """Handles the uploaded file using the new google-genai SDK."""
    
    # 1. Convert Excel to CSV
    csv_file_path = file_path.replace('.xlsx', '.csv')
    try:
        df = pd.read_excel(file_path)
        df.to_csv(csv_file_path, index=False)
        print(f"Converted {file_path} to {csv_file_path}.")
    except Exception as e:
        print(f"Error converting Excel to CSV: {e}")
        return None

    try:
        # 2. Upload to Gemini
        print(f"Uploading {csv_file_path}...")
        uploaded_file = client.files.upload(path=csv_file_path)
        
        # 3. Wait for processing
        wait_for_files_active([uploaded_file])

        # 4. Generate content (Extraction)
        prompt = (
            "Please extract the following data from the attached CSV file for each row:\n"
            "- `telegram_username`\n"
            "- `family_member`\n"
            "- `name`\n"
            "- `phone`\n"
            "- `year`\n\n"
            "Return the data as a JSON list of objects."
        )

        # Configuration for the model
        config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )

        # Create response
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[uploaded_file, prompt],
            config=config
        )

        # 5. Process and return response
        extracted_data = response.text
        print("Extracted Data:", extracted_data)
        return extracted_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    finally:
        # Clean up the CSV file
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
            print(f"Temporary file {csv_file_path} removed.")

# Example usage (commented out as per your original)
# handle_file_upload("path_to_your_file.xlsx")