"""
Semantic Kernel-based orchestrator for multi-agent workflow.

This module replaces the LangGraph orchestrator with a cleaner,
Semantic Kernel-based approach using intelligent intent detection
and agent routing.
"""

from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

from semantic_kernel import Kernel
from langchain_openai import AzureChatOpenAI

from src.core.logging_config import LoggerMixin
from src.core.semantic_kernel_factory import SemanticKernelFactory
from src.core.cache_service import get_cache_service, CacheService
from src.core.config import get_settings
from src.agents.semantic_kernel_agents import (
    GreetingAgent,
    ResearcherAgent,
    EmailWriterAgent,
    DatabaseAgent,
    EventAndCelebrationAgent,
)


class IntentDetectionService:
    """Semantic Kernel-based intent detection using LLM."""
    
    def __init__(self):
        """Initialize intent detection service with LLM."""
        self.settings = get_settings()
        self._llm = AzureChatOpenAI(
            api_version=self.settings.azure_openai.api_version,
            azure_deployment=self.settings.azure_openai.deployment_name,
            azure_endpoint=self.settings.azure_openai.endpoint,
            api_key=self.settings.azure_openai.api_key,
            temperature=0.3,  # Lower temperature for consistency
        )
    
    async def classify_intent(self, query: str) -> str:
        """
        Classify the intent of a user query using LLM.
        
        Args:
            query: User query
            
        Returns:
            Intent type: 'greeting', 'research', 'email', 'database', or 'celebration'
        """
        intent_prompt = f"""You are an expert intent classifier. Your task is to classify user messages into exactly ONE category.

User Message: "{query}"

CLASSIFICATION RULES - Apply in this order:
1. 'greeting' - ONLY Simple greetings, small talk, or conversation starters (no other activities mentioned)
   Examples: "Hello", "Hi", "Hey", "How are you?", "Good morning", "What's up?", "Nice to meet you"
   
2. 'database' - Requests about employee data, staff information, company records, or any database operations
   Examples: "Who is John?", "List employees", "Show me John's details", "Get 5 random employees", "Employee EMP123 details", "Add new employee", "Delete employee EMP123"
   
3. 'celebration' - Requests to create celebration posts, announcements, wishes for birthdays, anniversaries, promotions, achievements, festivals, events
   Keywords: "create post", "birthday post", "celebration", "anniversary", "promotion", "achievement", "festival", "congratulate", "celebrate", "wish", "announce celebration"
   Examples: "Create a birthday post for John", "Announce promotion for Sarah", "Celebrate team achievement", "Write birthday wishes", "Create Diwali celebration post"
   IMPORTANT: If user mentions "post", "celebration", "birthday", "anniversary", "festival", "achievement" - classify as 'celebration' NOT 'email'
   
4. 'email' - ONLY requests that explicitly mention "email" or "letter" in the context of writing/composing/drafting
   Keywords: "write email", "compose email", "draft email", "send email", "email to", "write a letter", "compose letter"
   Examples: "Write an email to manager", "Compose email for meeting request", "Draft email about project update", "Send email to team"
   IMPORTANT: Must explicitly say "email" or "letter" - if it says "post", "wishes", "announcement" it's NOT email
   
5. 'research' - Requests for information, explanations, research, or knowledge about topics
   Examples: "Tell me about AI", "Explain machine learning", "What is Python?", "How does blockchain work?"

CRITICAL DISTINCTION:
- "create a birthday POST" = celebration (NOT email)
- "write birthday WISHES" = celebration (NOT email)
- "create celebration ANNOUNCEMENT" = celebration (NOT email)
- "write an EMAIL for birthday" = email (explicitly mentions email)
- "compose EMAIL about celebration" = email (explicitly mentions email)

IMPORTANT RULES:
- If user says "post", "wishes", "announcement", "celebrate" → celebration
- ONLY classify as 'email' if the word "email" or "letter" is explicitly mentioned
- If the message is ONLY a greeting and nothing else, classify as 'greeting'
- Return ONLY ONE word in lowercase: greeting, email, database, celebration, or research
- Do NOT include explanations, examples, or any other text

Your response:"""
        
        try:
            response = await self._llm.ainvoke([
                {"role": "system", "content": "You are a precise intent classifier. CRITICAL: Only classify as 'email' if the word 'email' or 'letter' is explicitly mentioned. If user says 'post', 'wishes', 'celebration', 'announcement' classify as 'celebration' NOT 'email'. Return only the category name in lowercase."},
                {"role": "user", "content": intent_prompt}
            ])
            
            intent = response.content.strip().lower()
            
            # Validate intent is one of the expected values
            valid_intents = ["greeting", "research", "email", "database", "celebration"]
            if intent in valid_intents:
                return intent
            
            # Fallback to research if response is unexpected
            return "research"
        
        except Exception as e:
            # Fallback to research on error
            return "research"


