import os
import easyocr
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
from core.config import settings

class OCRService:
    def __init__(self):
        # Initialize EasyOCR reader
        self.reader = easyocr.Reader(['en'])

    def extract_text_from_file(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext in [".png", ".jpg", ".jpeg"]:
            return self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        doc = fitz.open(pdf_path)
        full_text = []
        for page in doc:
            # First try direct text extraction
            text = page.get_text()
            if text.strip():
                full_text.append(text)
            else:
                # If no text, use OCR on the page image
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text = self.extract_text_from_image_obj(img)
                full_text.append(ocr_text)
        return "\n\n".join(full_text)

    def extract_text_from_image(self, img_path: str) -> str:
        results = self.reader.readtext(img_path)
        return " ".join([res[1] for res in results])

    def extract_text_from_image_obj(self, img_obj: Image.Image) -> str:
        # Convert PIL Image to numpy array for EasyOCR
        img_np = np.array(img_obj)
        results = self.reader.readtext(img_np)
        return " ".join([res[1] for res in results])

ocr_service = OCRService()
