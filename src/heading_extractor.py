# improved_heading_extractor.py

import fitz  # PyMuPDF
import re
from collections import Counter
from multilingual_support import get_detected_languages, get_tesseract_lang_string

# Fixed junk patterns - properly terminated strings
GENERIC_JUNK_PATTERNS = [
    re.compile(r'^(page|p\.)\s*\d+\s*$', re.IGNORECASE),
    re.compile(r'^\d+$'),  # Numbers only
    re.compile(r'^(www\.|http|https)', re.IGNORECASE),  # URLs
    re.compile(r'@\w+\.\w+', re.IGNORECASE),  # Email addresses
    re.compile(r'^\s*[•\-]\s*$'),  # Just bullet points
    re.compile(r'^(date|signature|for|time|address|rsvp|phone|email)[\s:]*$', re.IGNORECASE),  # Form labels
    re.compile(r'^(closed|parents|please|hope)[\s\w]*$', re.IGNORECASE),  # Common form text
]

def has_native_text(doc: fitz.Document) -> bool:
    """Checks the first few pages to see if the document contains native text."""
    for page in doc.pages(stop=min(5, len(doc))):
        if page.get_text("text").strip():
            return True
    return False

def get_table_areas(page):
    """Get table areas and boxed/bordered areas, excluding standalone headings."""
    excluded_areas = []
    
    try:
        # Method 1: PyMuPDF table detection
        tables = page.find_tables()
        for table in tables:
            excluded_areas.append(table.bbox)
        
        # Method 2: Drawn rectangles
        drawings = page.get_drawings()
        rects = []
        for drawing in drawings:
            if 'rect' in drawing:
                rect = fitz.Rect(drawing['rect'])
                if rect.width > 30 and rect.height > 15:
                    rects.append(rect)
        excluded_areas.extend(rects)
        
        # Method 3: Text block analysis for boxes
        text_dict = page.get_text("dict")
        blocks = text_dict.get("blocks", [])
        
        for block in blocks:
            if block.get("type") != 0:
                continue
                
            block_bbox = fitz.Rect(block.get("bbox", [0, 0, 0, 0]))
            block_text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span.get("text", "") + " "
            block_text = block_text.strip()
            
            # Skip likely headings
            words = block_text.split()
            if len(words) <= 5 and len(block_text) < 50:
                if (block_text.isupper() or 
                    any(word.lower() in ['pathway', 'options', 'section', 'chapter', 'part'] for word in words)):
                    continue
            
            is_boxed_content = False
            
            # Box content indicators
            box_indicators = ["mission statement:", "goals:", "objectives:", "summary:", "abstract:", 
                             "note:", "important:", "warning:", "caution:", "definition:", "example:", 
                             "key points:", "highlights:"]
            
            if any(block_text.lower().startswith(indicator) for indicator in box_indicators):
                is_boxed_content = True
            elif len(words) > 10 and len(block_text) > 100:
                lines = block.get("lines", [])
                if lines:
                    first_line_x = lines[0].get("bbox", [0, 0, 0, 0])[0]
                    page_width = page.rect.width
                    
                    if (first_line_x > page_width * 0.08 and block_bbox.width < page_width * 0.85):
                        for rect in rects:
                            expanded_rect = rect + (-5, -5, 5, 5)
                            if expanded_rect.contains(block_bbox) or rect.intersects(block_bbox):
                                is_boxed_content = True
                                break
                        
                        if not is_boxed_content:
                            similar_indent_count = sum(1 for other_block in blocks 
                                                     if other_block != block and other_block.get("lines") 
                                                     and abs(other_block.get("lines")[0].get("bbox", [0,0,0,0])[0] - first_line_x) < 15)
                            if similar_indent_count <= 1:
                                is_boxed_content = True
            elif "•" in block_text or "●" in block_text or block_text.count('\n') > 2:
                for rect in rects:
                    if rect.intersects(block_bbox):
                        is_boxed_content = True
                        break
            
            if is_boxed_content:
                excluded_areas.append(block_bbox + (-3, -3, 3, 3))
        
    except Exception as e:
        print(f"[WARNING] Box detection failed: {e}")
    
    # Merge overlapping areas
    final_areas = []
    excluded_areas.sort(key=lambda x: (fitz.Rect(x).y0, fitz.Rect(x).x0))
    
    for area in excluded_areas:
        area_rect = fitz.Rect(area)
        merged = False
        for i, existing in enumerate(final_areas):
            existing_rect = fitz.Rect(existing)
            if (existing_rect + (-8, -8, 8, 8)).intersects(area_rect):
                final_areas[i] = existing_rect | area_rect
                merged = True
                break
        if not merged:
            final_areas.append(area_rect)
    
    return final_areas

