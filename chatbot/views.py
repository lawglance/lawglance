from django.shortcuts import render
import os
import random
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from django.http import JsonResponse
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_chroma import Chroma
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_retrieval_chain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# Load environment variables
load_dotenv()

# Initialize OpenAI(LLM) and Chroma(vector db)
openai_api_key = os.getenv('OPENAI_API_KEY')
llm = OpenAI(temperature=0.9, openai_api_key=openai_api_key, max_tokens=1200)
embeddings = OpenAIEmbeddings()
vector_store = Chroma(persist_directory="chroma_db_legal_bot_part1", embedding_function=embeddings)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 10})

# Chatbot view to handle the user interaction
def chatbot(request):
    if 'query_count' not in request.session:
        request.session['query_count'] = 0  # Initialize if it does not exist

    request.session['query_count'] += 1
   
    # If the request is a POST (user sent a message)
    if request.method == "POST":
        user_input = request.POST.get('message')

        # Add user message to session
        request.session['messages'].append({"role": "user", "content": user_input})
        request.session['query_count'] += 1  # Increment query count

        query = user_input
        system_prompt = (

            "You are a legal assistant  and your task is to answer queries relating to legal matters alone "
            "Use the following pieces of retrieved context to answer "
            "the question and ensure answer is complete sentence with proper casing and puctuations given. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise. Remember you have access to the legal database"
            "The answer should not contain any tags like ```\n```"
            "Ensure your answer contains the relevant content only not some words like ```System``` or ```Computer:``` etc"

            "{context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        response = rag_chain.invoke({"input": query})
        sources = {doc.metadata['source'] for doc in response['context']}
        src = "\n".join([f"Source: {source}" for source in sources])
        res = response["answer"].replace("\n", "").capitalize()
        result = res + "\n\n" + src

        # Create the final response
        final_response = f"AI Law Assistant: {result}"
        # Add assistant's response to the session
        request.session['messages'].append({"role": "assistant", "content": final_response})

        # Return the response as JSON (for AJAX handling)
        return JsonResponse({"response": final_response})

    # Check if the session is ending (optional, depends on your use case)
    if 'end_session' in request.GET:
        end_time = time.time()
        duration = end_time - request.session['start_time']

        # Create the session data to log
        session_data = {
            "session_start": str(datetime.fromtimestamp(request.session['start_time'])),
            "session_end": str(datetime.fromtimestamp(end_time)),
            "duration_seconds": round(duration),
            "query_count": request.session['query_count'],
            "ip_address": request.session['ip_address']
        }

        # Log the session data to a JSON file
        log_session_data(session_data)

        # Clear the session after logging
        request.session.flush()
        return JsonResponse({"message": "Session ended and logged."})

    # If it's a GET request, render the chat interface with the chat history
    return render(request, 'chatbot.html', {'messages': request.session['messages']})