class SemanticKernelOrchestrator(LoggerMixin):
    """
    Semantic Kernel-based multi-agent orchestrator.
    
    This orchestrator:
    1. Uses Semantic Kernel for intent detection
    2. Routes to appropriate agent based on intent
    3. Manages conversation context
    4. Implements caching for performance
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.kernel_factory = SemanticKernelFactory()
        self.kernel = self.kernel_factory.create_kernel()
        
        # Initialize intent detection service (LLM-based)
        self.intent_service = IntentDetectionService()
        
        # Initialize agents
        self.greeting_agent = GreetingAgent()
        self.researcher_agent = ResearcherAgent()
        self.email_agent = EmailWriterAgent()
        self.database_agent = DatabaseAgent()
        self.celebration_agent = EventAndCelebrationAgent()
        
        # Initialize cache
        self.cache = get_cache_service()
        
        # Agent mapping
        self.agents = {
            "greeting": self.greeting_agent,
            "research": self.researcher_agent,
            "email": self.email_agent,
            "database": self.database_agent,
            "celebration": self.celebration_agent,
        }
        
        self.logger.info("semantic_kernel_orchestrator_initialized")
    
    async def _detect_intent(self, query: str) -> str:
        """
        Detect user intent with caching using LLM.
        
        Args:
            query: User query
            
        Returns:
            Detected intent
        """
        # Check cache
        cached_intent = await self.cache.get_intent(query)
        if cached_intent:
            self.logger.debug("using_cached_intent", query=query[:50])
            return cached_intent["intent"]
        
        # Classify intent using LLM
        intent = await self.intent_service.classify_intent(query)
        
        # Cache the result
        await self.cache.set_intent(query, intent, confidence=1.0, ttl_minutes=60)
        
        self.logger.info(
            "intent_detected",
            intent=intent,
            query=query[:100]
        )
        
        return intent
    
    async def process_request(
        self,
        user_query: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user request through the multi-agent system.
        
        Args:
            user_query: The user's input query
            conversation_id: Optional conversation ID for tracking
            
        Returns:
            Dictionary with final response and metadata
        """
        # Create conversation ID if not provided
        if conversation_id is None:
            conversation_id = str(uuid4())
        
        request_id = str(uuid4())
        
        self.logger.info(
            "processing_request",
            conversation_id=conversation_id,
            request_id=request_id,
            query=user_query[:100]
        )
        
        try:
            # Detect intent
            intent = await self._detect_intent(user_query)
            
            # Check cache for complete response
            cached_response = await self.cache.get_response(
                agent_type=intent,
                query=user_query
            )
            
            if cached_response:
                self.logger.info("using_cached_response", intent=intent)
                return {
                    "success": True,
                    "conversation_id": conversation_id,
                    "request_id": request_id,
                    "user_query": user_query,
                    "intent": intent,
                    "agent": f"{intent.capitalize()}Agent",
                    "response": cached_response["response"],
                    "messages": [
                        {
                            "role": "user",
                            "content": user_query,
                            "agent": None
                        },
                        {
                            "role": "assistant",
                            "content": cached_response["response"],
                            "agent": f"{intent.capitalize()}Agent"
                        }
                    ],
                    "timestamp": datetime.utcnow().isoformat(),
                    "from_cache": True,
                }
            
            # Route to appropriate agent
            agent = self.agents.get(intent)
            
            if not agent:
                return {
                    "success": False,
                    "conversation_id": conversation_id,
                    "request_id": request_id,
                    "user_query": user_query,
                    "intent": intent,
                    "error": f"No agent found for intent: {intent}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            # Execute agent
            agent_response = await agent.process(
                query=user_query,
                conversation_id=conversation_id
            )
            
            # Cache the response
            await self.cache.set_response(
                agent_type=intent,
                query=user_query,
                response=agent_response,
                ttl_minutes=30
            )
            
            self.logger.info(
                "request_processed_successfully",
                conversation_id=conversation_id,
                request_id=request_id,
                intent=intent,
                agent=type(agent).__name__
            )
            
            # Return formatted response
            return {
                "success": True,
                "conversation_id": conversation_id,
                "request_id": request_id,
                "user_query": user_query,
                "intent": intent,
                "agent": type(agent).__name__,
                "response": agent_response,
                "messages": [
                    {
                        "role": "user",
                        "content": user_query,
                        "agent": None
                    },
                    {
                        "role": "assistant",
                        "content": agent_response,
                        "agent": type(agent).__name__
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "from_cache": False,
            }
        
        except Exception as e:
            self.logger.error(
                "request_processing_failed",
                conversation_id=conversation_id,
                request_id=request_id,
                error=str(e),
                exc_info=True
            )
            
            return {
                "success": False,
                "conversation_id": conversation_id,
                "request_id": request_id,
                "user_query": user_query,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# Global orchestrator instance
_orchestrator: Optional[SemanticKernelOrchestrator] = None


def get_semantic_kernel_orchestrator() -> SemanticKernelOrchestrator:
    """
    Get or create the global Semantic Kernel orchestrator instance.
    
    Returns:
        SemanticKernelOrchestrator: The orchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SemanticKernelOrchestrator()
    return _orchestrator
