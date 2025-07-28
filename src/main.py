# # import os
# # import time
# # from utils import list_pdf_files, write_json_output
# # from heading_extractor import extract_outline



# import os
# import time
# from utils import list_pdf_files, write_json_output
# from heading_extractor import extract_outline  # Import the main function

# # Define relative directories for input and output
# # Your container can map volumes to these local directories
# INPUT_DIR = "input"
# OUTPUT_DIR = "output"

# def main():
#     """
#     Processes all PDF files in the INPUT_DIR, extracts title from first page
#     and headings (including first page headings and outline from page 2 onwards),
#     and saves the results to the OUTPUT_DIR according to the provided schema.
#     """
#     # Ensure directories exist
#     os.makedirs(INPUT_DIR, exist_ok=True)
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
        
#     pdf_files = list_pdf_files(INPUT_DIR)
        
#     if not pdf_files:
#         print(f"[INFO] No PDF files found in the '{INPUT_DIR}' directory.")
#         print("Please add your PDF files to the 'input' folder and run again.")
#         return

#     print(f"[INFO] Found {len(pdf_files)} PDF(s) to process.")
        
#     for pdf_path in pdf_files:
#         fname = os.path.basename(pdf_path)
#         out_json_path = os.path.join(OUTPUT_DIR, fname.replace(".pdf", ".json"))
                
#         print(f"\n[INFO] Processing {fname}...")
#         t_start = time.time()
                
#         # Extract title and outline according to schema
#         result = extract_outline(pdf_path)
        
#         write_json_output(out_json_path, result)
                
#         duration = time.time() - t_start
        
#         print(f"✅ Finished processing {fname} in {duration:.2f}s.")
#         print(f"   Title extracted: '{result['title']}'")
#         print(f"   Headings found: {len(result['outline'])}")
#         print(f"   Output saved to: {out_json_path}")

# if __name__ == "__main__":
#     main()


#!/usr/bin/env python3
"""
Main script for processing PDFs in Docker environment.
Processes all PDFs in /app/input and saves JSON results to /app/output.
"""

import os
import json
import sys
from pathlib import Path
import traceback

# Add the current directory to Python path
sys.path.append('/app/src')

try:
    from heading_extractor import extract_outline
except ImportError as e:
    print(f"[ERROR] Cannot import heading_extractor: {e}")
    sys.exit(1)

def process_pdfs_in_docker():
    """Process all PDFs in Docker input directory and save to output directory."""
    
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Ensure directories exist
    if not input_dir.exists():
        print(f"[ERROR] Input directory {input_dir} does not exist")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"[ERROR] No PDF files found in {input_dir}")
        sys.exit(1)
    
    print(f"[INFO] Found {len(pdf_files)} PDF(s) to process.")
    
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        try:
            print(f"[INFO] Processing {pdf_file.name}...")
            
            # Extract outline
            result = extract_outline(str(pdf_file))
            
            # Generate output filename
            json_filename = pdf_file.stem + ".json"
            json_path = output_dir / json_filename
            
            # Validate result structure
            if not isinstance(result, dict) or 'title' not in result or 'outline' not in result:
                print(f"[ERROR] Invalid result structure for {pdf_file.name}")
                result = {
                    "title": "Processing Error",
                    "outline": []
                }
            
            # Ensure outline is a list
            if not isinstance(result['outline'], list):
                result['outline'] = []
            
            # Clean up outline items to match schema
            cleaned_outline = []
            for item in result['outline']:
                if isinstance(item, dict) and all(key in item for key in ['level', 'text', 'page']):
                    cleaned_outline.append({
                        "level": str(item['level']),
                        "text": str(item['text']),
                        "page": int(item['page']) if isinstance(item['page'], (int, float)) else 1
                    })
            
            result['outline'] = cleaned_outline
            
            # Save JSON result
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"[SUCCESS] Saved {json_filename}")
            print(f"[INFO] Title: '{result['title']}'")
            print(f"[INFO] Found {len(result['outline'])} headings")
            
            successful += 1
            
        except Exception as e:
            print(f"[ERROR] Failed to process '{pdf_file.name}': {e}")
            print("[DEBUG] Full traceback:")
            traceback.print_exc()
            
            # Create error JSON file
            error_result = {
                "title": "Processing Error",
                "outline": []
            }
            
            json_filename = pdf_file.stem + ".json"
            json_path = output_dir / json_filename
            
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(error_result, f, ensure_ascii=False, indent=2)
                print(f"[INFO] Created error JSON for {pdf_file.name}")
            except Exception as save_error:
                print(f"[ERROR] Could not save error JSON: {save_error}")
            
            failed += 1
    
    print(f"\n[SUMMARY] Processing complete:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(pdf_files)}")
    
    # List output files
    output_files = list(output_dir.glob("*.json"))
    print(f"[INFO] Generated {len(output_files)} JSON files in {output_dir}")
    
    for output_file in output_files:
        print(f"  - {output_file.name}")

def main():
    """Main entry point."""
    print("[INFO] Starting PDF outline extraction...")
    print(f"[INFO] Python version: {sys.version}")
    print(f"[INFO] Working directory: {os.getcwd()}")
    print(f"[INFO] Python path: {sys.path}")
    
    try:
        process_pdfs_in_docker()
        print("[INFO] All processing completed successfully.")
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()