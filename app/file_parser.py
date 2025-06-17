# app/file_parser.py
import os
import pytesseract
from PIL import Image
import pandas as pd
import pdfplumber
import docx

def parse_file(path: str) -> str:
    ext = os.path.splitext(path)[-1].lower()
    try:
        if ext == '.txt':
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()[:1000]
        elif ext == '.csv':
            df = pd.read_csv(path)
            return df.head(5).to_string()
        elif ext in ['.png', '.jpg', '.jpeg']:
            text = pytesseract.image_to_string(Image.open(path))
            return text.strip()[:500]
        elif ext == '.pdf':
            with pdfplumber.open(path) as pdf:
                text = ''.join([page.extract_text() or '' for page in pdf.pages])
                return text.strip()[:1000]
        elif ext == '.docx':
            doc = docx.Document(path)
            text = '\n'.join([para.text for para in doc.paragraphs])
            return text.strip()[:1000]
        elif ext in ['.py', '.ipynb']:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()[:1000]
        else:
            return "[Unsupported file type]"

    except Exception as e:
        return f"[Error parsing file: {e}]"
