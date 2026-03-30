import os
from typing import List, Dict, Optional
from fpdf import FPDF
from datetime import datetime
from groq import Groq
from core.config import settings

class SummaryService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None

    def generate_clinical_summary(self, transcript: str, entities: List[Dict]) -> str:
        if not self.client:
            return "Error: Groq API Key missing."
            
        entity_str = ", ".join([f"{e['text']} ({e['label']})" for e in entities])
        
        prompt = f"""
        You are a warm, highly empathetic medical scribe. Write a supportive 'Personalized Care Plan' for a patient.
        
        CONSULTATION DATA:
        - Transcription: {transcript}
        - Key Details: {entity_str}
        
        INSTRUCTIONS FOR EMPATHETIC CLARITY:
        1. **Tone**: Be warm, reassuring, and use 'You'/ 'Your'. 
        2. **Language**: Use 5th-grade reading level. Avoid jargon (e.g., 'high blood pressure' instead of 'hypertension').
        3. **Structure**: 
           - **Overview**: A friendly summary.
           - **Medicine Schedule**: Simple instructions.
           - **Your Next Steps**: Actionable items.
        
        YOUR PERSONALIZED CARE PLAN:
        """
        
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a warm medical assistant providing clear, low-jargon, and empathetic care plans."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def summarize_report(self, extracted_text: str) -> str:
        if not self.client:
            return "Error: Groq API Key missing."
            
        prompt = f"""
        You are a helpful clinical report analyzer. Summarize these medical report findings for a patient in plain, reassuring language.
        
        RAW EXTRACTED TEXT:
        {extracted_text}
        
        INSTRUCTIONS:
        1. **Overview**: Explain what kind of report this is (e.g., "This is your blood test report").
        2. **Key Findings**: List the most important numbers or results in simple terms (e.g., "Your sugar levels are normal").
        3. **Supportive Advice**: Add a reassuring sentence about discussing this with a doctor soon.
        
        YOUR REPORT SUMMARY:
        """
        
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a clinical assistant who simplifies report findings into clear, patient-friendly summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error summarizing report: {str(e)}"

    def generate_pdf_summary(self, transcript: str, entities: List[Dict], summary_text: str, output_path: str):
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, "Carelinq AI Medical Portal", ln=True, align="C")
        pdf.set_font("Arial", "I", 10)
        pdf.cell(190, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
        pdf.ln(10)
        
        # Section: Brief Summary
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, "Patient Summary", ln=True, fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 7, summary_text)
        pdf.ln(5)
        
        # Section: Extracted Entities
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "Key Clinical Details", ln=True, fill=True)
        pdf.set_font("Arial", "", 10)
        if not entities:
            pdf.cell(0, 7, "No medical entities identified.", ln=True)
        else:
            for ent in entities:
                pdf.set_font("Arial", "B", 9)
                pdf.write(7, f"{ent['label']}: ")
                pdf.set_font("Arial", "", 9)
                pdf.write(7, f"{ent['text']}\n")
        pdf.ln(5)
        
        # Optional: Raw Transcript (abridged if too long)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "Original Consultation Context", ln=True, fill=True)
        pdf.set_font("Arial", "I", 8)
        pdf.multi_cell(0, 5, transcript[:1500] + ("..." if len(transcript) > 1500 else ""))
        
        # Footer
        pdf.set_y(-25)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, "Disclaimer: This summary was generated by AI and must be reviewed by a qualified healthcare professional.", align="C")
        
        pdf.output(output_path)
        return output_path

summary_service = SummaryService()
