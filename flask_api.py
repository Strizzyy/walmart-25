from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from nlu_pipeline import NLUPipeline
from datetime import datetime
from werkzeug.utils import secure_filename
import speech_recognition as sr
from io import BytesIO

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'mock_data', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize NLU Pipeline
GROQ_API_KEY = "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"  # Replace with your actual API key
nlu = NLUPipeline(GROQ_API_KEY)

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
        
        return jsonify({
            'customer': customer,
            'orders': orders,
            'payments': payments,
            'summary': {
                'total_orders': len(orders),
                'total_payments': len(payments),
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
    
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)

    # Use the absolute upload dir
    file.save(os.path.join(UPLOAD_DIR, filename))

    return jsonify({'message': f"File '{filename}' uploaded successfully."})


@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio part in request'}), 400
    audio_file = request.files['audio']
    recognizer = sr.Recognizer()
    audio_data = sr.AudioFile(BytesIO(audio_file.read()))
    with audio_data as source:
        audio = recognizer.record(source)
    text = recognizer.recognize_google(audio)
    return jsonify({'text': text})

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
                'GENERAL_INQUIRY': 7
            },
            'customer_satisfaction': 4.3,
            'top_issues': [
                'Wallet balance discrepancy',
                'Delivery delays',
                'Payment failures',
                'Order tracking'
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
    print("- GET /analytics - Get analytics data")
    
    app.run(debug=True, host='0.0.0.0', port=5000)