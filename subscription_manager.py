import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SubscriptionManager:
    def __init__(self, data_dir: str = "mock_data"):
        self.data_dir = data_dir
        self.subscriptions = self._load_json("subscriptions.json")
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON data from file"""
        file_path = os.path.join(self.data_dir, filename)
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found, creating empty file")
            return {"subscriptions": []}
    
    def _save_json(self, filename: str, data: Dict) -> None:
        """Save JSON data to file"""
        file_path = os.path.join(self.data_dir, filename)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_subscription(self, customer_id: str, items: List[Dict], delivery_day: str, frequency: str = "weekly") -> Dict:
        """Create a new subscription"""
        subscription_id = f"SUB{len(self.subscriptions['subscriptions']) + 1:03d}"
        subscription = {
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "items": items,
            "delivery_day": delivery_day,
            "frequency": frequency,
            "next_delivery": self._calculate_next_delivery(delivery_day),
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        self.subscriptions["subscriptions"].append(subscription)
        self._save_json("subscriptions.json", self.subscriptions)
        return subscription
    
    def get_customer_subscriptions(self, customer_id: str) -> List[Dict]:
        """Get all subscriptions for a customer"""
        return [s for s in self.subscriptions["subscriptions"] if s["customer_id"] == customer_id]
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        for sub in self.subscriptions["subscriptions"]:
            if sub["subscription_id"] == subscription_id:
                sub["status"] = "cancelled"
                self._save_json("subscriptions.json", self.subscriptions)
                return True
        return False
    
    def _calculate_next_delivery(self, delivery_day: str) -> str:
        """Calculate the next delivery date based on the delivery day"""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        current_date = datetime.now()
        target_day = days.index(delivery_day)
        current_day = current_date.weekday()
        days_until = (target_day - current_day + 7) % 7
        if days_until == 0:
            days_until = 7  # If today is the delivery day, schedule for next week
        next_delivery = current_date + timedelta(days=days_until)
        return next_delivery.strftime("%Y-%m-%d")
    
    def get_notification(self, subscription_id: str) -> Optional[Dict]:
        """Check if a notification is needed (1-2 days before delivery)"""
        for sub in self.subscriptions["subscriptions"]:
            if sub["subscription_id"] == subscription_id and sub["status"] == "active":
                next_delivery = datetime.strptime(sub["next_delivery"], "%Y-%m-%d")
                days_until = (next_delivery - datetime.now()).days
                if days_until < 1:
                    items = ", ".join([item["name"] for item in sub["items"]])
                    return {
                        "message": f"Reminder: Your planned order {subscription_id} will restock {items} on {sub['next_delivery']} i.e tomorrow.",
                        "subscription_id": subscription_id,
                        "delivery_date": sub["next_delivery"]
     }
        return None