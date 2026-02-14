import json

import pandas as pd
import streamlit as st

from frontend.api import (
    chat_agent,
    check_health,
    create_api_key,
    get_part_details,
    get_tree_structure,
    get_trees,
    ingest_bom,
    list_api_keys,
    login,
    revoke_api_key,
    signup,
)

st.set_page_config(
    page_title="Interlock Manufacturing",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background-color: #0F172A;
        }

        section[data-testid="stSidebar"] {
            background-color: #1E293B;
            border-right: 1px solid #334155;
        }

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

        .stDataFrame {
            border: 1px solid #334155;
            border-radius: 8px;
            overflow: hidden;
        }

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


def get_token() -> str | None:
    return st.session_state.get("token")


def show_auth_page():
    st.title("Welcome to Interlock")
    st.markdown("Sign in or create an account to get started.")

    tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign In", type="primary")

            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    result = login(email, password)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state.token = result["access_token"]
                        st.session_state.user = result["user"]
                        st.rerun()

    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Name (optional)", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
            submitted = st.form_submit_button("Create Account", type="primary")

            if submitted:
                if not email or not password:
                    st.error("Please fill in email and password.")
                elif password != password_confirm:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    result = signup(email, password, name if name else None)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state.token = result["access_token"]
                        st.session_state.user = result["user"]
                        st.rerun()


if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.user = None

if not st.session_state.token:
    show_auth_page()
    st.stop()

token = get_token()


def display_json_collapsible(data, label="Details"):
    with st.expander(label):
        st.json(data)


with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/infrastructure.png", width=64
    )
    st.title("Interlock")
    st.caption("Manufacturing Graph Intelligence")

    st.markdown("---")

    user = st.session_state.get("user", {})
    user_display = user.get("name") or user.get("email", "User")
    st.markdown(f"Signed in as **{user_display}**")
    if st.button("Sign Out"):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()

    st.markdown("---")

    nav_option = st.radio(
        "Navigation",
        ["🤖 Agent Chat", "📊 Parts Explorer", "🌳 Tree Visualizer", "📥 BOM Ingest", "🔑 API Keys"],
        label_visibility="collapsed",
    )

    st.markdown("---")

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

if nav_option == "🤖 Agent Chat":
    st.title("Manufacturing Assistant")
    st.markdown("Ask questions about your manufacturing graph, parts, or processes.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("How can I help you today?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Thinking..."):
            response_data = chat_agent(prompt, token)

            if "error" in response_data:
                bot_reply = f"Error: {response_data['error']}"
            else:
                bot_reply = str(response_data)
                if isinstance(response_data, dict):
                    bot_reply = json.dumps(response_data, indent=2)

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

    with st.spinner("Loading parts..."):
        parts_data = get_trees(token)

    if parts_data:
        df = pd.DataFrame(parts_data)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

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

        st.markdown("### Part Details")
        selected_part_id = st.text_input(
            "Enter Part ID for deep dive", placeholder="UUID..."
        )
        if selected_part_id:
            with st.spinner(f"Fetching details for {selected_part_id}..."):
                details = get_part_details(selected_part_id, token)
                if details:
                    st.success("Part Found")
                    st.json(details)
                else:
                    st.error("Part not found")
    else:
        st.info("No parts found in the database.")


elif nav_option == "🌳 Tree Visualizer":
    st.title("Manufacturing Tree Visualizer")
    st.markdown(
        "Visualize the end-to-end manufacturing hierarchy for each distinct product."
    )

    with st.spinner("Loading trees..."):
        roots = get_trees(token)

    if not roots:
        st.info(
            "No completed trees found. Use the Agent or BOM Ingest to build the graph."
        )
    else:
        selected_root_name = st.selectbox(
            "Select a Product Tree to Visualize",
            options=[f"{r['name']} ({r['id'][:8]})" for r in roots],
        )

        selected_root_id = next(
            r["id"]
            for r in roots
            if f"{r['name']} ({r['id'][:8]})" == selected_root_name
        )

        with st.spinner("Building visualization..."):
            tree_data = get_tree_structure(selected_root_id, token)

            if tree_data:
                import graphviz

                dot = graphviz.Digraph(comment="Manufacturing Tree")
                dot.attr(bgcolor="transparent")
                dot.attr(rankdir="TB")

                dot.attr(
                    "node",
                    shape="box",
                    style="filled,rounded",
                    fontname="Inter",
                    fontsize="10",
                )

                def add_to_graph(node, parent_id=None):
                    node_id = node["id"]
                    label = node["name"]
                    ntype = node["type"]

                    color = "#3B82F6"
                    fontcolor = "white"

                    if ntype == "part":
                        color = "#1E40AF"
                        uc = node.get("unit_cost")
                        cost_str = f"\n${uc:,.2f}" if uc is not None else ""
                        label = f"{label}\n(Part){cost_str}"
                    elif ntype == "operation":
                        color = "#8B5CF6"
                        label = f"{label}\n({node.get('op_type', 'OP')})"
                        shape = "ellipse"
                        dot.node(
                            node_id,
                            label,
                            fillcolor=color,
                            fontcolor=fontcolor,
                            shape=shape,
                        )
                    elif ntype == "currency":
                        color = "#10B981"
                        label = (
                            f"{label}\n{node.get('quantity', 0)} {node.get('unit', '')}"
                        )
                    elif ntype == "labor":
                        color = "#F59E0B"
                        label = (
                            f"{label}\n{node.get('quantity', 0)} {node.get('unit', '')}"
                        )
                    elif ntype == "tool":
                        color = "#6366F1"
                        label = (
                            f"{label}\n{node.get('quantity', 0)} {node.get('unit', '')}"
                        )

                    if ntype != "operation":
                        if "quantity" in node and ntype != "part":
                            pass

                        dot.node(node_id, label, fillcolor=color, fontcolor=fontcolor)

                    if parent_id:
                        dot.edge(parent_id, node_id)

                    for child in node.get("children", []):
                        add_to_graph(child, node_id)

                    if "linked_part" in node:
                        linked = node["linked_part"]
                        add_to_graph(linked, node_id)

                add_to_graph(tree_data)

                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.graphviz_chart(dot, width="stretch")
                st.markdown("</div>", unsafe_allow_html=True)

                with st.expander("View Raw Tree Data"):
                    st.json(tree_data)
            else:
                st.error("Failed to load tree structure.")

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
                result = ingest_bom(uploaded_file, token)

                if "error" in result:
                    st.error(f"Ingestion Failed: {result['error']}")
                else:
                    st.success("Ingestion Successful!")
                    with st.expander("View Response"):
                        st.json(result)

    st.markdown("</div>", unsafe_allow_html=True)

elif nav_option == "🔑 API Keys":
    st.title("API Key Management")
    st.markdown("Create and manage API keys for programmatic access to the Interlock API.")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Create New API Key")
    with st.form("create_api_key_form"):
        key_name = st.text_input("Key Name", placeholder="e.g. Production Server")
        submitted = st.form_submit_button("Generate API Key", type="primary")

        if submitted:
            if not key_name:
                st.error("Please provide a name for the API key.")
            else:
                result = create_api_key(token, key_name)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("API key created successfully!")
                    st.warning("Copy this key now. You won't be able to see it again.")
                    st.code(result["key"], language=None)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Your API Keys")
    st.markdown("Use these keys in the `x-api-key` header for programmatic API access.")

    keys = list_api_keys(token)
    if keys:
        for key_info in keys:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                status_emoji = "🟢" if not key_info.get("revoked_at") else "🔴"
                st.markdown(f"{status_emoji} **{key_info['name']}** (****{key_info['last4']})")
            with col2:
                st.caption(f"Created: {key_info['created_at'][:10]}")
                if key_info.get("last_used_at"):
                    st.caption(f"Last used: {key_info['last_used_at'][:10]}")
            with col3:
                if not key_info.get("revoked_at"):
                    if st.button("Revoke", key=f"revoke_{key_info['id']}"):
                        revoke_api_key(token, str(key_info["id"]))
                        st.rerun()
                else:
                    st.caption("Revoked")
    else:
        st.info("No API keys yet. Create one above to get started.")

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
