from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain.schema import SystemMessage, HumanMessage
import os
import streamlit as st
import random
import time


st.title("Niyam Saha-AI")
load_dotenv()

openai_api_key =os.getenv('OPENAI_API_KEY') # please type your OPENAI API KEY
llm = OpenAI(temperature=0, openai_api_key = openai_api_key, max_tokens=1200)
embeddings = OpenAIEmbeddings()
vector_store = Chroma(persist_directory="chroma_db_legal_bot_part1", embedding_function=embeddings)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k" : 2})


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
    get_documents = retriever.invoke(query)
    metadata = [doc.metadata for doc in get_documents]
    
    combined_input = (
        "You are an lawyer assistant and you are provided with some documents with legal contents that might contain relevant sections or articles which can help you answer the question  and revalidate the sections carefully: "
        +query
        +"\n\nRelevant Documents: \n"
        + "\n\n".join([doc.page_content for doc in get_documents])
        + "\n\nSource: \n"
        + "\n\n"+", ".join([f"{key}: {value}" for key, value in metadata[0].items()])
        + "\n\n Please provide an answer considering the above documents only and also show the source. If the answer is not found, provide ''' Content Not found''' "
    )



    messages = [
        SystemMessage(content ="You are a helpful assistant who answers based on the combined input alone"),
        HumanMessage(content = combined_input)
    ]

    result = llm.invoke(messages)

    
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


        
 
