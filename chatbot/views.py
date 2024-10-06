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
# from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# Load environment variables
load_dotenv()

# Initialize OpenAI(LLM) and Chroma(vector db)
openai_api_key = os.getenv('OPENAI_API_KEY')
llm = OpenAI(temperature=0.9, openai_api_key=openai_api_key, max_tokens=1200)
embeddings = OpenAIEmbeddings()
vector_store = Chroma(persist_directory="chroma_db_legal_bot_part1", embedding_function=embeddings)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 10})


# Helper function to log session data to a JSON file
# def log_session_data(session_data):
#     log_dir = os.path.join(os.path.dirname(__file__), 'logs')
#
#     # Ensure the directory exists
#     if not os.path.exists(log_dir):
#         os.makedirs(log_dir)
#
#     log_file_path = os.path.join(log_dir, 'session_logs.json')
#
#     # Read the existing log file or create a new one if it doesn't exist
#     if os.path.exists(log_file_path):
#         with open(log_file_path, 'r') as log_file:
#             logs = json.load(log_file)
#     else:
#         logs = []
#
#     # Append the new session data to the log
#     logs.append(session_data)
#
#     # Write the updated logs back to the JSON file
#     with open(log_file_path, 'w') as log_file:
#         json.dump(logs, log_file, indent=4)
#

# Chatbot view to handle the user interaction
def chatbot(request):
    if 'query_count' not in request.session:
        request.session['query_count'] = 0  # Initialize if it does not exist

    request.session['query_count'] += 1
    # Handle the chat history stored in session
    # if 'messages' not in request.session:
    #     request.session['messages'] = []
    #     request.session['query_count'] = 0
    #     request.session['start_time'] = time.time()  # Track session start time
    #     request.session['ip_address'] = request.META.get('REMOTE_ADDR')  # Get user's IP address

    # If the request is a POST (user sent a message)
    if request.method == "POST":
        user_input = request.POST.get('message')

        # Add user message to session
        request.session['messages'].append({"role": "user", "content": user_input})
        request.session['query_count'] += 1  # Increment query count

        query = user_input

        # Retrieve relevant documents using Chroma
        # get_documents = retriever.invoke(user_input)
        # metadata = [doc.metadata for doc in get_documents]
        #
        # # Prepare the input for the AI assistant
        # combined_input = (
        #         "You are a lawyer assistant and you are provided with some documents with legal contents "
        #         + user_input
        #         + "\n\nRelevant Documents:\n"
        #         + "\n\n".join([doc.page_content for doc in get_documents])
        #         + "\n\nSource:\n"
        #
        #         + "\n\n" + ", ".join([f"{key}: {value}" for key, value in metadata[0].items()])
        #         + "\n\nPlease provide a very concise answer in a simple english language considering the above documents only and show the source.also in a concise way"
        #           "If the answer is not found, provide ```Hello, Please ask a relevant legal question.```."
        # )
        #
        # # Messages sent to OpenAI LLM
        # messages = [
        #     SystemMessage(content="""You are a helpful legal assistant who answers legal english questions in simple English language and ensure answer is not offensive.If you are provided with
        #         a question outside legal context reply ```Hello, Please ask a relevant legal question```
        #         and it is important to answer all questions based on relevant questions in English language
        #         whenever there is answers from greeting words just don't provide source
        #
        #           """),
        #     HumanMessage(content=combined_input)
        # ]
        # result = llm.invoke(messages)

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
