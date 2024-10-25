import streamlit as st
from langchain_openai import OpenAIEmbeddings
from langchain_openai import OpenAI
from langchain_chroma import Chroma
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.schema import HumanMessage
import random
import time

# Initialize session state for API key
if "openai_api_key" not in st.session_state:
    st.session_state["openai_api_key"] = None
if "api_key_submitted" not in st.session_state:
    st.session_state["api_key_submitted"] = False

# Simulate a popup for API key input during the start of the page
if not st.session_state["api_key_submitted"]:
    with st.form("api_key_form"):
        api_key = st.text_input("Enter your OpenAI API Key:", type="password")
        submitted = st.form_submit_button("Submit")

        # If the form is submitted, store the API key in the session state and hide the form
        if submitted and api_key:
            st.session_state["openai_api_key"] = api_key
            st.session_state["api_key_submitted"] = True
            st.success("API key saved successfully!")
            st.rerun()  # Reload the page to continue to the main content

# Once the API key is submitted, proceed with the main app logic
if st.session_state["api_key_submitted"] and st.session_state["openai_api_key"]:
    openai_api_key = st.session_state["openai_api_key"]

    # Title
    st.title("LawGlance")

    # Initialize the LLM and embeddings with the provided API key
    llm = OpenAI(temperature=0, openai_api_key=openai_api_key)
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)  # Explicitly pass the API key here
    vector_store = Chroma(persist_directory="chroma_db_legal_bot_part1", embedding_function=embeddings)
    retriever = vector_store.as_retriever(search_type="similarity")

    # Initialize session state for chat memory
    if "chat_memory" not in st.session_state:
        st.session_state.chat_memory = []  # Initialize chat memory in session state

    contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is. \
    If general greeting words or incomplete questions which are totally not related \
    to chat history then handle this in such a way that model doesn't formulate a wrong standalone question.
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

    qa_system_prompt = """You are a Legal Assistant for question-answering \
    tasks relating to Indian Laws. \
    Use the following pieces of retrieved context to answer the question. \
    If you don't know the answer, just say that you don't know. \
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
        output_messages_key="answer",
    )

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
        with st.chat_message("user"):
            st.markdown(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        query = prompt
        result_text = chat(query)["answer"]

        # Extract the text after "System:" from the AI's response
        if "System:" in result_text:
            result = result_text.split("System:")[1].strip()
        else:
            result = result_text  # If "System:" is not present, use the whole response

        def response_generator(result):
            response = random.choice([result])
            for word in response.split():
                yield word + " "
                time.sleep(0.05)

        final_response = f"AI Law Assistant: {result}"

        with st.chat_message("assistant"):
            response = st.write_stream(response_generator(final_response))

        st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.warning("Please enter your OpenAI API Key to continue.")
