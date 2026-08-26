from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: list[str] = Field(description="Document name where the data is fetched")

class structured_output(BaseModel):
    answer: str = Field(description="Answer to the user query which is retrieved from the vector store.")
    
    source: Citation = Field(description="Sources that support the answer")

