import os
import streamlit as st
import random
import time
import base64
import uuid
from dotenv import load_dotenv

from lawglance_main import Lawglance
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import HumanMessage, AIMessage

# Set page configuration
st.set_page_config(page_title="LawGlance", page_icon="logo/logo.png", layout="wide")

# Load environment variables
load_dotenv()

# Custom CSS for UI
def add_custom_css():
    custom_css = """
    <style>
        body { font-family: 'Arial', sans-serif; }
        .st-chat-input {
            border-radius: 15px; padding: 10px;
            border: 1px solid #ddd; margin-bottom: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        .stButton > button {
            background-color: #0066cc; color: white;
            font-size: 16px; border-radius: 20px;
            padding: 10px 20px; margin-top: 5px;
            transition: background-color 0.3s ease;
        }
        .stButton > button:hover { background-color: #0052a3; }
        .st-chat-message-assistant {
            background-color: #f7f7f7; border-radius: 15px;
            padding: 15px; margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .st-chat-message-user {
            background-color: #d9f0ff; border-radius: 15px;
            padding: 15px; margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .chat-input-container {
            position: fixed; bottom: 0; width: 100%;
            background-color: #f0f0f0; padding: 20px;
            box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
            display: flex; gap: 10px;
        }
        .chat-input { flex-grow: 1; }
        .st-title {
            font-family: 'Arial', sans-serif; font-weight: bold;
            color: #333; display: flex; align-items: center;
            gap: 15px; margin-top: 20px; margin-bottom: 20px;
        }
        .logo { width: 40px; height: 30px; }
        .st-sidebar {
            background-color: #f9f9f9; padding: 20px;
        }
        .st-sidebar header {
            font-size: 20px; font-weight: bold; margin-bottom: 10px;
        }
        .st-sidebar p {
            font-size: 14px; color: #666;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

add_custom_css()

# Title with Logo
logo_path = "logo/logo.png"
if os.path.exists(logo_path):
    with open(logo_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()
    st.markdown(f"""
    <div class="st-title">
        <img src="data:image/png;base64,{encoded_image}" alt="LawGlance Logo" class="logo">
        <span>LawGlance - An AI Legal Assistant </span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="st-title">
        <span>LawGlance - Your Legal Assistant 📖</span>
    </div>
    """, unsafe_allow_html=True)

# Sidebar Info
st.sidebar.header("About LawGlance")
st.sidebar.markdown("""
**LawGlance** is a free, open-source AI legal assistant that helps answer legal questions.

Visit our website: [LawGlance](https://lawglance.com)

_Disclaimer_: This tool is in its pilot phase, and responses may not be 100% accurate.
""")

# Persistent session ID
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

thread_id = st.session_state.thread_id

# Load OpenAI models
openai_api_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.9, openai_api_key=openai_api_key)
embeddings = OpenAIEmbeddings()
vector_store = Chroma(persist_directory="chroma_db_legal_bot_part1", embedding_function=embeddings)

# Create LawGlance instance
law = Lawglance(llm, embeddings, vector_store)

# Get chat history from backend and display
if "messages" not in st.session_state:
    st.session_state.messages = []

    history = law.get_session_history(thread_id).messages
    for msg in history:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        st.session_state.messages.append({"role": role, "content": msg.content})

# Display history
for message in st.session_state.messages:
    role = "user" if message["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(message["content"])

# Prompt input
st.markdown("<div class='chat-input-container'>", unsafe_allow_html=True)
prompt = st.chat_input("Have a legal question? Let’s work through it.")
st.markdown("</div>", unsafe_allow_html=True)

if prompt and prompt.strip():
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Invoke LawGlance backend
    result, updated_history = law.conversational(prompt, thread_id)

    # Rebuild session messages from updated Redis chat
    st.session_state.messages = []
    for msg in updated_history:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        st.session_state.messages.append({"role": role, "content": msg.content})

    # Animate AI response
    final_response = f"AI Legal Assistant: {result}"

    def response_generator(response):
        for word in response.split():
            yield word + " "
            time.sleep(0.05)

    with st.chat_message("assistant"):
        animated = "".join(list(response_generator(final_response)))
        st.markdown(animated)
