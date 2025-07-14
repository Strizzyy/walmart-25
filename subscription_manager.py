import json
import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
import calendar

class SubscriptionManager:
    def __init__(self, data_dir: str = "mock_data"):
        self.data_dir = data_dir
        self.subscriptions = self._load_json("subscriptions.json")
        self._migrate_subscriptions()  # Migrate old subscriptions on initialization
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON data from file"""
        file_path = os.path.join(self.data_dir, filename)
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found, creating empty file")
            data = {"subscriptions": []}
            self._save_json(filename, data)
            return data
    
    def _save_json(self, filename: str, data: Dict) -> None:
        """Save JSON data to file"""
        file_path = os.path.join(self.data_dir, filename)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _migrate_subscriptions(self):
        """Migrate subscriptions with 'delivery_day' to 'delivery_date'"""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        updated = False
        for sub in self.subscriptions["subscriptions"]:
            if "delivery_day" in sub and "delivery_date" not in sub:
                # Convert delivery_day to a date in July 2025 (arbitrarily choose the first occurrence)
                delivery_day = sub["delivery_day"]
                if delivery_day in days:
                    cal = calendar.monthcalendar(2025, 7)
                    target_day = days.index(delivery_day)
                    for week in cal:
                        if week[target_day] != 0:
                            sub["delivery_date"] = f"2025-07-{week[target_day]:02d}"
                            break
                    del sub["delivery_day"]
                    updated = True
        if updated:
            self._save_json("subscriptions.json", self.subscriptions)
    
    def create_subscription(self, customer_id: str, items: List[Dict], delivery_date: str, subscription_type: str) -> Dict:
        """Create a new subscription with a specific delivery date and type"""
        subscription_id = f"SUB{len(self.subscriptions['subscriptions']) + 1:03d}"
        subscription = {
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "items": items,
            "delivery_date": delivery_date,
            "subscription_type": subscription_type,
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
    
    def get_notification(self, subscription_id: str) -> Optional[Dict]:
        """Check if a notification is needed based on subscription type"""
        for sub in self.subscriptions["subscriptions"]:
            if sub["subscription_id"] == subscription_id and sub["status"] == "active":
                delivery_date = sub.get("delivery_date", sub.get("delivery_day", None))
                subscription_type = sub.get("subscription_type", "weekly")
                if delivery_date:
                    try:
                        next_delivery = datetime.strptime(delivery_date, "%Y-%m-%d").date()
                        current_date = datetime.now().date()
                        days_until = (next_delivery - current_date).days
                        items = ", ".join([item["name"] for item in sub["items"]])
                        if days_until == 1:
                            return {
                                "message": f"Reminder: Your planned order {subscription_id} will restock {items} tomorrow on {delivery_date} ({subscription_type}).",
                                "subscription_id": subscription_id,
                                "delivery_date": delivery_date
                            }
                        elif 2 <= days_until <= 3:
                            return {
                                "message": f"Reminder: Your planned order {subscription_id} will restock {items} on {delivery_date} ({subscription_type}).",
                                "subscription_id": subscription_id,
                                "delivery_date": delivery_date
                            }
                    except ValueError:
                        print(f"Invalid date format for subscription {subscription_id}")
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