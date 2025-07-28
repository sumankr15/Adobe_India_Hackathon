# 📄 PDF Outline Extractor

**Intelligent PDF structure extraction tool that automatically identifies titles and hierarchical headings (H1/H2/H3) from both digital and scanned PDF documents. Runs completely offline in a Docker container optimized for AMD64 architecture.**

---

## 🎯 Overview

PDFs are ubiquitous but lack machine-readable structure. This tool bridges that gap by extracting meaningful document outlines that enable:

- 🔍 **Advanced semantic search** and intelligent document navigation
- 🤖 **AI-powered recommendations** and content analysis
- 📊 **Automated knowledge extraction** for enterprise workflows
- 📚 **Document summarization** and insight generation

---

## ✨ Key Features

### Input Support

- PDF documents up to **50 pages**
- Both **digital** (text-based) and **scanned/image-based** PDFs
- Multilingual document support

### Extraction Capabilities

- **Document Title** (from metadata or intelligent first-page detection)
- **Hierarchical Headings** (H1, H2, H3) with:
  - Exact text content
  - Heading level classification
  - Precise page number location

### Technical Specifications

- **100% Offline Operation** - No internet connectivity required
- **AMD64 (x86_64) Optimized** - Runs on standard CPU hardware
- **Docker Containerized** - Consistent execution across environments
- **Fast Processing** - ≤10 seconds for 50-page documents
- **Lightweight** - Total container size ≤200MB including all dependencies

## 📋 Output Format

Each processed PDF generates a corresponding JSON file with this exact structure:

---

## 🔧 Technical Architecture

### Core Processing Pipeline

1. **PDF Analysis**

   - Utilizes **PyMuPDF (fitz)** for comprehensive document parsing
   - Extracts text, font properties, layout blocks, and page structure
   - Analyzes document metadata for title information

2. **Title Extraction Strategy**

   - **Primary**: Extract from PDF metadata fields
   - **Fallback**: Heuristic analysis of first page content
     - Identifies largest/most prominent text elements
     - Excludes headers, footers, and decorative elements
     - Filters out table contents and form fields

3. **Heading Classification Algorithm**

   - **Font Analysis**: Compares font sizes relative to body text
   - **Style Detection**: Identifies bold/emphasized text formatting
   - **Structural Analysis**: Examines document layout and positioning
   - **Level Assignment**: Maps to H1/H2/H3 based on hierarchical importance
   - **Multi-line Handling**: Intelligently combines fragmented headings

4. **OCR Fallback System**

   - **Trigger**: Activated when no extractable text is detected
   - **Engine**: Tesseract OCR via pytesseract wrapper
   - **Language Support**: Auto-detection with 15+ language packs
   - **Image Processing**: Pillow library for optimal OCR preparation

5. **Multilingual Processing**
   - Real-time language detection from document content
   - Automatic Tesseract language pack selection
   - Optimized for English, European, and major Asian languages

---

## 🚀 Quick Start Guide

### Prerequisites

- Docker installed and running
- AMD64/x86_64 architecture system
- Minimum 8GB RAM recommended for optimal performance

### Custom Language Support

To add additional language support, modify `multilingual_support.py` and rebuild the container with the required Tesseract language packs.

---

## 🐛 Troubleshooting Guide

### Common Issues

**No JSON output generated:**

- Verify PDF files are in the correct input directory
- Check Docker volume mounting paths
- Ensure PDFs are not password-protected or corrupted

**OCR not working for scanned PDFs:**

- Confirm required language packs are installed
- Check image quality and resolution of scanned content
- Review container logs for OCR-specific errors

**Performance issues:**

- Ensure sufficient RAM allocation to Docker
- Check if PDFs exceed 50-page limit
- Monitor system resources during processing

**Container build failures:**

- Verify AMD64 platform specification
- Check internet connectivity during build (required for dependency download)
- Ensure Docker has sufficient disk space

---

## 🚀 Build Using

docker buildx build --platform linux/amd64 -t mysolutionname:somerandomidentifier .

## Run using:-

docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none mysolutionname:somerandomidentifier
