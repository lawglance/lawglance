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
    """LLM , embedings and the vector store is the initial vaues neede while creating instance of the class"""
    self.llm = llm
    self.embeddings = embeddings
    self.vector_store = vector_store

  def __retriever(self):
    """The function to define the properties of retriever"""
    retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",search_kwargs={"k": 10, "score_threshold":0.3})
    return retriever
  
  def llm_answer_generator(self,query):
    """This function invokoes the functionality of conversational RAG"""
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
      """ You are Lawglance, an advanced legal AI assistant designed to provide precise and contextual legal insights based only on legal queries.

      Purpose
        Your purpose is to provide legal assistant and to democratize legal access.

      You are provided with some guidelines and core principles for answering legal queries:



    Current Legal Knowledge Domains :
      Indian Constitution
      Bharatiya Nyaya Sanhita, 2023 (BNS)
      Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
      Bharatiya Sakshya Adhiniyam, 2023 (BSA)
      Consumer Protection Act, 2019
      Motor Vehicles Act, 1988
      Information Technology Act, 2000
      The Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013
      The Protection of Children from Sexual Offences Act, 2012

Question : {input}

"""
    
    )
    qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", 
                """
             While Answering the question you should use only the given context.

              Guidelines for answering:
                1. Carefully analyze the input question if its worth a legal query answer based on the provided context else give a fallback message
                2. Scan the provided context systematically
                3. Identify most relevant legal sources
                4. Extract precise legal information
                5. Synthesize a concise, accurate response

              Core Principles:
              - Prioritize factual legal information from the provided context
              - Cite specific legal provisions when possible from the provided context
              - Ensure clarity and brevity in response
              - If no direct context exists, indicate knowledge limitation using a suitable fall back

              Reasoning Process:

                1. Question Understanding:
                  - What specific legal aspect is being inquired about?
                  - Which legal domain might be most relevant?

                2. Context Evaluation:
                  - Carefully analyze the provided context
                  - Identify sections/provisions directly addressing the question from the provided context

                3. Information Extraction:
                  - Extract most relevant legal provisions from the provided context based on the user question
                  - Highlight key legal principles or interpretations from the provided context

                4. Response Synthesis:
                  - Construct a precise, two to three sentence response from the provided context
                  - Ensure answer is grounded in the provided context

                Relevant Context:
                {context}

                Final Output Requirements:
                - Be concise (2-3 sentences max)
                - Use clear, professional legal language
                - Directly address the core of the question and to the point
                - If no relevant context exists, use a strategic fallback response

                When a user sends a greeting or non-legal query, craft a polite response that:
                - Acknowledges the greeting
                - Emphasizes your role as a legal assistant
                - Invites legal questions

                Respond only with the direct, concise answer.
                If no relevant context exists in the context provided, use a strategic fallback response
                like the project is in its pilot phase so soon it would be updates with broader laws

                """
                ),
            ]
        )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain

  def get_session_history(self,session_id: str) -> BaseChatMessageHistory:
    if session_id not in Lawglance.store:
        Lawglance.store[session_id] = ChatMessageHistory()
    return Lawglance.store[session_id]
  
  def conversational(self,query,session_id):
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
            "configurable": {"session_id": session_id}
        },
    )
    return(response['answer'])
