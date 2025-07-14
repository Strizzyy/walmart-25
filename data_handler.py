import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class DataHandler:
    def __init__(self, data_dir: str = "mock_data"):
        self.data_dir = data_dir
        self.customers = self._load_json("customers.json")
        self.orders = self._load_json("orders.json")
        self.payments = self._load_json("payments.json")
        self.subscriptions = self._load_json("subscriptions.json")
        self.escalations = self._load_json("escalations.json")
    
    def _load_json(self, filename: str) -> Dict:
        try:
            with open(os.path.join(self.data_dir, filename), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found")
            return {"subscriptions": []} if filename == "subscriptions.json" else {"escalations": {}} if filename == "escalations.json" else {}
    
    def _save_json(self, filename: str, data: Dict) -> None:
        with open(os.path.join(self.data_dir, filename), 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        customers_list = self.customers.get("customers", [])
        return next((c for c in customers_list if c["customer_id"] == customer_id), None)
    
    def get_customer_orders(self, customer_id: str) -> List[Dict]:
        orders_list = self.orders.get("orders", [])
        return [o for o in orders_list if o["customer_id"] == customer_id]
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        orders_list = self.orders.get("orders", [])
        return next((o for o in orders_list if o["order_id"] == order_id), None)
    
    def get_payment(self, payment_id: str) -> Optional[Dict]:
        payments_list = self.payments.get("payments", [])
        return next((p for p in payments_list if p["payment_id"] == payment_id), None)
    
    def get_customer_payments(self, customer_id: str) -> List[Dict]:
        payments_list = self.payments.get("payments", [])
        return [p for p in payments_list if p["customer_id"] == customer_id]
    
    def get_order_payment(self, order_id: str) -> Optional[Dict]:
        payments_list = self.payments.get("payments", [])
        return next((p for p in payments_list if p["order_id"] == order_id), None)
    
    def update_wallet_balance(self, customer_id: str, new_balance: float) -> bool:
        customers_list = self.customers.get("customers", [])
        for customer in customers_list:
            if customer["customer_id"] == customer_id:
                customer["wallet_balance"] = new_balance
                self._save_json("customers.json", self.customers)
                return True
        return False
    
    def get_failed_payments(self, customer_id: str) -> List[Dict]:
        payments_list = self.payments.get("payments", [])
        return [p for p in payments_list if p["customer_id"] == customer_id and p["status"] == "failed"]
    
    def get_customer_subscriptions(self, customer_id: str) -> List[Dict]:
        subscriptions_list = self.subscriptions.get("subscriptions", [])
        return [s for s in subscriptions_list if s["customer_id"] == customer_id]
    
    def add_escalation(self, case_id: str, customer_id: str, issue_details: str) -> bool:
        self.escalations.setdefault("escalations", {})[case_id] = {
            "customer_id": customer_id,
            "issue_details": issue_details,
            "status": "pending",
            "escalation_time": datetime.now().isoformat()
        }
        self._save_json("escalations.json", self.escalations)
        return True
    
    def get_escalation(self, case_id: str) -> Optional[Dict]:
        return self.escalations.get("escalations", {}).get(case_id)
    
    def update_escalation_status(self, case_id: str, status: str) -> bool:
        if case_id in self.escalations.get("escalations", {}):
            self.escalations["escalations"][case_id]["status"] = status
            self._save_json("escalations.json", self.escalations)
            return True
        return False