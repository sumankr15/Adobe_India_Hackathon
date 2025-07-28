# Approach Explanation

**Goal**:  
Extract a structured hierarchical outline from both digital and scanned PDFs, identifying the document title and three heading levels (H1, H2, H3) reliably and efficiently — all within a fully offline, Dockerized AMD64 environment.

---

## 📋 Pipeline Overview

### 1. Text and Layout Extraction

Utilizes a combination of PDF parsing libraries to extract detailed content and layout data:

- **PyMuPDF (fitz)**: Primary engine for reading per-page text blocks, font properties (size, family, bold/italic status), and spatial positioning.
- **pdfminer.six**: Optionally used for finer-grained character-level parsing and verification.

Each text element is enriched with:

- Font size, weight, and styling (bold, italic, caps)
- Coordinates and layout position (x/y coordinates, top/mid/bottom)
- Page number and block grouping

**Key Strengths**:

- Goes beyond font size: spatial layout and font styling also guide structure.
- Handles complex layouts with multi-column text, footers, headers, and decorative elements.

---

### 2. Title Detection

- First attempts to extract the title from the PDF metadata.
- If metadata is missing or unreliable:
  - Analyzes text on the **first page**.
  - Prioritizes large, **top-centered** text with unique styling (e.g., distinct font or color).
  - Ignores footer/header zones and tabular content.
  - Merges multi-line headings when necessary for better accuracy.

---

### 3. Heading Detection and Hierarchical Classification

- Identifies potential headings using **relative font sizes** and formatting patterns.
- Clusters font sizes in the document to differentiate between:
  - Body text
  - H1, H2, H3 levels

Factors considered:

- Font boldness and capitalization
- Indentation patterns
- Common numbering (e.g., `1.`, `1.2.`, `1.2.3.`)
- Line spacing and proximity (for multi-line headings)

Excludes:

- Text within tables
- Captions, labels, or graphical decorations

Each heading is mapped to its **page number** for traceability.

---

### 4. OCR Integration for Scanned PDFs

When a PDF contains little or no extractable text, a fallback OCR stage is triggered:

- Uses **Tesseract OCR** via `pytesseract` and **Pillow** for preprocessing (e.g., contrast adjustment).
- **Basic language detection** helps choose the correct OCR language model.
- Keeps runtime efficient by only enabling OCR if digital text is missing or very sparse.

---

## 🌍 Multilingual Detection

To support OCR for scanned PDFs in different languages, the system detects the most likely language **before** applying OCR.

### 🔎 Detection Strategy

- Based on text or OCR pre-check:
  - Unicode script checks (e.g., Devanagari → Hindi)
  - Regex patterns for stopwords or character ranges
- Language selection is mapped to Tesseract-compatible codes.

### 🌐 Default Supported Languages

| Language | Code    |
| -------- | ------- |
| English  | eng     |
| Hindi    | hin     |
| French   | fra     |
| Korean   | kor     |
| Mandarin | chi-sim |
| Italian  | ita     |
| Japanese | jpn     |

etc...

### 6. Output Generation

The final result is a clean JSON file per PDF that adheres strictly to the defined schema:

```json
{
  "title": "Document Title",
  "outline": [
    { "level": "H1", "text": "Main Section", "page": 1 },
    { "level": "H2", "text": "Subsection", "page": 2 },
    { "level": "H3", "text": "Detail Point", "page": 3 }
  ]
}
```

## ✅ Robustness & Design Considerations

-- Handles diverse PDF styles: research papers, business reports, manuals, educational books, etc.

-- Fully offline: no reliance on external APIs or web services.

## Modular codebase:

- heading_extractor.py: Title and heading logic

- ocr_extractor.py: OCR fallback logic

- utils.py: File I/O, text utilities

- Easy to extend or improve specific parts

## Summary

This solution uses a layered, modular pipeline that ensures reliable PDF structure extraction while meeting performance and offline execution goals:

- Rich metadata extraction via layout and font analysis

- Intelligent title and heading detection based on statistical and spatial cues

- OCR fallback for image-based content

- Output in machine-readable, consistent JSON format
