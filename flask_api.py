from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from nlu_pipeline import NLUPipeline
from subscription_manager import SubscriptionManager
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
load_dotenv()

# Initialize NLU Pipeline and Subscription Manager
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Replace with your actual API key
nlu = NLUPipeline(GROQ_API_KEY)
subscription_manager = SubscriptionManager()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/customers', methods=['GET'])
def get_customers():
    """Get all customers for demo selection"""
    try:
        customers = nlu.data_handler.customers.get('customers', [])
        return jsonify({
            'customers': [
                {
                    'customer_id': c['customer_id'],
                    'name': c['name'],
                    'membership': c['membership'],
                    'location': c['location']
                }
                for c in customers
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/customer/<customer_id>', methods=['GET'])
def get_customer_info(customer_id):
    """Get detailed customer information"""
    try:
        customer = nlu.data_handler.get_customer(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        orders = nlu.data_handler.get_customer_orders(customer_id)
        payments = nlu.data_handler.get_customer_payments(customer_id)
        subscriptions = nlu.data_handler.get_customer_subscriptions(customer_id)
        
        return jsonify({
            'customer': customer,
            'orders': orders,
            'payments': payments,
            'subscriptions': subscriptions,
            'summary': {
                'total_orders': len(orders),
                'total_payments': len(payments),
                'total_subscriptions': len(subscriptions),
                'wallet_balance': customer['wallet_balance']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        message = data.get('message', '')
        customer_id = data.get('customer_id', 'WM001')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Classify intent
        intent = nlu.classify_intent(message)
        
        # Generate response
        response = nlu.generate_response(intent, message, customer_id)
        
        # Log the conversation (in production, store in database)
        print(f"[{datetime.now()}] Customer: {customer_id}, Intent: {intent}, Message: {message}")
        
        return jsonify({
            'response': response,
            'intent': intent,
            'customer_id': customer_id,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'error': 'I apologize, but I encountered an error. Please try again.',
            'details': str(e)
        }), 500

@app.route('/subscription', methods=['POST'])
def create_subscription():
    """Create a new subscription"""
    try:
        data = request.json
        customer_id = data.get('customer_id')
        items = data.get('items')
        delivery_day = data.get('delivery_day')
        
        if not all([customer_id, items, delivery_day]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        subscription = subscription_manager.create_subscription(customer_id, items, delivery_day)
        if subscription:
            return jsonify({
                'message': f'Subscription {subscription["subscription_id"]} created successfully',
                'subscription': subscription
            }), 201
        else:
            return jsonify({'error': 'Failed to create subscription'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/subscriptions/<customer_id>', methods=['GET'])
def get_subscriptions(customer_id):
    """Get all subscriptions for a customer"""
    try:
        subscriptions = subscription_manager.get_customer_subscriptions(customer_id)
        return jsonify({'subscriptions': subscriptions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/subscription/cancel/<subscription_id>', methods=['POST'])
def cancel_subscription(subscription_id):
    """Cancel a subscription"""
    try:
        if subscription_manager.cancel_subscription(subscription_id):
            return jsonify({'message': f'Subscription {subscription_id} cancelled'})
        return jsonify({'error': 'Subscription not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/subscription/notifications/<customer_id>', methods=['GET'])
def get_subscription_notifications(customer_id):
    """Get subscription notifications for a customer"""
    try:
        subscriptions = subscription_manager.get_customer_subscriptions(customer_id)
        notifications = []
        for sub in subscriptions:
            notification = subscription_manager.get_notification(sub['subscription_id'])
            if notification:
                notifications.append(notification)
        return jsonify({'notifications': notifications})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Get basic analytics for admin dashboard"""
    try:
        # Mock analytics data
        analytics = {
            'total_interactions': 127,
            'resolution_rate': 89.5,
            'avg_response_time': 1.2,
            'intent_distribution': {
                'WALLET_ISSUE': 35,
                'DELIVERY_ISSUE': 28,
                'PAYMENT_PROBLEM': 22,
                'ORDER_STATUS': 20,
                'REFUND_REQUEST': 15,
                'SUBSCRIPTION_REQUEST': 10,
                'GENERAL_INQUIRY': 7
            },
            'customer_satisfaction': 4.3,
            'top_issues': [
                'Wallet balance discrepancy',
                'Delivery delays',
                'Payment failures',
                'Order tracking',
                'Subscription setup'
            ]
        }
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create mock_data directory if it doesn't exist
    if not os.path.exists('mock_data'):
        os.makedirs('mock_data')
    
    print("Starting Walmart AI Support API...")
    print("Available endpoints:")
    print("- GET /health - Health check")
    print("- GET /customers - Get all customers")
    print("- GET /customer/<id> - Get customer details")
    print("- POST /chat - Chat with AI assistant")
    print("- POST /subscription - Create a subscription")
    print("- GET /subscriptions/<customer_id> - Get customer subscriptions")
    print("- POST /subscription/cancel/<subscription_id> - Cancel a subscription")
    print("- GET /subscription/notifications/<customer_id> - Get subscription notifications")
    print("- GET /analytics - Get analytics data")
    
    app.run(debug=True, host='0.0.0.0', port=5000)