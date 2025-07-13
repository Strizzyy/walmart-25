import groq
import re
from typing import Dict, Tuple
from data_handler import DataHandler

class NLUPipeline:
    def __init__(self, groq_api_key: str):
        self.client = groq.Groq(api_key=groq_api_key)
        self.data_handler = DataHandler()
        
        # Intent keywords for quick classification
        self.intent_keywords = {
            'REFUND_REQUEST': ['refund', 'money back', 'return', 'cancel order', 'get my money'],
            'DELIVERY_ISSUE': ['not delivered', 'missing', 'delay', 'late', 'not received', 'where is'],
            'PAYMENT_PROBLEM': ['charged twice', 'payment failed', 'double charge', 'not charged', 'billing'],
            'WALLET_ISSUE': ['wallet', 'balance', 'credited', 'deducted', 'shows 0', 'wallet empty'],
            'ORDER_STATUS': ['order status', 'tracking', 'shipped', 'when will', 'delivery date'],
            'GENERAL_INQUIRY': ['help', 'support', 'question', 'how to', 'what is']
        }
    
    def extract_order_id(self, message: str) -> str:
        """Extract order ID from message"""
        order_pattern = r'ORD\d{3}'
        match = re.search(order_pattern, message)
        return match.group() if match else None
    
    def extract_amount(self, message: str) -> float:
        """Extract amount from message"""
        amount_pattern = r'₹(\d+(?:\.\d{2})?)'
        match = re.search(amount_pattern, message)
        return float(match.group(1)) if match else None
    
    def classify_intent_quick(self, message: str) -> str:
        """Quick intent classification using keywords"""
        message_lower = message.lower()
        scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                scores[intent] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'GENERAL_INQUIRY'
    
    def classify_intent_groq(self, message: str) -> str:
        """Fallback intent classification using Groq"""
        prompt = f"""
        Classify this customer support message into ONE of these intents:
        REFUND_REQUEST, DELIVERY_ISSUE, PAYMENT_PROBLEM, WALLET_ISSUE, ORDER_STATUS, GENERAL_INQUIRY
        
        Message: "{message}"
        
        Return only the intent name, nothing else.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API error: {e}")
            return self.classify_intent_quick(message)
    
    def classify_intent(self, message: str) -> str:
        """Main intent classification method"""
        # Try quick classification first
        intent = self.classify_intent_quick(message)
        
        # If general inquiry, use Groq for better classification
        if intent == 'GENERAL_INQUIRY':
            intent = self.classify_intent_groq(message)
        
        return intent
    
    def generate_response(self, intent: str, message: str, customer_id: str) -> str:
        """Generate contextual response based on intent and customer data"""
        customer = self.data_handler.get_customer(customer_id)
        if not customer:
            return "I'm sorry, I couldn't find your customer information. Please contact support."
        
        # Extract relevant information
        order_id = self.extract_order_id(message)
        amount = self.extract_amount(message)
        
        # Get customer context
        customer_orders = self.data_handler.get_customer_orders(customer_id)
        customer_payments = self.data_handler.get_customer_payments(customer_id)
        
        # Build context for Groq
        context = f"""
        You are a helpful Walmart customer support agent. Respond professionally and helpfully.
        
        Customer Information:
        - Name: {customer['name']}
        - Wallet Balance: ₹{customer['wallet_balance']}
        - Membership: {customer['membership']}
        - Location: {customer['location']}
        
        Recent Orders: {len(customer_orders)} orders
        Intent: {intent}
        Customer Message: "{message}"
        
        Based on the intent, provide a helpful response:
        """
        
        if intent == 'WALLET_ISSUE':
            context += f"""
            Recent payments: {len(customer_payments)} transactions
            Current wallet balance: ₹{customer['wallet_balance']}
            
            If wallet shows ₹0 but customer paid, explain payment processing and offer to credit wallet.
            """
        
        elif intent == 'DELIVERY_ISSUE':
            if order_id:
                order = self.data_handler.get_order(order_id)
                if order:
                    context += f"""
                    Order {order_id} details:
                    - Status: {order['status']}
                    - Expected delivery: {order['expected_delivery']}
                    - Items: {len(order['items'])} items
                    """
        
        elif intent == 'PAYMENT_PROBLEM':
            failed_payments = self.data_handler.get_failed_payments(customer_id)
            context += f"""
            Failed payments: {len(failed_payments)}
            Recent payment issues found.
            """
        
        context += "\n\nProvide a concise, helpful response (max 100 words)."
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": context}],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Response generation error: {e}")
            return self._fallback_response(intent, customer, order_id)
    
    def _fallback_response(self, intent: str, customer: Dict, order_id: str = None) -> str:
        """Fallback responses when API fails"""
        responses = {
            'WALLET_ISSUE': f"Hi {customer['name']}! I can see your current wallet balance is ₹{customer['wallet_balance']}. Let me help you resolve this payment issue.",
            'DELIVERY_ISSUE': f"Hi {customer['name']}! I'm checking your delivery status right now. Let me get you an update.",
            'PAYMENT_PROBLEM': f"Hi {customer['name']}! I can help you with your payment concerns. Let me review your recent transactions.",
            'ORDER_STATUS': f"Hi {customer['name']}! I'll check your order status for you right away.",
            'REFUND_REQUEST': f"Hi {customer['name']}! I can help you with your refund request. Let me process this for you.",
            'GENERAL_INQUIRY': f"Hi {customer['name']}! I'm here to help. How can I assist you today?"
        }
        return responses.get(intent, "I'm here to help you with your query!")