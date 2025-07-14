import streamlit as st
import requests
import json
import time
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import calendar

# Page configuration
st.set_page_config(
    page_title="Walmart AI Support",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with light/dark mode support
st.markdown("""
<style>
    :root {
        --primary-gradient-start: #0078d4;
        --primary-gradient-end: #005a9e;
        --primary-color: #0078d4;
        --secondary-color: #22c55e;
        --text-color: #ffffff;
        --background-color: #1a1a1a;
        --card-background: #2d2d2d;
        --light-gray: #4a4a4a;
        --shadow-color: rgba(0,0,0,0.2);
        --hover-background: #005a9e;
    }

    @media (prefers-color-scheme: light) {
        :root {
            --primary-gradient-start: #0078d4;
            --primary-gradient-end: #005a9e;
            --primary-color: #005a9e;
            --secondary-color: #22c55e;
            --text-color: #1a1a1a;
            --background-color: #f5f7fa;
            --card-background: #ffffff;
            --light-gray: #e5e7eb;
            --shadow-color: rgba(0,0,0,0.1);
            --hover-background: #004c91;
        }
    }

    /* Global styles */
    body {
        font-family: 'Inter', sans-serif;
        background-color: var(--background-color);
        color: var(--text-color);
        transition: all 0.3s ease;
    }

    /* Main header */
    .main-header {
        background: linear-gradient(135deg, var(--primary-gradient-start) 0%, var(--primary-gradient-end) 100%);
        color: var(--text-color);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px var(--shadow-color);
    }
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--card-background);
        border-right: 1px solid var(--light-gray);
        padding: 1.5rem;
    }
    .css-1d391kg .stSelectbox {
        background: var(--card-background);
        border-radius: 8px;
        padding: 0.5rem;
        color: var(--text-color);
        border: 1px solid var(--light-gray);
    }
    .css-1d391kg .stSelectbox option {
        background: var(--card-background);
        color: var(--text-color);
    }

    /* Customer info card */
    .customer-info {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid var(--primary-color);
        box-shadow: 0 4px 6px var(--shadow-color);
        margin-bottom: 1.5rem;
        color: var(--text-color);
    }

    /* Chat container */
    .chat-container {
        background: var(--card-background);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px var(--shadow-color);
        min-height: 500px;
        max-height: 600px;
        overflow-y: auto;
    }
    .chat-container .stChatMessage {
        border-radius: 8px;
        margin-bottom: 1rem;
        padding: 1rem;
        background: var(--light-gray);
    }
    .chat-container .stChatMessage[data-testid="stChatMessageUser"] {
        background: #e6f3ff;
    }

    /* Metric cards */
    .metric-card {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px var(--shadow-color);
        text-align: center;
        transition: transform 0.2s;
        color: var(--text-color);
    }
    .metric-card:hover {
        transform: translateY(-4px);
    }
    .metric-card h4 {
        color: var(--text-color);
        margin-bottom: 0.5rem;
    }
    .metric-card p {
        font-size: 1.5rem;
        color: var(--primary-color);
        font-weight: 600;
    }

    /* Buttons */
    .scenario-button {
        background: var(--primary-color);
        color: var(--text-color);
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        cursor: pointer;
        width: 100%;
        font-weight: 500;
        transition: background 0.2s;
    }
    .scenario-button:hover {
        background: var(--hover-background);
    }

    /* Subscription panel */
    .subscription-panel {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid var(--secondary-color);
        box-shadow: 0 4px 6px var(--shadow-color);
        color: var(--text-color);
    }
    .subscription-panel h3 {
        color: var(--text-color);
        margin-bottom: 1rem;
    }

    /* Calendar container */
    .calendar-container {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px var(--shadow-color);
        color: var(--text-color);
    }
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 5px;
        text-align: center;
    }
    .calendar-day {
        padding: 10px;
        border-radius: 8px;
        cursor: pointer;
        background: var(--light-gray);
        color: var(--text-color);
        transition: background 0.2s;
    }
    .calendar-day:hover {
        background: var(--primary-color);
    }
    .calendar-day-selected {
        background: var(--secondary-color);
        color: var(--text-color);
    }
    .calendar-day-header {
        font-weight: 600;
        padding: 10px;
        color: var(--text-color);
    }
    .calendar-day-disabled {
        background: var(--background-color);
        color: var(--light-gray);
        cursor: not-allowed;
    }

    /* Form styling */
    .stForm {
        background: var(--light-gray);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--light-gray);
        color: var(--text-color);
    }
    .stButton>button {
        background: var(--primary-color);
        color: var(--text-color);
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        border: none;
        font-weight: 500;
    }
    .stButton>button:hover {
        background: var(--hover-background);
    }

    /* Navigation */
    .stMultiPageNav {
        background: var(--card-background);
        padding: 1rem;
        border-bottom: 1px solid var(--light-gray);
        margin-bottom: 2rem;
    }
    .stMultiPageNav button {
        color: var(--text-color);
        font-weight: 500;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        margin-right: 0.5rem;
    }
    .stMultiPageNav button:hover {
        background: var(--light-gray);
    }
    .stMultiPageNav button[selected] {
        background: var(--primary-color);
        color: var(--text-color);
    }

    /* Input and select styling */
    .stTextInput, .stNumberInput, .stSelectbox div {
        background: var(--card-background) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--light-gray) !important;
    }
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background: var(--card-background) !important;
        color: var(--text-color) !important;
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
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None
if "selected_subscription_type" not in st.session_state:
    st.session_state.selected_subscription_type = "weekly"

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

def create_subscription(customer_id, items, delivery_date, subscription_type):
    """Create a subscription via API with subscription type"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/subscription",
            json={"customer_id": customer_id, "items": items, "delivery_date": delivery_date, "subscription_type": subscription_type},
            timeout=5
        )
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"Failed to create subscription: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return None

def get_subscriptions(customer_id):
    """Fetch subscriptions for a customer"""
    try:
        response = requests.get(f"{API_BASE_URL}/subscriptions/{customer_id}", timeout=5)
        if response.status_code == 200:
            return response.json().get('subscriptions', [])
        else:
            st.error(f"Failed to fetch subscriptions: HTTP {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return []

def cancel_subscription(subscription_id):
    """Cancel a subscription via API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/subscription/cancel/{subscription_id}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to cancel subscription: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return None

def get_subscription_notifications(customer_id):
    """Fetch subscription notifications"""
    try:
        response = requests.get(f"{API_BASE_URL}/subscription/notifications/{customer_id}", timeout=5)
        if response.status_code == 200:
            return response.json().get('notifications', [])
        else:
            st.error(f"Failed to fetch notifications: HTTP {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return []

# Page definitions
def main_page():
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
                placeholder="Select a customer...",
                key="main_page_customer_select"
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
                "When will ORD003 be delivered?",
                "Set up weekly delivery for milk"
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

    # Main layout with two columns (chat + customer info/analytics)
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

def subscription_page():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🛒 Autonomous Order Planner</h1>
        <p>Manage your Walmart order plans</p>
    </div>
    """, unsafe_allow_html=True)

    # Customer selection
    customers = get_customers()
    if customers:
        customer_options = {f"{c['name']} ({c['customer_id']})": c['customer_id'] for c in customers}
        selected_customer = st.selectbox(
            "Select Customer",
            options=list(customer_options.keys()),
            index=0 if customer_options else None,
            placeholder="Select a customer...",
            key="subscription_page_customer_select"
        )
        customer_id = customer_options.get(selected_customer)
    else:
        st.warning("No customers available. Please check the API or data files.")
        customer_id = None
        selected_customer = None

    # Subscription Management
    with st.container():
        st.markdown("""
        <div class="subscription-panel">
        """, unsafe_allow_html=True)
        if not customer_id:
            st.info("Select a customer to manage Order Plans.")
        else:
            # Display existing subscriptions
            subscriptions = get_subscriptions(customer_id)
            if subscriptions:
                st.subheader("Current Order Plans")
                for sub in subscriptions:
                    st.markdown(f"**Order Plan {sub['subscription_id']}**")
                    st.markdown(f"- **Items**: {', '.join([item['name'] for item in sub['items']])}")
                    # Handle both delivery_date and delivery_day for backward compatibility
                    delivery_info = sub.get('delivery_date', sub.get('delivery_day', 'N/A'))
                    st.markdown(f"- **Delivery**: {delivery_info}")
                    st.markdown(f"- **Type**: {sub.get('subscription_type', 'N/A')}")
                    st.markdown(f"- **Status**: {sub['status']}")
                    if st.button(f"Cancel {sub['subscription_id']}", key=f"cancel_{sub['subscription_id']}"):
                        if cancel_subscription(sub['subscription_id']):
                            st.success(f"Order Plan {sub['subscription_id']} cancelled.")
                            st.rerun()
            else:
                st.info("No order plans found for this customer.")

            # Subscription notifications
            notifications = get_subscription_notifications(customer_id)
            if notifications:
                st.subheader("Upcoming Deliveries")
                for notif in notifications:
                    st.markdown(f"- {notif['message']}")

            # Placeholder Calendar for July 2025 in row and column format
            st.subheader("Select Delivery Date (July 2025)")
            with st.container():
                st.markdown("""
                <div class="calendar-container">
                """, unsafe_allow_html=True)
                # Generate calendar for July 2025
                cal = calendar.monthcalendar(2025, 7)
                days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                current_date = datetime.now().date()  # Get current date for comparison

                # Header row for days of the week
                cols = st.columns(7)
                for i, day in enumerate(days):
                    with cols[i]:
                        st.markdown(f'<div class="calendar-day-header">{day}</div>', unsafe_allow_html=True)

                # Rows for each week
                for week in cal:
                    cols = st.columns(7)
                    for i, day in enumerate(week):
                        with cols[i]:
                            if day == 0:
                                st.markdown('<div class="calendar-day-disabled"></div>', unsafe_allow_html=True)
                            else:
                                # Create date object for the calendar day
                                calendar_date = date(2025, 7, day)
                                is_past_date = calendar_date < current_date
                                is_selected = st.session_state.selected_date == calendar_date
                                css_class = "calendar-day-selected" if is_selected else "calendar-day"
                                if is_past_date:
                                    css_class = "calendar-day-disabled"
                                    st.markdown(f'<div class="{css_class}"></div>', unsafe_allow_html=True)
                                else:
                                    if st.button(
                                        str(day),
                                        key=f"calendar_day_{day}",
                                        help=f"Select {calendar_date.strftime('%Y-%m-%d')}",
                                        disabled=is_past_date
                                    ):
                                        st.session_state.selected_date = calendar_date
                                        st.rerun()
                                    st.markdown(f'<div class="{css_class}"></div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            # Create new subscription
            st.subheader("Create New Subscription")
            with st.form(key="subscription_form"):
                item_name = st.text_input("Item Name")
                item_price = st.number_input("Item Price (₹)", min_value=0.0, step=0.01)
                item_quantity = st.number_input("Quantity", min_value=1, step=1)
                subscription_type = st.selectbox(
                    "Subscription Type",
                    options=["daily", "weekly", "monthly"],
                    index=["daily", "weekly", "monthly"].index(st.session_state.selected_subscription_type),
                    key="subscription_type_select"
                )
                st.session_state.selected_subscription_type = subscription_type
                delivery_date = st.session_state.selected_date.strftime("%Y-%m-%d") if st.session_state.selected_date else "Select a date from the calendar"
                st.text_input("Delivery Date", value=delivery_date, disabled=True)
                submit_button = st.form_submit_button("Create Subscription")
                if submit_button and item_name and item_price and item_quantity and st.session_state.selected_date:
                    items = [{"name": item_name, "price": item_price, "quantity": item_quantity}]
                    response = create_subscription(customer_id, items, delivery_date, subscription_type)
                    if response and ('message' in response or response.get('subscription')):
                        st.success(response.get('message', f"Order Plan created successfully!"))
                        st.session_state.selected_date = None  # Reset selected date
                    elif response and 'error' in response:
                        st.error(f"Failed to create order plan: {response['error']}")
                    else:
                        st.error("Failed to create order plan. Please try again.")
                    st.rerun()
                elif submit_button and not st.session_state.selected_date:
                    st.error("Please select a delivery date from the calendar.")
        st.markdown("</div>", unsafe_allow_html=True)

# Navigation
st.markdown("""
<div class="stMultiPageNav">
</div>
""", unsafe_allow_html=True)

page = st.radio("Navigate", ["Support Dashboard", "Autonomous Order Planner"], horizontal=True, key="page_navigation")
if page == "Support Dashboard":
    main_page()
else:
    subscription_page()