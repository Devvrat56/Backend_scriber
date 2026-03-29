import os
import uuid
from typing import List, Dict, Optional
from groq import Groq
from core.config import settings

class ChatService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
            
        # Fake hospital contact details (for demo/safety)
        self.FAKE_EMERGENCY_NUMBER = "+91-214-352-354-235"
        self.FAKE_APPOINTMENT_EMAIL = "dvvratshuk@softsensor.ai"

    def get_patient_system_prompt(self, cancer_type: str, cancer_stage: str) -> str:
        base = """
You are a warm, empathetic Oncology Information Assistant. Your goal is to provide supportive, clear, and patient-friendly information about cancer care.
- Never give medical advice, dosages, or specific treatment plans.
- Always encourage the user to speak with their oncology team.
- Use simple language and be highly supportive.
"""
        extra = f"""
<IMPORTANT>
Patient Context:
- Cancer type: {cancer_type}
- Stage: {cancer_stage}
Always relate answers to this context.
Keep responses short, warm, and supportive.
</IMPORTANT>
"""
        return base + "\n\n" + extra

    def get_doctor_system_prompt(self) -> str:
        return """
You are a professional Medical Assistant for Oncologists. Your goal is to provide concise, evidence-based clinical information, summarize reports, and assist with patient data retrieval.
- Use professional medical terminology.
- Be precise and efficient.
"""

    def handle_message(self, 
                       message: str, 
                       history: List[Dict], 
                       user_type: str = "patient", 
                       cancer_type: str = "Not specified", 
                       cancer_stage: str = "Unknown") -> Dict:
        
        # ── Guardrails ──
        contact_keywords = ["appointment", "book", "schedule", "contact", "call", "emergency", "urgent"]
        if any(kw in message.lower() for kw in contact_keywords):
            return {
                "answer": (
                    "I understand you would like to book an appointment or contact the hospital. "
                    "I cannot make bookings directly, but you can reach out here:\n\n"
                    f"• **Emergency**: {self.FAKE_EMERGENCY_NUMBER}\n"
                    f"• **Appointments**: {self.FAKE_APPOINTMENT_EMAIL}"
                ),
                "guarded": True
            }

        dangerous = ["dose", "dosage", "how much", "treatment plan", "prescribe"]
        if any(w in message.lower() for w in dangerous):
            return {
                "answer": "I am not permitted to provide dosages or specific treatment recommendations. Please discuss this with your oncologist.",
                "guarded": True
            }

        # ── LLM Flow ──
        if not self.client:
            return {"answer": "AI service currently unavailable.", "error": True}

        # Prepare messages
        if not history or history[0].get("role") != "system":
            system_prompt = self.get_doctor_system_prompt() if user_type == "doctor" else self.get_patient_system_prompt(cancer_type, cancer_stage)
            history.insert(0, {"role": "system", "content": system_prompt})

        history.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=history,
                temperature=0.45,
                max_tokens=512,
            )
            answer = response.choices[0].message.content.strip()
            return {"answer": answer, "guarded": False}
        except Exception as e:
            return {"answer": f"Error: {str(e)}", "error": True}

chat_service = ChatService()