def is_text_in_table(text_bbox, excluded_areas, margin=2):
    """Check if text bbox overlaps with any excluded area."""
    if not excluded_areas:
        return False
    
    text_rect = fitz.Rect(text_bbox)
    for area_bbox in excluded_areas:
        area_rect = fitz.Rect(area_bbox) + (-margin, -margin, margin, margin)
        if text_rect.intersects(area_rect):
            return True
    return False

def extract_title_from_document(doc, tesseract_langs=None, is_scanned=False) -> str:
    """Extract title from document."""
    # Try metadata first
    metadata = doc.metadata
    if metadata.get('title') and metadata['title'].strip():
        title = metadata['title'].strip()
        if len(title) < 100:
            return title
    
    # Extract from first page
    first_page = doc[0]
    
    try:
        excluded_areas = get_table_areas(first_page)
        page_data = first_page.get_text("dict", languages=tesseract_langs) if is_scanned else first_page.get_text("dict")
        
        title_candidates = []
        page_height = first_page.rect.height
        
        for block in page_data.get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                
                bbox = line.get('bbox', [0, 0, 0, 0])
                relative_y = bbox[1] / page_height if page_height > 0 else 0
                
                if (is_text_in_table(bbox, excluded_areas) or relative_y > 0.4):
                    continue
                
                text = " ".join(s["text"] for s in spans).strip()
                if (not text or len(text) < 3 or 
                    any(p.match(text) for p in GENERIC_JUNK_PATTERNS) or
                    text.lower().startswith(('page ', 'figure ', 'table ')) or
                    len(text) > 200):
                    continue
                
                title_candidates.append({
                    'text': text,
                    'font_size': round(spans[0]["size"]),
                    'position': relative_y,
                    'length': len(text)
                })
        
        if title_candidates:
            title_candidates.sort(key=lambda x: (x['font_size'], -x['position']), reverse=True)
            for candidate in title_candidates:
                text = candidate['text']
                if (3 <= len(text.split()) <= 20 and not text.endswith('.') and len(text) >= 10):
                    return text
            return title_candidates[0]['text']
    
    except Exception as e:
        print(f"[ERROR] Title extraction failed: {e}")
    
    return ""

def is_bold_or_emphasized(spans) -> bool:
    """Check if text spans indicate bold/emphasized formatting."""
    if not spans:
        return False
    
    for span in spans:
        font_name = span.get('font', '').lower()
        flags = span.get('flags', 0)
        
        if (flags & 16) or any(indicator in font_name for indicator in ['bold', 'black', 'heavy']):
            return True
    return False

def is_simple_junk(text: str) -> bool:
    """Simple junk detection."""
    text = text.strip()
    
    if (not text or any(p.match(text) for p in GENERIC_JUNK_PATTERNS) or
        len(text) < 2 or text.count('_') > len(text) // 2 or 
        text.count('-') > len(text) // 2 or 
        (text.count(' ') == 0 and len(text) > 50)):
        return True
    return False

def should_combine_lines(line1_data, line2_data, max_distance=8):
    """Check if two lines should be combined as same heading."""
    y_distance = abs(line2_data['bbox'][1] - line1_data['bbox'][3])
    size_diff = abs(line1_data['font_size'] - line2_data['font_size'])
    x_alignment = abs(line1_data['bbox'][0] - line2_data['bbox'][0])
    
    return y_distance <= max_distance and size_diff <= 1 and x_alignment <= 15

