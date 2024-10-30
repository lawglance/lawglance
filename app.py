import os
import streamlit as st
import random
import time
from lawglance_main import Lawglance
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
from langchain.schema import HumanMessage


st.title("LawGlance")
load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key)
embeddings = OpenAIEmbeddings()
vector_store = Chroma(persist_directory="chroma_db_legal_bot_part1", embedding_function=embeddings)
law = Lawglance(llm, embeddings, vector_store)


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Have a legal question? Let’s work through it."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    query = prompt

    result = law.llm_answer_generator(query)


    def response_generator(result):  # To generate text as a list of pre-determind responses.
        response = random.choice([result])
        for word in response.split():
            yield word + " "
            time.sleep(0.05)


    final_response = f"AI Legal Assistant: {result}"

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(final_response))

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
