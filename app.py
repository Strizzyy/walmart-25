# app.py (Streamlit Frontend)
import streamlit as st
import requests
import json
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Walmart AI Support",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0071ce, #004c91);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .customer-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0071ce;
    }
    
    .chat-container {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .scenario-button {
        background: #0071ce;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.25rem;
        cursor: pointer;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# API Base URL
API_BASE_URL = "http://localhost:5000"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_customer" not in st.session_state:
    st.session_state.selected_customer = None
if "customer_data" not in st.session_state:
    st.session_state.customer_data = None

# Helper functions
def get_customers():
    """Fetch customers from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/customers", timeout=5)
        if response.status_code == 200:
            customers = response.json().get('customers', [])
            if not customers:
                st.warning("No customers found in the database.")
            return customers
        else:
            st.error(f"Failed to fetch customers: HTTP {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}. Is the Flask server running on {API_BASE_URL}?")
        return []

def get_customer_info(customer_id):
    """Fetch customer information"""
    try:
        response = requests.get(f"{API_BASE_URL}/customer/{customer_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch customer info: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return None

def send_message(message, customer_id):
    """Send message to chat API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"message": message, "customer_id": customer_id},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to send message: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return None

def get_analytics():
    """Fetch analytics data"""
    try:
        response = requests.get(f"{API_BASE_URL}/analytics", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch analytics: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return None

# Main app
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🛒 Walmart AI Support Assistant</h1>
        <p>Intelligent customer support powered by AI</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for customer selection
    with st.sidebar:
        st.header("Customer Selection")
        customers = get_customers()
        if customers:
            customer_options = {f"{c['name']} ({c['customer_id']})": c['customer_id'] for c in customers}
            selected_customer = st.selectbox(
                "Select Customer",
                options=list(customer_options.keys()),
                index=0 if customer_options else None,
                placeholder="Select a customer..."
            )
            customer_id = customer_options.get(selected_customer)
        else:
            st.warning("No customers available. Please check the API or data files.")
            customer_id = None
            selected_customer = None

        if customer_id and customer_id != st.session_state.selected_customer:
            st.session_state.selected_customer = customer_id
            st.session_state.customer_data = get_customer_info(customer_id)
            st.session_state.messages = []  # Clear chat history on customer change

        # Predefined scenario buttons
        if customer_id:
            st.header("Quick Scenarios")
            scenarios = [
                "Where is my order ORD001?",
                "My payment for ORD002 failed",
                "I want a refund for ORD005",
                "My wallet balance shows ₹0",
                "When will ORD003 be delivered?"
            ]
            for scenario in scenarios:
                if st.button(scenario, key=f"scenario_{scenario}", help="Send this predefined query"):
                    response = send_message(scenario, customer_id)
                    if response:
                        st.session_state.messages.append({
                            "role": "user",
                            "content": scenario,
                            "timestamp": datetime.now().isoformat()
                        })
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response['response'],
                            "intent": response['intent'],
                            "timestamp": response['timestamp']
                        })

    # Main layout with two columns
    col1, col2 = st.columns([2, 1])

    # Column 1: Chat interface
    with col1:
        st.header("Chat Support")
        chat_container = st.container()
        
        with chat_container:
            if not customer_id:
                st.info("Please select a customer to start chatting.")
            else:
                # Display chat history
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(f"**{message['role'].capitalize()}** ({message['timestamp']}):")
                        st.write(message["content"])
                        if message["role"] == "assistant" and "intent" in message:
                            st.markdown(f"**Detected Intent**: {message['intent']}")

                # Chat input
                prompt = st.chat_input("Type your message here...", disabled=not customer_id)
                if prompt and customer_id:
                    # Add user message to history
                    st.session_state.messages.append({
                        "role": "user",
                        "content": prompt,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Get and display assistant response
                    response = send_message(prompt, customer_id)
                    if response:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response['response'],
                            "intent": response['intent'],
                            "timestamp": response['timestamp']
                        })
                    
                    # Refresh the page to show new messages
                    st.rerun()

    # Column 2: Customer information and analytics
    with col2:
        # Customer Information
        if st.session_state.customer_data and customer_id:
            customer = st.session_state.customer_data['customer']
            st.header("Customer Information")
            with st.container():
                st.markdown("""
                <div class="customer-info">
                """, unsafe_allow_html=True)
                st.markdown(f"**Name**: {customer['name']}")
                st.markdown(f"**ID**: {customer['customer_id']}")
                st.markdown(f"**Email**: {customer['email']}")
                st.markdown(f"**Phone**: {customer['phone']}")
                st.markdown(f"**Membership**: {customer['membership']}")
                st.markdown(f"**Location**: {customer['location']}")
                st.markdown(f"**Wallet Balance**: ₹{customer['wallet_balance']:.2f}")
                st.markdown(f"**Total Spent**: ₹{customer['total_spent']:.2f}")
                st.markdown(f"**Recent Orders**: {', '.join(customer['recent_orders'])}")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Select a customer to view their information.")

        # Analytics Dashboard
        st.header("Analytics Dashboard")
        analytics = get_analytics()
        if analytics:
            # Metrics
            col_metrics = st.columns(3)
            with col_metrics[0]:
                st.markdown("""
                <div class="metric-card">
                    <h4>Total Interactions</h4>
                    <p>{}</p>
                </div>
                """.format(analytics['total_interactions']), unsafe_allow_html=True)
            with col_metrics[1]:
                st.markdown("""
                <div class="metric-card">
                    <h4>Resolution Rate</h4>
                    <p>{}%</p>
                </div>
                """.format(analytics['resolution_rate']), unsafe_allow_html=True)
            with col_metrics[2]:
                st.markdown("""
                <div class="metric-card">
                    <h4>Avg Response Time</h4>
                    <p>{}s</p>
                </div>
                """.format(analytics['avg_response_time']), unsafe_allow_html=True)

            # Intent Distribution Pie Chart
            intent_data = analytics['intent_distribution']
            fig = px.pie(
                values=list(intent_data.values()),
                names=list(intent_data.keys()),
                title="Intent Distribution",
                color_discrete_sequence=px.colors.sequential.Blues
            )
            st.plotly_chart(fig, use_container_width=True)

            # Top Issues
            st.subheader("Top Issues")
            for issue in analytics['top_issues']:
                st.markdown(f"- {issue}")
        else:
            st.info("Analytics data unavailable.")

if __name__ == "__main__":
    main()