def extract_outline(pdf_path: str) -> dict:
    """Extract outline from PDF, excluding table areas and combining continuation lines."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"title": f"Error opening PDF: {e}", "outline": []}

    total_pages = len(doc)
    if total_pages == 0:
        doc.close()
        return {"title": "", "outline": []}

    print(f"[INFO] Analyzing '{pdf_path}' ({total_pages} pages)...")
    
    # Check if scanned
    is_scanned = not has_native_text(doc)
    if is_scanned:
        print("[INFO] Document appears to be scanned. OCR will be required.")
    
    # Language detection
    first_page_text = doc[0].get_text(sort=True)
    detected_langs = get_detected_languages(first_page_text[:1000]) if first_page_text else ['eng']
    tesseract_langs = get_tesseract_lang_string(detected_langs)
    print(f"[INFO] Detected languages: {detected_langs}")

    # Extract title
    title = extract_title_from_document(doc, tesseract_langs, is_scanned)

    # Analyze font patterns
    font_counts = Counter()
    
    for page_num in range(total_pages):
        page = doc[page_num]
        excluded_areas = get_table_areas(page)
        if excluded_areas:
            print(f"[INFO] Found {len(excluded_areas)} table/box area(s) on page {page_num + 1}")
        
        if is_scanned:
            try:
                blocks = page.get_text("dict", languages=tesseract_langs).get("blocks", [])
            except RuntimeError:
                blocks = page.get_text("dict").get("blocks", [])
        else:
            blocks = page.get_text("dict").get("blocks", [])
        
        for block in blocks:
            for line in block.get("lines", []):
                line_bbox = line.get('bbox', [0, 0, 0, 0])
                if is_text_in_table(line_bbox, excluded_areas):
                    continue
                    
                for span in line.get("spans", []):
                    size = round(span["size"])
                    if size > 0:
                        font_counts[size] += 1

    if not font_counts:
        doc.close()
        return {"title": title, "outline": []}

    # Find heading sizes
    body_size = font_counts.most_common(1)[0][0]
    heading_sizes = sorted([size for size in font_counts if size > body_size], reverse=True)
    level_map = {size: f"H{i+1}" for i, size in enumerate(heading_sizes)}
    
    print(f"[INFO] Body text size: {body_size}, Heading sizes: {heading_sizes}")

    # Extract headings
    headings = []
    seen_texts = set()
    
    for page_num in range(total_pages):
        page = doc[page_num]
        excluded_areas = get_table_areas(page)
        
        if is_scanned:
            try:
                page_data = page.get_text("dict", languages=tesseract_langs)
            except RuntimeError:
                page_data = page.get_text("dict")
        else:
            page_data = page.get_text("dict")

        potential_lines = []
        
        for block in page_data.get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                line_bbox = line.get('bbox', [0, 0, 0, 0])
                if is_text_in_table(line_bbox, excluded_areas):
                    continue

                text = " ".join(s["text"] for s in spans).strip()
                
                if (not text or is_simple_junk(text) or 
                    (page_num == 0 and title and text.strip() == title.strip())):
                    continue
                
                potential_lines.append({
                    'text': text,
                    'font_size': round(spans[0]["size"]),
                    'bbox': line_bbox,
                    'spans': spans,
                    'is_bold': is_bold_or_emphasized(spans)
                })
        
        # Process and combine lines
        i = 0
        while i < len(potential_lines):
            current_line = potential_lines[i]
            combined_text = current_line['text']
            
            j = i + 1
            while j < len(potential_lines) and should_combine_lines(potential_lines[j-1], potential_lines[j]):
                combined_text += " " + potential_lines[j]['text']
                j += 1
            
            if combined_text in seen_texts:
                i = j
                continue
            
            text = combined_text
            first_span_size = current_line['font_size']
            is_bold = current_line['is_bold']
            
            # Font size based detection
            if first_span_size in level_map:
                word_count = len(text.split())
                if word_count <= 20 and word_count >= 1 and len(text) >= 3:
                    headings.append({
                        "level": level_map[first_span_size],
                        "text": text,
                        "page": page_num + 1
                    })
                    seen_texts.add(text)
                    i = j
                    continue
            
            # Bold text detection
            if is_bold and first_span_size >= body_size:
                word_count = len(text.split())
                if (word_count <= 15 and word_count >= 1 and len(text) >= 3 and 
                    not text.endswith('.') and not re.search(r'\d+%|\$|₹', text)):
                    
                    level_num = len(heading_sizes) + 1 if first_span_size > body_size else len(heading_sizes) + 2
                    if first_span_size == body_size and text.strip().endswith(':'):
                        level_num = len(heading_sizes) + 2
                    
                    headings.append({
                        "level": f"H{level_num}",
                        "text": text,
                        "page": page_num + 1
                    })
                    seen_texts.add(text)
            
            i = j

    doc.close()
    
    print(f"[INFO] Extracted title: '{title}'")
    print(f"[INFO] Found {len(headings)} headings total")
    
    return {
        "title": title,
        "outline": headings
    }