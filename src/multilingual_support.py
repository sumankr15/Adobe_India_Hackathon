import fitz
import re
from typing import List, Union

def extract_text_sample_from_page(page: fitz.Page, is_scanned: bool = False) -> str:
    """Extract a text sample from the page for language detection."""
    try:
        if is_scanned:
            # For scanned documents, try OCR
            try:
                text = page.get_text("text", languages="eng")  # Default to English for OCR
            except:
                text = page.get_text("text")
        else:
            # For native PDFs, extract text directly
            text = page.get_text("text")
        
        # Clean and limit the text sample
        text = text.strip()
        
        # Take first 1000 characters for language detection
        if len(text) > 1000:
            text = text[:1000]
            
        return text
    except Exception as e:
        print(f"[WARNING] Failed to extract text sample from page: {e}")
        return ""

def detect_language_from_text(text: str) -> List[str]:
    """Detect language from text using simple heuristics."""
    if not text or not text.strip():
        return ["eng"]  # Default to English
    
    text = text.lower()
    
    # Simple language detection based on common words/patterns
    language_indicators = {
        "eng": [
            r'\bthe\b', r'\band\b', r'\bof\b', r'\bto\b', r'\ba\b', r'\bin\b',
            r'\bthat\b', r'\bhave\b', r'\bi\b', r'\bit\b', r'\bfor\b', r'\bnot\b',
            r'\bon\b', r'\bwith\b', r'\bhe\b', r'\bas\b', r'\byou\b', r'\bdo\b',
            r'\bat\b', r'\bthis\b', r'\bbut\b', r'\bhis\b', r'\bby\b', r'\bfrom\b'
        ],
        "fra": [
            r'\ble\b', r'\bde\b', r'\bet\b', r'\bà\b', r'\bun\b', r'\bil\b',
            r'\bêtre\b', r'\bavec\b', r'\bne\b', r'\bse\b', r'\bpas\b', r'\btout\b',
            r'\bpour\b', r'\bsur\b', r'\bavec\b', r'\bson\b', r'\bune\b', r'\bdu\b'
        ],
        "deu": [
            r'\bder\b', r'\bdie\b', r'\bdas\b', r'\bund\b', r'\bin\b', r'\bvon\b',
            r'\bzu\b', r'\bmit\b', r'\bist\b', r'\bauf\b', r'\bfür\b', r'\bals\b',
            r'\bauch\b', r'\bnicht\b', r'\bsich\b', r'\bwird\b', r'\bein\b', r'\beine\b'
        ],
        "spa": [
            r'\bel\b', r'\bla\b', r'\bde\b', r'\bque\b', r'\by\b', r'\ba\b',
            r'\ben\b', r'\bun\b', r'\bser\b', r'\bse\b', r'\bno\b', r'\bte\b',
            r'\blo\b', r'\ble\b', r'\bda\b', r'\bsu\b', r'\bpor\b', r'\bson\b'
        ],
        "ita": [
            r'\bil\b', r'\bdi\b', r'\bche\b', r'\be\b', r'\bla\b', r'\bun\b',
            r'\ba\b', r'\bper\b', r'\bnon\b', r'\bcon\b', r'\bsi\b', r'\bsu\b',
            r'\bcome\b', r'\bdal\b', r'\bma\b', r'\blo\b', r'\bgli\b', r'\bnel\b'
        ],
        "por": [
            r'\bo\b', r'\ba\b', r'\bde\b', r'\bque\b', r'\be\b', r'\bdo\b',
            r'\bda\b', r'\bem\b', r'\bum\b', r'\bpara\b', r'\bcom\b', r'\bnão\b',
            r'\buma\b', r'\bos\b', r'\bno\b', r'\bse\b', r'\bna\b', r'\bpor\b'
        ]
    }
    
    # Count matches for each language
    language_scores = {}
    for lang, patterns in language_indicators.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, text))
            score += matches
        language_scores[lang] = score
    
    # Find the language with the highest score
    if language_scores:
        detected_lang = max(language_scores, key=language_scores.get)
        if language_scores[detected_lang] > 0:
            return [detected_lang]
    
    # If no clear language detected, return English as default
    return ["eng"]

