from langchain_openai import OpenAIEmbeddings
from langchain_openai import OpenAI
from langchain_chroma import Chroma
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv
from langchain.schema import HumanMessage
import os
import streamlit as st
import random
import time

st.title("Niyam Saha-AI")
load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
llm = OpenAI(temperature=0, openai_api_key=openai_api_key)
embeddings = OpenAIEmbeddings()
vector_store = Chroma(persist_directory="chroma_db_legal_bot_part1", embedding_function=embeddings)
retriever = vector_store.as_retriever(search_type="similarity")

# Initialize session state for chat memory
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []  # Initialize chat memory in session state

contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is.\
If general greeting words or incomplete questions which are totally not related \
to chat history then handle this in such a way that model doesn't formulate a wrong standalone question
"""


contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_memory"),
        ("human", "{input}"),
    ]
)


history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

qa_system_prompt = """You are an Legal Assistant for question-answering \
tasks relating to Indian Laws. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
\

{context}"""
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_memory"),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_memory",
    output_messages_key="answer", )





def chat(question):
    ai = rag_chain.invoke({"input": question, "chat_memory": st.session_state.chat_memory})
    st.session_state.chat_memory.extend([HumanMessage(content=question), ai["answer"]])
    return ai


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

    result_text = chat(query)["answer"]

    # Extract the text after "System:" from the AI's response
    if "System:" in result_text:
        # Extract the text after "System:" and strip leading/trailing spaces
        result = result_text.split("System:")[1].strip()
    else:
        result = result_text  # If "System:" is not present, use the whole response


    def response_generator(result):  # To generate text as a list of pre-determind responses.
        response = random.choice([result])
        for word in response.split():
            yield word + " "
            time.sleep(0.05)


    final_response = f"AI Law Assistant: {result}"

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(final_response))

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})