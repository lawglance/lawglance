#adding necessary imports
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

#This Class delas with working of Chatbot

class Lawglance: 
  """This is the class which deals mainly with a conversational RAG
    It takes llm, embeddings and vector store as input to initialise.

    create an instance of it using law = LawGlance(llm,embeddings,vectorstore)
    In order to run the instance

    law.conversational(query)

    Example:
    law = LawGlance(llm,embeddings,vectorstore)
    query1 = "What is rule of Law?"
    law.conversational(query1)
    query2 = "Is it applicable in India?"
    law.conversational(query2)
  """
  store = {}

  def __init__(self,llm,embeddings,vector_store):
    self.llm = llm
    self.embeddings = embeddings
    self.vector_store = vector_store

  def __retriever(self):
    """The function to define the properties of retriever"""
    retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",search_kwargs={"k": 10, "score_threshold":0.3})
    return retriever
  
  def llm_answer_generator(self,query):
    llm = self.llm
    retriever = self.__retriever()
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )
    system_prompt = (
      "You are a helpful legal assistant who is tasked with answering to the question, which is: {input}")
    qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", """You are provided with some context with legal contents that might contain
        relevant sections or articles which can help you answer the question.
        Your task is to answer the question based on the context.
        You should ensure that question is answered based on the relavants parts from the context only.
        \n\nRelevant Context: \n"
        {context}

        You should return only the answer as output."""),
            ]
        )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain

  def get_session_history(self,session_id: str) -> BaseChatMessageHistory:
    if session_id not in Lawglance.store:
        Lawglance.store[session_id] = ChatMessageHistory()
    return Lawglance.store[session_id]
  
  def conversational(self,query):
    rag_chain = self.llm_answer_generator(query)
    get_session_history = self.get_session_history
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer")
    response = conversational_rag_chain.invoke(
        {"input": query},
        config={
            "configurable": {"session_id": "abc123"}
        },
    )
    return(response['answer'])
