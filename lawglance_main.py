from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import ChatPromptTemplate
class Lawglance:
  def __init__(self,llm,embeddings,vector_store):
    self.llm = llm
    self.embeddings = embeddings
    self.vector_store = vector_store
  def retriever(self):
    retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",search_kwargs={"k": 10, "score_threshold":0.3})
    return retriever
  def llm_answer_generator(self,query):
    retriever=self.retriever()
    system_prompt = (
      "You are a helpful legal assistant who is tasked with answering to the question, which is: {input}")
    prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", """You are provided with some context with legal contents that might contain
        relevant sections or articles which can help you answer the question.
        Your task is to answer the question based on the context.
        You should ensure that question is answered based on the relavants parts from the context only.
        \n\nRelevant Context: \n"
        {context}

        You should return only the answer as output."""),
            ]
        )

    question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    response = rag_chain.invoke({"input": query})
    return(response['answer'])