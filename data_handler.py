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
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON data from file"""
        try:
            with open(os.path.join(self.data_dir, filename), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found")
            return {}
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer by ID"""
        customers_list = self.customers.get("customers", [])
        return next((c for c in customers_list if c["customer_id"] == customer_id), None)
    
    def get_customer_orders(self, customer_id: str) -> List[Dict]:
        """Get all orders for a customer"""
        orders_list = self.orders.get("orders", [])
        return [o for o in orders_list if o["customer_id"] == customer_id]
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        orders_list = self.orders.get("orders", [])
        return next((o for o in orders_list if o["order_id"] == order_id), None)
    
    def get_payment(self, payment_id: str) -> Optional[Dict]:
        """Get payment by ID"""
        payments_list = self.payments.get("payments", [])
        return next((p for p in payments_list if p["payment_id"] == payment_id), None)
    
    def get_customer_payments(self, customer_id: str) -> List[Dict]:
        """Get all payments for a customer"""
        payments_list = self.payments.get("payments", [])
        return [p for p in payments_list if p["customer_id"] == customer_id]
    
    def get_order_payment(self, order_id: str) -> Optional[Dict]:
        """Get payment for specific order"""
        payments_list = self.payments.get("payments", [])
        return next((p for p in payments_list if p["order_id"] == order_id), None)
    
    def update_wallet_balance(self, customer_id: str, new_balance: float) -> bool:
        """Update customer wallet balance"""
        customers_list = self.customers.get("customers", [])
        for customer in customers_list:
            if customer["customer_id"] == customer_id:
                customer["wallet_balance"] = new_balance
                return True
        return False
    
    def get_failed_payments(self, customer_id: str) -> List[Dict]:
        """Get failed payments for a customer"""
        payments_list = self.payments.get("payments", [])
        return [p for p in payments_list if p["customer_id"] == customer_id and p["status"] == "failed"]