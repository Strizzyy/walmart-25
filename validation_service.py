import google.generativeai as genai
from flask import request
from typing import Dict, Optional
import io
from PIL import Image
import uuid

class ValidationService:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def validate_request(self, file, message: str, customer_id: str) -> Dict:
        try:
            img = Image.open(io.BytesIO(file.read()))
            # Enhanced prompt to detect significant damage and enforce stricter rules
            prompt = f"""
            Analyze this image for damage related to a refund or replacement request. The message is: {message}.
            Look for significant damage such as large tears, dents, or structural collapse. 
            - Return 'valid' only if there is NO significant damage (e.g., minor scratches or intact packaging).
            - Return 'invalid' if the image shows no damage at all.
            - Return 'uncertain' if there is significant damage (e.g., tears, dents) or if the damage is unclear.
            Provide a concise response: 'valid', 'invalid', or 'uncertain'.
            """
            response = self.model.generate_content([prompt, img])
            result = response.text.strip().lower()

            if result == 'valid':
                return {
                    'status': 'approved',
                    'message': 'No significant damage detected. Refund or replacement processed autonomously.'
                }
            elif result == 'invalid':
                return {
                    'status': 'rejected',
                    'message': 'No valid damage detected. Request denied.'
                }
            else:  # 'uncertain' or any other response
                return {
                    'status': 'escalated',
                    'case_id': str(uuid.uuid4()),
                    'message': 'Significant damage or unclear evidence detected. Case escalated for human review.'
                }
        except Exception as e:
            return {
                'status': 'escalated',
                'case_id': str(uuid.uuid4()),
                'message': f'Error processing request: {str(e)}. Escalated for review.'
            }