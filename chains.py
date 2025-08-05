from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder

def get_rag_chain(llm, vector_store, system_prompt, qa_prompt):
    retriever = vector_store.as_retriever(search_type="similarity_score_threshold", search_kwargs={"k": 10, "score_threshold": 0.3})
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", "Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    qa_prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", qa_prompt),
    ])
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt_template)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain