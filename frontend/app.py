import streamlit as st
from api_client import APIClient, APIClientError

# Page layout & styling
st.set_page_config(
    page_title="FastAPI Docs Assistant",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("⚡ FastAPI Documentation Assistant")
st.caption("Ask questions grounded strictly in official FastAPI documentation.")

# Initialize API client
client = APIClient()

# Sidebar: System status & instructions
with st.sidebar:
    st.header("⚙️ System Status")
    st.markdown(f"**Backend URL:** `{client.base_url}`")

    if st.button("Check Backend Connection", use_container_width=True):
        try:
            health = client.check_health()
            st.success("✅ Backend Online")
            st.json(health)
        except APIClientError as err:
            st.error(f"❌ Connection Failed: {err}")

    st.divider()
    st.markdown("### 💡 Example Questions")
    example_prompts = [
        "How do I declare a request body with Pydantic?",
        "How does dependency injection work?",
        "How do I set a default value for a query parameter?",
        "How do I add CORS middleware to my FastAPI app?",
    ]
    for ex in example_prompts:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state["user_query_input"] = ex

# Maintain chat message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous conversation messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Cited Source Files"):
                for src in message["sources"]:
                    st.markdown(f"- `{src}`")

# Chat input prompt
user_question = st.chat_input("Ask a question about FastAPI...")

# Handle sidebar example selection if clicked
if "user_query_input" in st.session_state and st.session_state["user_query_input"]:
    user_question = st.session_state.pop("user_query_input")

if user_question:
    # Append user question to chat
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Generate assistant response with loading spinner
    with st.chat_message("assistant"):
        with st.spinner("Searching FastAPI documentation and generating answer..."):
            try:
                response = client.query(user_question)
                answer_text = response["answer"]
                sources = response.get("sources", [])

                st.markdown(answer_text)

                if sources:
                    with st.expander("📚 Cited Source Files"):
                        for src in sources:
                            st.markdown(f"- `{src}`")

                # Store response in session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer_text,
                    "sources": sources,
                })

            except APIClientError as e:
                st.error(f"⚠️ {str(e)}")
