# app.py (Streamlit Frontend)

import streamlit as st
import requests
from datetime import datetime
import plotly.express as px

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
</style>
""", unsafe_allow_html=True)

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
    try:
        res = requests.get(f"{API_BASE_URL}/customers", timeout=5)
        if res.status_code == 200:
            return res.json().get('customers', [])
    except Exception as e:
        st.error(f"Failed to fetch customers: {e}")
    return []

def get_customer_info(customer_id):
    try:
        res = requests.get(f"{API_BASE_URL}/customer/{customer_id}", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to fetch customer info: {e}")
    return None

def send_message(msg, customer_id):
    try:
        res = requests.post(f"{API_BASE_URL}/chat", json={"message": msg, "customer_id": customer_id}, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to send message: {e}")
    return None

def get_analytics():
    try:
        res = requests.get(f"{API_BASE_URL}/analytics", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to fetch analytics: {e}")
    return None

def main():
    st.markdown("""
    <div class="main-header">
        <h1>🛒 Walmart AI Support Assistant</h1>
        <p>Intelligent customer support powered by AI</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("Customer Selection")
        customers = get_customers()
        if customers:
            options = {f"{c['name']} ({c['customer_id']})": c['customer_id'] for c in customers}
            selected = st.selectbox("Select Customer", list(options.keys()))
            customer_id = options[selected]

            if customer_id != st.session_state.selected_customer:
                st.session_state.selected_customer = customer_id
                st.session_state.customer_data = get_customer_info(customer_id)
                st.session_state.messages = []
        else:
            st.warning("No customers available.")
            customer_id = None

        if customer_id:
            st.header("Quick Scenarios")
            scenarios = [
                "Where is my order ORD001?",
                "My payment for ORD002 failed",
                "I want a refund for ORD005",
                "My wallet balance shows ₹0",
                "When will ORD003 be delivered?"
            ]
            for s in scenarios:
                if st.button(s, key=f"scenario_{s}"):
                    resp = send_message(s, customer_id)
                    if resp:
                        st.session_state.messages.append({"role": "user", "content": s, "timestamp": datetime.now().isoformat()})
                        st.session_state.messages.append({"role": "assistant", "content": resp['response'], "intent": resp['intent'], "timestamp": resp['timestamp']})

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Chat Support")
        if not customer_id:
            st.info("Please select a customer to chat.")
        else:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(f"**{msg['role'].capitalize()}** ({msg['timestamp']}):")
                    st.write(msg["content"])
                    if msg["role"] == "assistant" and "intent" in msg:
                        st.markdown(f"**Detected Intent**: {msg['intent']}")

            st.write("---")
            input_col1, input_col2, input_col3 = st.columns([5, 1, 1])

            with input_col1:
                prompt = st.text_input("Type your message", key="chat_input", label_visibility="collapsed")

            with input_col2:
                uploaded_file = st.file_uploader(" ", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

            with input_col3:
                mic_pressed = st.button("🎙️", help="Record and send speech")

            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt, "timestamp": datetime.now().isoformat()})
                resp = send_message(prompt, customer_id)
                if resp:
                    st.session_state.messages.append({"role": "assistant", "content": resp['response'], "intent": resp['intent'], "timestamp": resp['timestamp']})
                st.rerun()

            if uploaded_file:
                files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
                res = requests.post(f"{API_BASE_URL}/upload", files=files)
                if res.status_code == 200:
                    st.success(f"✅ {uploaded_file.name} uploaded.")
                else:
                    st.error("❌ Upload failed.")

            if mic_pressed:
                st.info("Record a WAV file & upload here.")
                audio_file = st.file_uploader("Upload recorded audio", type=["wav"], key="mic_audio")
                if audio_file:
                    files = {'audio': (audio_file.name, audio_file.getvalue())}
                    res = requests.post(f"{API_BASE_URL}/speech-to-text", files=files)
                    if res.status_code == 200:
                        data = res.json()
                        if "text" in data:
                            st.success(f"✅ Recognized: {data['text']}")
                            st.session_state.messages.append({"role": "user", "content": data['text'], "timestamp": datetime.now().isoformat()})
                            chat_resp = send_message(data['text'], customer_id)
                            if chat_resp:
                                st.session_state.messages.append({"role": "assistant", "content": chat_resp['response'], "intent": chat_resp['intent'], "timestamp": chat_resp['timestamp']})
                            st.rerun()
                        else:
                            st.error(data.get('error'))

    with col2:
        if st.session_state.customer_data:
            cust = st.session_state.customer_data['customer']
            st.header("Customer Information")
            with st.container():
                st.markdown("<div class='customer-info'>", unsafe_allow_html=True)
                st.markdown(f"**Name:** {cust['name']}")
                st.markdown(f"**ID:** {cust['customer_id']}")
                st.markdown(f"**Email:** {cust['email']}")
                st.markdown(f"**Phone:** {cust['phone']}")
                st.markdown(f"**Membership:** {cust['membership']}")
                st.markdown(f"**Location:** {cust['location']}")
                st.markdown(f"**Wallet Balance:** ₹{cust['wallet_balance']:.2f}")
                st.markdown(f"**Total Spent:** ₹{cust['total_spent']:.2f}")
                st.markdown(f"**Recent Orders:** {', '.join(cust['recent_orders'])}")
                st.markdown("</div>", unsafe_allow_html=True)

        st.header("Analytics Dashboard")
        analytics = get_analytics()
        if analytics:
            col_metrics = st.columns(3)
            col_metrics[0].markdown(f"<div class='metric-card'><h4>Total Interactions</h4><p>{analytics['total_interactions']}</p></div>", unsafe_allow_html=True)
            col_metrics[1].markdown(f"<div class='metric-card'><h4>Resolution Rate</h4><p>{analytics['resolution_rate']}%</p></div>", unsafe_allow_html=True)
            col_metrics[2].markdown(f"<div class='metric-card'><h4>Avg Response Time</h4><p>{analytics['avg_response_time']}s</p></div>", unsafe_allow_html=True)

            fig = px.pie(
                values=list(analytics['intent_distribution'].values()),
                names=list(analytics['intent_distribution'].keys()),
                title="Intent Distribution",
                color_discrete_sequence=px.colors.sequential.Blues
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Top Issues")
            for issue in analytics['top_issues']:
                st.markdown(f"- {issue}")

if __name__ == "__main__":
    main()