def get_detected_languages(page: Union[fitz.Page, str], is_scanned: bool = False) -> List[str]:
    """
    Detect languages from a page or text sample.
    
    Args:
        page: Either a fitz.Page object or a text string
        is_scanned: Whether the PDF is scanned (affects text extraction)
        
    Returns:
        List of detected language codes
    """
    try:
        # Handle both Page objects and text strings
        if isinstance(page, fitz.Page):
            text_sample = extract_text_sample_from_page(page, is_scanned)
        elif isinstance(page, str):
            text_sample = page
        else:
            print(f"[WARNING] Unexpected input type for language detection: {type(page)}")
            return ["eng"]
        
        if not text_sample.strip():
            print("[INFO] No text found for language detection, defaulting to English")
            return ["eng"]
        
        detected_languages = detect_language_from_text(text_sample)
        print(f"[INFO] Detected languages: {detected_languages}")
        
        return detected_languages
        
    except Exception as e:
        print(f"[ERROR] Language detection failed: {e}")
        return ["eng"]  # Fallback to English

def get_tesseract_lang_string(languages: List[str]) -> str:
    """
    Convert language codes to Tesseract language string.
    
    Args:
        languages: List of language codes (e.g., ['eng', 'fra'])
        
    Returns:
        Tesseract language string (e.g., 'eng+fra')
    """
    if not languages:
        return "eng"
    
    # Map common language codes to Tesseract codes
    tesseract_mapping = {
        "eng": "eng",
        "fra": "fra", 
        "deu": "deu",
        "spa": "spa",
        "ita": "ita",
        "por": "por",
        "rus": "rus",
        "jpn": "jpn",
        "chi_sim": "chi_sim",
        "chi_tra": "chi_tra",
        "ara": "ara",
        "hin": "hin"
    }
    
    # Convert to Tesseract codes
    tesseract_langs = []
    for lang in languages:
        if lang in tesseract_mapping:
            tesseract_langs.append(tesseract_mapping[lang])
        else:
            print(f"[WARNING] Unknown language code '{lang}', using English")
            tesseract_langs.append("eng")
    
    # Remove duplicates and join with '+'
    tesseract_langs = list(dict.fromkeys(tesseract_langs))  # Remove duplicates while preserving order
    result = "+".join(tesseract_langs)
    
    print(f"[INFO] Tesseract language string: '{result}'")
    return result

def is_multilingual_document(page: fitz.Page, is_scanned: bool = False) -> bool:
    """
    Check if the document appears to be multilingual.
    
    Args:
        page: Page to analyze
        is_scanned: Whether the PDF is scanned
        
    Returns:
        True if multiple languages are detected
    """
    try:
        languages = get_detected_languages(page, is_scanned)
        return len(languages) > 1
    except:
        return False

def get_primary_language(page: fitz.Page, is_scanned: bool = False) -> str:
    """
    Get the primary language of a page.
    
    Args:
        page: Page to analyze
        is_scanned: Whether the PDF is scanned
        
    Returns:
        Primary language code
    """
    try:
        languages = get_detected_languages(page, is_scanned)
        return languages[0] if languages else "eng"
    except:
        return "eng"

# Additional utility functions for language handling

def get_language_name(lang_code: str) -> str:
    """Get human-readable language name from code."""
    lang_names = {
        "eng": "English",
        "fra": "French", 
        "deu": "German",
        "spa": "Spanish",
        "ita": "Italian",
        "por": "Portuguese",
        "rus": "Russian",
        "jpn": "Japanese",
        "chi_sim": "Chinese (Simplified)",
        "chi_tra": "Chinese (Traditional)",
        "ara": "Arabic",
        "hin": "Hindi"
    }
    return lang_names.get(lang_code, f"Unknown ({lang_code})")

def validate_tesseract_languages(lang_string: str) -> str:
    """Validate and clean Tesseract language string."""
    if not lang_string:
        return "eng"
    
    # Split by '+' and validate each language
    langs = lang_string.split('+')
    valid_langs = []
    
    valid_tesseract_codes = {
        "eng", "fra", "deu", "spa", "ita", "por", "rus", "jpn", 
        "chi_sim", "chi_tra", "ara", "hin", "nld", "swe", "dan", "nor"
    }
    
    for lang in langs:
        lang = lang.strip().lower()
        if lang in valid_tesseract_codes:
            valid_langs.append(lang)
        else:
            print(f"[WARNING] Invalid Tesseract language code '{lang}', skipping")
    
    if not valid_langs:
        print("[WARNING] No valid language codes found, defaulting to English")
        return "eng"
    
    return "+".join(valid_langs)