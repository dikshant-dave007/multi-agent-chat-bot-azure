"""
State schema for LangGraph multi-agent system.

This module defines the state structure that flows through the
LangGraph agent network, managing conversation history and routing.
"""

from typing import List, Literal, TypedDict, Optional


class Message(TypedDict):
    """Message structure for agent communication."""
    role: Literal["user", "assistant", "system"]
    content: str
    agent: Optional[str]  # Which agent generated this message


class AgentState(TypedDict):
    """
    State structure for multi-agent system.
    
    This TypedDict defines the state that flows through the
    LangGraph network and is shared across all agents.
    """
    # User input and conversation history
    messages: List[Message]
    
    # Extracted intent and entity information
    user_intent: str  # Type of request: greeting, research, facility, database
    user_query: str  # The actual user question/request
    
    # Results from agents
    current_agent: str  # Which agent is currently processing
    agent_response: Optional[str]  # Response from the current agent
    
    # Context and metadata
    conversation_id: str
    metadata: dict  # Additional context data
    
    # Final output
    final_response: Optional[str]  # Final response to user
