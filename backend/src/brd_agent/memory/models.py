from typing import Literal

from pydantic import BaseModel, Field


class EpisodicMemory(BaseModel):
    category: Literal["episodic"]
    content: str = Field(description="A specific project event, decision, or outcome.")


class SemanticMemory(BaseModel):
    category: Literal["semantic"]
    content: str = Field(description="A stable project fact, term, or constraint.")


class ProceduralMemory(BaseModel):
    category: Literal["procedural"]
    content: str = Field(description="A project workflow rule or user preference.")
