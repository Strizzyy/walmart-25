import uuid
from datetime import datetime
from data_handler import DataHandler
from typing import Dict, Optional

class ResolutionEngine:
    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler
    
    def process_intent(self, intent: str, message: str, customer_id: str) -> str:
        case_id = str(uuid.uuid4())
        if intent == 'PAYMENT_PROBLEM':
            if self._resolve_payment_issue(customer_id, message):
                return case_id
        elif intent == 'WALLET_ISSUE':
            if self._resolve_wallet_issue(customer_id):
                return case_id
        elif intent == 'REFUND_REQUEST':
            return self._handle_refund_request(case_id, customer_id, message)
        return case_id  # Escalation by default for unhandled cases
    
    def _resolve_payment_issue(self, customer_id: str, message: str) -> bool:
        failed_payments = self.data_handler.get_failed_payments(customer_id)
        if failed_payments:
            for payment in failed_payments:
                payment['status'] = 'processed'
            self.data_handler._save_json("payments.json", self.data_handler.payments)
            return True
        return False
    
    def _resolve_wallet_issue(self, customer_id: str) -> bool:
        customer = self.data_handler.get_customer(customer_id)
        if customer and customer['wallet_balance'] == 0:
            customer['wallet_balance'] = 100.0  # Mock credit
            self.data_handler._save_json("customers.json", self.data_handler.customers)
            return True
        return False
    
    def _handle_refund_request(self, case_id: str, customer_id: str, message: str) -> str:
        self.data_handler.add_escalation(case_id, customer_id, message)
        return case_id  # Escalation required until validation
    
    def escalate_case(self, case_id: str, details: Dict) -> Dict:
        self.data_handler.add_escalation(case_id, details.get('customer_id'), details.get('issue_details'))
        return {'status': 'escalated', 'case_id': case_id}
    
    def resolve_escalated(self, case_id: str, decision: str) -> Dict:
        if decision == 'approve':
            customer_id = self.data_handler.get_escalation(case_id)['customer_id']
            customer = self.data_handler.get_customer(customer_id)
            customer['wallet_balance'] += 50.0  # Mock refund
            self.data_handler._save_json("customers.json", self.data_handler.customers)
            self.data_handler.update_escalation_status(case_id, 'resolved')
            return {'status': 'resolved', 'case_id': case_id}
        self.data_handler.update_escalation_status(case_id, 'rejected')
        return {'status': 'rejected', 'case_id': case_id}