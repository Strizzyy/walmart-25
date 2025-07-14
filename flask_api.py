from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from nlu_pipeline import NLUPipeline
from subscription_manager import SubscriptionManager
from datetime import datetime
from dotenv import load_dotenv
from resolution_engine import ResolutionEngine
from validation_service import ValidationService
from data_handler import DataHandler

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("flask_api.log"), logging.StreamHandler()]
)

app = Flask(__name__)
CORS(app)
load_dotenv()

# Initialize components
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Replace with your actual API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Add Gemini API key to .env
data_handler = DataHandler()
nlu = NLUPipeline(GROQ_API_KEY)
subscription_manager = SubscriptionManager()
resolution_engine = ResolutionEngine(data_handler)
validation_service = ValidationService(GEMINI_API_KEY)

@app.route('/health', methods=['GET'])
def health_check():
    logging.info("Health check endpoint called.")
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/customers', methods=['GET'])
def get_customers():
    try:
        logging.info("Fetching customers via API endpoint.")
        customers = nlu.data_handler.customers.get('customers', [])
        logging.info(f"Fetched {len(customers)} customers.")
        return jsonify({
            'customers': [
                {'customer_id': c['customer_id'], 'name': c['name'], 'membership': c['membership'], 'location': c['location']}
                for c in customers
            ]
        })
    except Exception as e:
        logging.error(f"Error in get_customers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/customer/<customer_id>', methods=['GET'])
def get_customer_info(customer_id):
    try:
        logging.info(f"Fetching info for customer {customer_id}.")
        customer = data_handler.get_customer(customer_id)
        if not customer:
            logging.warning(f"Customer {customer_id} not found.")
            return jsonify({'error': 'Customer not found'}), 404
        orders = data_handler.get_customer_orders(customer_id)
        payments = data_handler.get_customer_payments(customer_id)
        subscriptions = data_handler.get_customer_subscriptions(customer_id)
        logging.info(f"Customer {customer_id}: {len(orders)} orders, {len(payments)} payments, {len(subscriptions)} subscriptions.")
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
        logging.error(f"Error in get_customer_info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        customer_id = data.get('customer_id', 'WM001')
        if not message:
            logging.warning("Chat endpoint called without message.")
            return jsonify({'error': 'Message is required'}), 400
        
        intent = nlu.classify_intent(message)
        response = nlu.generate_response(intent, message, customer_id)
        
        # Trigger resolution if applicable
        if intent in ['PAYMENT_PROBLEM', 'WALLET_ISSUE', 'REFUND_REQUEST']:
            case_id = resolution_engine.process_intent(intent, message, customer_id)
            if case_id:
                response += f" Case ID: {case_id}. Check status later."
        
        logging.info(f"Chat: Customer {customer_id}, Intent: {intent}, Message: {message}")
        return jsonify({
            'response': response,
            'intent': intent,
            'customer_id': customer_id,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return jsonify({
            'error': 'I apologize, but I encountered an error. Please try again.',
            'details': str(e)
        }), 500

@app.route('/subscription', methods=['POST'])
def create_subscription():
    try:
        data = request.json
        customer_id = data.get('customer_id')
        items = data.get('items')
        delivery_date = data.get('delivery_date')
        subscription_type = data.get('subscription_type', 'weekly')  # Default to weekly if not provided
        
        if not all([customer_id, items, delivery_date]):
            logging.warning("Create subscription called with missing fields.")
            return jsonify({'error': 'Missing required fields'}), 400
        subscription = subscription_manager.create_subscription(customer_id, items, delivery_date, subscription_type)
        if subscription:
            logging.info(f"Subscription {subscription['subscription_id']} created for customer {customer_id}.")
            return jsonify({
                'message': f'Subscription {subscription["subscription_id"]} created successfully',
                'subscription': subscription
            }), 201
        logging.error("Failed to create subscription.")
        return jsonify({'error': 'Failed to create subscription'}), 500
    except Exception as e:
        logging.error(f"Error in create_subscription: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/subscriptions/<customer_id>', methods=['GET'])
def get_subscriptions(customer_id):
    try:
        logging.info(f"Fetching subscriptions for customer {customer_id}.")
        subscriptions = subscription_manager.get_customer_subscriptions(customer_id)
        logging.info(f"Found {len(subscriptions)} subscriptions for customer {customer_id}.")
        return jsonify({'subscriptions': subscriptions})
    except Exception as e:
        logging.error(f"Error in get_subscriptions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/subscription/cancel/<subscription_id>', methods=['POST'])
def cancel_subscription(subscription_id):
    try:
        logging.info(f"Attempting to cancel subscription {subscription_id}.")
        if subscription_manager.cancel_subscription(subscription_id):
            logging.info(f"Subscription {subscription_id} cancelled.")
            return jsonify({'message': f'Subscription {subscription_id} cancelled'})
        logging.warning(f"Subscription {subscription_id} not found for cancellation.")
        return jsonify({'error': 'Subscription not found'}), 404
    except Exception as e:
        logging.error(f"Error in cancel_subscription: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/subscription/notifications/<customer_id>', methods=['GET'])
def get_subscription_notifications(customer_id):
    try:
        logging.info(f"Fetching notifications for customer {customer_id}.")
        subscriptions = subscription_manager.get_customer_subscriptions(customer_id)
        notifications = []
        for sub in subscriptions:
            notification = subscription_manager.get_notification(sub['subscription_id'])
            if notification:
                notifications.append(notification)
        logging.info(f"Found {len(notifications)} notifications for customer {customer_id}.")
        return jsonify({'notifications': notifications})
    except Exception as e:
        logging.error(f"Error in get_subscription_notifications: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analytics', methods=['GET'])
def get_analytics():
    try:
        logging.info("Fetching analytics data.")
        analytics = {
            'total_interactions': 127,
            'resolution_rate': 89.5,
            'avg_response_time': 1.2,
            'intent_distribution': {
                'WALLET_ISSUE': 35, 'DELIVERY_ISSUE': 28, 'PAYMENT_PROBLEM': 22, 'ORDER_STATUS': 20,
                'REFUND_REQUEST': 15, 'SUBSCRIPTION_REQUEST': 10, 'GENERAL_INQUIRY': 7
            },
            'customer_satisfaction': 4.3,
            'top_issues': [
                'Wallet balance discrepancy', 'Delivery delays', 'Payment failures', 'Order tracking', 'Subscription setup'
            ]
        }
        logging.info("Analytics data sent.")
        return jsonify(analytics)
    except Exception as e:
        logging.error(f"Error in get_analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/validate', methods=['POST'])
def validate_request():
    try:
        if 'file' not in request.files:
            logging.warning("Validate request called without file upload.")
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        message = request.form.get('message', '')
        customer_id = request.form.get('customer_id', 'WM001')
        
        logging.info(f"Processing validation request for customer {customer_id} with file {file.filename}")
        
        # Get validation result from service
        validation_result = validation_service.validate_request(file, message, customer_id)
        
        # Generate reference ID
        ref_id = f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Prepare response
        response_data = {
            'status': validation_result.get('status'),
            'message': 'Your refund request has been automatically approved based on the evidence provided.' if validation_result.get('status') == 'approved' else 'Your request requires additional review and has been escalated to our customer service team.',
            'category': 'Refund Request',
            'priority': 'Standard' if validation_result.get('status') == 'approved' else 'High',
            'reference_id': ref_id,
            'validation_details': validation_result
        }
        
        return jsonify(response_data)
    except Exception as e:
        logging.error(f"Error in validate_request: {e}")
        return jsonify({
            'status': 'escalated',
            'message': 'We encountered an issue processing your request. A customer service agent will review it shortly.',
            'category': 'Refund Request',
            'priority': 'High',
            'reference_id': f"REF-ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }), 500

if __name__ == '__main__':
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
    print("- POST /validate - Validate request with file")
    app.run(debug=True, host='0.0.0.0', port=5000)