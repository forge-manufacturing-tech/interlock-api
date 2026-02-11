import json

import pandas as pd
import streamlit as st

from frontend.api import (
    chat_agent,
    check_health,
    get_part_details,
    get_parts,
    ingest_bom,
)

# Page config
st.set_page_config(
    page_title="Interlock Manufacturing",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern aesthetic
st.markdown(
    """
    <style>
        /* Import font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        /* Base Styles */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background-color: #0F172A; /* Slate 900 */
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #1E293B; /* Slate 800 */
            border-right: 1px solid #334155;
        }

        /* Glassmorphism Card Effect */
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            padding: 24px;
            box-shadow:
                0 4px 6px -1px rgba(0, 0, 0, 0.1),
                0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin-bottom: 24px;
        }

        /* Typography */
        h1 {
            background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800 !important;
            letter-spacing: -0.025em;
        }

        h2, h3 {
            color: #F8FAFC;
        }

        p, label {
            color: #CBD5E1;
        }

        /* Custom Button */
        .stButton > button {
            background: linear-gradient(to right, #3B82F6, #8B5CF6);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        /* Dataframe styling */
        .stDataFrame {
            border: 1px solid #334155;
            border-radius: 8px;
            overflow: hidden;
        }

        /* Status Indicators */
        .status-dot {
            height: 10px;
            width: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }

        .status-online {
            background-color: #10B981;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
        }

        .status-offline {
            background-color: #EF4444;
            box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
        }
    </style>
""",
    unsafe_allow_html=True,
)


# Helper for displaying JSON
def display_json_collapsible(data, label="Details"):
    with st.expander(label):
        st.json(data)


# --- Sidebar ---
with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/infrastructure.png", width=64
    )  # Placeholder logo
    st.title("Interlock")
    st.caption("Manufacturing Graph Intelligence")

    st.markdown("---")

    nav_option = st.radio(
        "Navigation",
        ["🤖 Agent Chat", "📊 Parts Explorer", "📥 BOM Ingest"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # System Status
    is_online = check_health()
    status_class = "status-online" if is_online else "status-offline"
    status_text = "System Online" if is_online else "System Offline"

    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: center;
            background: rgba(255,255,255,0.03);
            padding: 12px;
            border-radius: 8px;
        ">
            <span class="status-dot {status_class}"></span>
            <span style="
                color: #E2E8F0;
                font-size: 0.9rem;
                font-weight: 500;
            ">{status_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not is_online:
        st.error("Cannot connect to API at http://127.0.0.1:8000")

# --- Main Content ---

if nav_option == "🤖 Agent Chat":
    st.title("Manufacturing Assistant")
    st.markdown("Ask questions about your manufacturing graph, parts, or processes.")

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("How can I help you today?"):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response from API
        with st.spinner("Thinking..."):
            response_data = chat_agent(prompt)

            # Simple handling of response - depends on actual API return structure
            # If the response has 'response' key or similar
            if "error" in response_data:
                bot_reply = f"Error: {response_data['error']}"
            else:
                # Assuming the API returns something like {"response": "..."}
                # or just a json dump if structure is unknown
                bot_reply = str(response_data)
                # Pretty print if it's a dict
                if isinstance(response_data, dict):
                    # Try to clean it up if possible
                    bot_reply = json.dumps(response_data, indent=2)

        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(
                f"```json\n{bot_reply}\n```"
                if isinstance(response_data, dict)
                else bot_reply
            )

elif nav_option == "📊 Parts Explorer":
    st.title("Parts Explorer")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Browse and manage parts within the manufacturing graph.")
    with col2:
        if st.button("🔄 Refresh Data"):
            st.rerun()

    # Fetch parts
    with st.spinner("Loading parts..."):
        parts_data = get_parts(limit=100)

    if parts_data:
        df = pd.DataFrame(parts_data)

        # Data Grid
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        # Search filter
        search_term = st.text_input(
            "Search parts...", placeholder="Filter by name or ID"
        )
        if search_term and not df.empty:
            df = df[
                df.astype(str)
                .apply(lambda x: x.str.contains(search_term, case=False))
                .any(axis=1)
            ]

        st.dataframe(
            df,
            column_config={
                "id": "ID",
                "name": "Name",
                "description": "Description",
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    help="Current status of the part",
                    options=["PENDING", "APPROVED", "REJECTED"],
                    required=True,
                ),
                "is_currency": st.column_config.CheckboxColumn(
                    "Is Currency",
                    help="Is this a currency node?",
                    default=False,
                ),
            },
            use_container_width=True,
            height=600,
            hide_index=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Drill down details (optional interaction)
        st.markdown("### Part Details")
        selected_part_id = st.text_input(
            "Enter Part ID for deep dive", placeholder="UUID..."
        )
        if selected_part_id:
            with st.spinner(f"Fetching details for {selected_part_id}..."):
                details = get_part_details(selected_part_id)
                if details:
                    st.success("Part Found")
                    st.json(details)
                else:
                    st.error("Part not found")
    else:
        st.info("No parts found in the database.")

elif nav_option == "📥 BOM Ingest":
    st.title("Bill of Materials Ingestion")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("""
        Upload your Bill of Materials (BOM) file here.
        Supported formats: CSV, Excel, JSON.
    """)

    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "json"])

    if uploaded_file is not None:
        st.info(f"File selected: {uploaded_file.name} ({uploaded_file.size} bytes)")

        if st.button("🚀 Process Ingestion", type="primary"):
            with st.spinner("Ingesting BOM..."):
                result = ingest_bom(uploaded_file)

                if "error" in result:
                    st.error(f"Ingestion Failed: {result['error']}")
                else:
                    st.success("Ingestion Successful!")
                    with st.expander("View Response"):
                        st.json(result)

    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown(
    """
    <div style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        opacity: 0.5;
        font-size: 0.8rem;
    ">
        Powered by Interlock AI
    </div>
    """,
    unsafe_allow_html=True,
)
