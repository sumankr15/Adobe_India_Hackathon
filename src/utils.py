# import os
# import json

# def list_pdf_files(input_dir):
#     return [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]

# def write_json_output(out_path, data):
#     with open(out_path, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)
# utils.py

import os
import json
import glob

def list_pdf_files(directory: str) -> list:
    """Finds all PDF files in a given directory."""
    if not os.path.isdir(directory):
        print(f"Error: Input directory '{directory}' not found.")
        return []
    return glob.glob(os.path.join(directory, '*.pdf'))

def write_json_output(filepath: str, data: dict):
    """Writes a dictionary to a JSON file, creating the directory if needed."""
    try:
        # Ensure the output directory exists
        output_dir = os.path.dirname(filepath)
        os.makedirs(output_dir, exist_ok=True)
        
        # Write the JSON file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing to {filepath}: {e}")
