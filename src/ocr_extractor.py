import pytesseract
from PIL import Image
import fitz

def pdf_image_to_text(pdf_path):
    doc = fitz.open(pdf_path)
    text_pages = []
    for page_num in range(len(doc)):
        pix = doc[page_num].get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img, lang='eng+jpn+hin')
        text_pages.append(text)
    return text_pages
