# 🩺 Carelinq Unified Backend

A high-performance, AI-powered medical portal backend built with **FastAPI**. This project unifies an **AI Scribe**, a specialized **Oncology Chatbot**, and a **Medical Summary Generator** into a single, scalable architecture.

## 🚀 Key Features

- **AI Medical Scribe**: Near-real-time transcription and clinical entity extraction.
- **Oncology Assistant**: Context-aware chatbot with medical guardrails.
- **Summary Generator**: Generates professional, downloadable **PDF medical reports**.
- **OCR Engine**: Extracts text from medical PDFs and images.

## 📁 Project Structure

```text
backend/
├── main.py              # Application entry point
├── api/                 # API Routes
├── services/            # Core Business Logic
├── db/                  # Database management
└── core/                # Global Settings & Security
```

## ⚙️ Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Setup Environment**:
   Copy `.env.example` to `.env` and add your `GROQ_API_KEY`.
3. **Run Server**:
   ```bash
   uvicorn main:app --reload
   ```

## 🧪 API Documentation

Once running, visit [http://localhost:8000/docs](http://localhost:8000/docs) for full interactive documentation.
