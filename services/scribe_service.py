import os
import json
from typing import List, Dict, Optional
from groq import Groq
from rapidfuzz import process, fuzz
from core.config import settings

class ScribeService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
            
        # Common medical terms for fuzzy matching
        self.medical_dictionary = [
            "Metformin", "Lisinopril", "Diabetes", "Hypertension", "Glucose", 
            "Cholesterol", "Amoxicillin", "Ibuprofen", "Acetaminophen", "Asthma",
            "Atorvastatin", "Levothyroxine", "Amlodipine", "Metoprolol", "Omeprazole",
            "Insulin", "Prednisone", "Albuterol", "Warfarin", "Hydrochlorothiazide"
        ]

    def transcribe(self, audio_path: str) -> str:
        if not self.client:
            raise ValueError("Groq API Key missing.")
            
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file {audio_path} not found")
        
        # Open in binary mode and pass the file object directly for better MIME type detection
        with open(audio_path, "rb") as file_handle:
            transcription = self.client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), file_handle.read()), # Send basename + binary content
                model="whisper-large-v3",
                response_format="verbose_json",
            )
            
        return transcription.text

    def fuzzy_correct(self, text: str) -> str:
        words = text.split()
        corrected_words = []
        for word in words:
            if len(word) > 4:
                match = process.extractOne(word, self.medical_dictionary, scorer=fuzz.WRatio)
                if match and match[1] > 85:
                    corrected_words.append(match[0])
                    continue
            corrected_words.append(word)
        return " ".join(corrected_words)

    def extract_entities(self, text: str) -> List[Dict]:
        corrected_text = self.fuzzy_correct(text)
        return self.extract_detailed_entities(corrected_text)

    def extract_detailed_entities(self, text: str) -> List[Dict]:
        if not self.client:
            return []

        prompt = f"""
        Extract detailed medical information from the following consultation transcript.
        Focus on:
        - Patient Details (Age, Gender, ID)
        - Patient Surgery (Existing, upcoming, pre-op, post-op)
        - Medications (Name, Dosage, Frequency, Time Slot)
        - Injuries (Details, location, pre/post-surgery state)
        - Pain levels and locations
        
        TRANSCRIPT: {text}
        
        RETURN ONLY A JSON ARRAY of objects: [{{"text": "ENTITY", "label": "LABEL"}}]
        Valid Labels: PATIENT_DETAIL, SURGERY, MEDICATION, DOSAGE, TIME_SLOT, INJURY, PAIN.
        """
        
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = completion.choices[0].message.content
            data = json.loads(content)
            if isinstance(data, dict) and "entities" in data:
                 return data["entities"]
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            print(f"Detailed extraction failed: {e}")
            return []

    def generate_summary(self, transcript: str, entities: List[Dict]) -> str:
        if not self.client:
            return "Error: Groq API Key missing."
            
        entity_str = ", ".join([f"{e['text']} ({e['label']})" for e in entities])
        
        prompt = f"""
        You are a warm, highly empathetic medical scribe. Your goal is to write a supportive 'Personalized Care Plan' for a patient based on their consultation.
        
        CONSULTATION DATA:
        - Transcription: {transcript}
        - Key Details: {entity_str}
        
        INSTRUCTIONS FOR EMPATHETIC CLARITY:
        1. **Tone**: Be warm, reassuring, and use 'You'/ 'Your'. 
        2. **Language**: Use 5th-grade reading level. Avoid jargon (e.g., say 'high blood pressure' instead of 'hypertension', 'sugar levels' instead of 'glycemia').
        3. **Structure**: 
           - **Overview**: A friendly summary of what was discussed.
           - **Medicine Schedule**: Clear instructions for any pills or treatments.
           - **Your Next Steps**: Simple, actionable items for the patient.
        
        YOUR PERSONALIZED CARE PLAN:
        """
        
        completion = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a warm medical assistant. You provide clear, very simple, and empathetic care plans for patients, avoiding all complex medical jargon."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        
        return completion.choices[0].message.content

scribe_service = ScribeService()
