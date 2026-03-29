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
        return f"""
        You are an AI oncology assistant designed to support cancer patients with accurate, safe, and empathetic information.

        ROLE:
        - You provide educational and guidance-based responses related to oncology.
        - You DO NOT provide medical diagnosis, prescriptions, or final treatment decisions.
        - You always encourage consultation with a qualified oncologist.

        BEHAVIOR RULES:
        1. Safety First: If the user describes severe symptoms (bleeding, breathlessness, severe pain), immediately move to EMERGENCY OVERRIDE.
        2. Accuracy: Only provide general, evidence-based oncology knowledge. If uncertain, say "I'm not fully certain" instead of guessing.
        3. Clarity: Explain medical terms in simple language (5th-grade level).
        4. Empathy: Maintain a calm, supportive, and non-alarming tone. Acknowledge emotional distress if present.
        5. Boundaries: Do not replace a doctor. Avoid making predictions about survival or outcomes.

        INTERNAL REASONING (DO NOT EXPOSE):
        - First, analyze the intent and classify Risk Level:
          * HIGH: Emergency symptoms (severe bleeding, breathing trouble, unconsciousness).
          * MEDIUM: Treatment confusion, medication concerns, new symptoms.
          * LOW: General information, definitions, navigation.
        - If HIGH RISK -> Prioritize EMERGENCY OVERRIDE: 
          "This may require immediate medical attention. Please contact your nearest emergency service or your oncologist right away."

        RESPONSE FORMAT (STRICT ENFORCEMENT):
        Every response MUST use these exact headings:
        ### Understanding:
        (Briefly restate the user's concern with empathy)
        ### Explanation:
        (Explain the medical concept in simple terms)
        ### Guidance:
        (Provide general next steps, non-prescriptive)
        ### Safety Note:
        (Mention when specifically to seek medical attention)
        ### Optional Follow-up:
        (Ask a helpful question to continue support)

        PATIENT CONTEXT:
        - Case: {cancer_type} | Stage: {cancer_stage}
        """

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
                       cancer_stage: str = "Unknown",
                       age: Optional[int] = None,
                       symptoms: Optional[str] = None) -> Dict:
        
        # ── LLM Flow ──
        if not self.client:
            return {"answer": "AI service currently unavailable.", "error": True}

        # Prepare messages
        if not history or history[0].get("role") != "system":
            system_prompt = self.get_doctor_system_prompt() if user_type == "doctor" else self.get_patient_system_prompt(cancer_type, cancer_stage)
            history.insert(0, {"role": "system", "content": system_prompt})

        # Dynamic User Prompt Template
        dynamic_user_prompt = f"""
        Patient Query: {message}

        Patient Context (if available):
        - Age: {age or "Not specified"}
        - Symptoms: {symptoms or "None reported"}
        - Type/Stage: {cancer_type} / {cancer_stage}
        
        CRITICAL INSTRUCTIONS:
        1. Classify Risk Level silently.
        2. IF HIGH RISK (Emergency): You must respond ONLY with this exact string and NOTHING ELSE (no headings, no extra advice):
           "This may require immediate medical attention. Please contact your nearest emergency service or your oncologist right away."
        3. IF NOT EMERGENCY: Follow the 5-point structure strictly. Ensure the "### Understanding:" heading is the very first thing you write.
        4. Detect emotional distress and use empathetic phrases.
        """
        
        history.append({"role": "user", "content": dynamic_user_prompt})

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=history,
                temperature=0.2, # Lower temperature for stricter format compliance
                max_tokens=600,
            )
            answer = response.choices[0].message.content.strip()
            
            # Final Guardrail: If AI identifies high risk but failed to use the exact string alone, 
            # we force the string to ensure patient safety.
            is_urgent = any(kw in message.lower() for kw in ["chest pain", "bleeding heavily", "unconscious", "cannot breathe"])
            if is_urgent and "immediate medical attention" in answer.lower():
                answer = "This may require immediate medical attention. Please contact your nearest emergency service or your oncologist right away."
                return {"answer": answer, "guarded": True}

            is_guarded = "immediate medical attention" in answer.lower()
            return {"answer": answer, "guarded": is_guarded}
        except Exception as e:
            return {"answer": f"Error: {str(e)}", "error": True}
        except Exception as e:
            return {"answer": f"Error: {str(e)}", "error": True}

    def summarize_conversation(self, history: List[Dict]) -> str:
        if not self.client:
            return "Summary unavailable."
            
        # Filter out system messages and focus on the exchange
        clean_history = [m for m in history if m.get("role") != "system"]
        if not clean_history:
            return "No conversation to summarize."

        history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in clean_history])
        
        prompt = f"""
        Summarize the following medical consultation chat into a single, supportive, and clear sentence for a patient's history log.
        Tone: Warm and helpful. 
        Length: Max 150 characters.
        
        CHAT LOG:
        {history_text}
        
        SUMMARY:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Chat summary failed: {e}")
            return "Conversation recorded."

chat_service = ChatService()
