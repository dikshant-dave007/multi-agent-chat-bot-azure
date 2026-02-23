"""
Semantic Kernel-based agent implementations.

This module contains five specialized agents that replace the LangGraph agents:
1. Greeting Agent - Handles user greetings
2. Researcher Agent - Researches topics using LLM and knowledge
3. Email Agent - Writes professional emails
4. Database Agent - CRUD operations on Cosmos DB
5. Event and Celebration Agent - Creates celebration posts and manages special occasions
"""

import json
import re
import uuid
import random
from typing import Optional
from abc import ABC, abstractmethod

from semantic_kernel import Kernel
from langchain_openai import AzureChatOpenAI

from src.core.config import get_settings
from src.core.logging_config import LoggerMixin
from src.core.semantic_kernel_factory import SemanticKernelFactory


class BaseSemanticAgent(ABC, LoggerMixin):
    """Base class for Semantic Kernel agents."""
    
    def __init__(self, agent_name: str):
        """
        Initialize base agent.
        
        Args:
            agent_name: Name of the agent
        """
        self.agent_name = agent_name
        self.settings = get_settings()
        self._kernel: Optional[Kernel] = None
        self._llm: Optional[AzureChatOpenAI] = None
        
        self.logger.info(f"initialized_{agent_name}")
    
    @property
    def kernel(self) -> Kernel:
        """Get or create Semantic Kernel instance."""
        if self._kernel is None:
            kernel_factory = SemanticKernelFactory()
            self._kernel = kernel_factory.create_kernel()
        return self._kernel
    
    @property
    def llm(self) -> AzureChatOpenAI:
        """Get or create Azure Chat OpenAI LLM instance."""
        if self._llm is None:
            self._llm = AzureChatOpenAI(
                api_version=self.settings.azure_openai.api_version,
                azure_deployment=self.settings.azure_openai.deployment_name,
                azure_endpoint=self.settings.azure_openai.endpoint,
                api_key=self.settings.azure_openai.api_key,
                temperature=0.7,
            )
        return self._llm
    
    @abstractmethod
    async def process(self, query: str, conversation_id: str) -> str:
        """
        Process user query and return response.
        
        Args:
            query: User query
            conversation_id: Conversation ID for context
            
        Returns:
            Agent response
        """
        pass


class GreetingAgent(BaseSemanticAgent):
    """Agent for handling user greetings."""
    
    def __init__(self):
        """Initialize greeting agent."""
        super().__init__("GreetingAgent")
    
    async def process(self, query: str, conversation_id: str) -> str:
        """
        Process user greeting and return a warm response.
        
        Args:
            query: User query
            conversation_id: Conversation ID
            
        Returns:
            Greeting response
        """
        self.logger.info("processing_greeting", query=query[:50])
        
        # Generate a warm greeting response
        greeting_prompt = f"""You are a friendly and professional virtual assistant.
The user has greeted you with: "{query}"

Respond with a warm, welcoming greeting. Be personable and ask how you can help them.
Keep the response to 1-2 sentences."""
        
        try:
            response = await self.llm.ainvoke([
                {"role": "system", "content": "You are a friendly virtual assistant."},
                {"role": "user", "content": greeting_prompt}
            ])
            
            result = response.content
            self.logger.info("greeting_processed_successfully")
            return result
        
        except Exception as e:
            error_msg = f"Greeting processing error: {str(e)}"
            self.logger.error("greeting_processing_failed", error=str(e))
            return error_msg


class ResearcherAgent(BaseSemanticAgent):
    """Agent for researching topics and providing information."""
    
    def __init__(self):
        """Initialize researcher agent."""
        super().__init__("ResearcherAgent")
    
    async def process(self, query: str, conversation_id: str) -> str:
        """
        Research a topic and provide information.
        
        Args:
            query: User query
            conversation_id: Conversation ID
            
        Returns:
            Research findings
        """
        self.logger.info("processing_research", query=query[:50])
        
        research_prompt = f"""You are a research expert with deep knowledge across multiple domains.

The user is asking for research on: {query}

Please provide a comprehensive but concise research summary including:
- Key information about the topic
- Recent developments (if applicable)
- Important facts and statistics
- Relevant insights
- Practical implications

Keep the response to 2-3 paragraphs maximum and make it informative and well-structured."""
        
        try:
            response = await self.llm.ainvoke([
                {"role": "system", "content": "You are a research expert. Provide accurate, well-researched, and insightful information."},
                {"role": "user", "content": research_prompt}
            ])
            
            result = response.content
            self.logger.info("research_completed_successfully")
            return result
        
        except Exception as e:
            error_msg = f"Research error: {str(e)}"
            self.logger.error("research_processing_failed", error=str(e))
            return error_msg


class EmailWriterAgent(BaseSemanticAgent):
    """Agent for writing professional emails."""
    
    def __init__(self):
        """Initialize email writer agent."""
        super().__init__("EmailWriterAgent")
    
    async def process(self, query: str, conversation_id: str) -> str:
        """
        Write a professional email based on user request.
        
        Args:
            query: User requirements for the email
            conversation_id: Conversation ID
            
        Returns:
            Composed email
        """
        self.logger.info("processing_email", query=query[:50])
        
        email_prompt = f"""You are a professional email writer with expertise in business communication.

User Request: {query}

Write a professional email with:
- Clear and professional subject line
- Appropriate greeting
- Well-structured body with clear points
- Professional closing with signature placeholder
- Proper formatting

The email should be polished, concise, and appropriate for a business context."""
        
        try:
            response = await self.llm.ainvoke([
                {"role": "system", "content": "You are an expert email writer. Create professional, well-structured emails that are clear, concise, and effective."},
                {"role": "user", "content": email_prompt}
            ])
            
            result = response.content
            self.logger.info("email_composed_successfully")
            return result
        
        except Exception as e:
            error_msg = f"Email writing error: {str(e)}"
            self.logger.error("email_processing_failed", error=str(e))
            return error_msg


class DatabaseAgent(BaseSemanticAgent):
    """Agent for CRUD operations on Cosmos DB."""
    
    def __init__(self):
        """Initialize database agent."""
        super().__init__("DatabaseAgent")
        self._cosmos_client = None
    
    async def _initialize_cosmos(self):
        """Initialize Cosmos DB client."""
        if self._cosmos_client is not None:
            return
        
        try:
            from azure.cosmos import CosmosClient
            from azure.identity import DefaultAzureCredential
            
            cosmos_settings = self.settings.cosmos_db
            
            # Initialize client
            if cosmos_settings.key:
                self._cosmos_client = CosmosClient(cosmos_settings.endpoint, cosmos_settings.key)
            else:
                credential = DefaultAzureCredential()
                self._cosmos_client = CosmosClient(cosmos_settings.endpoint, credential)
        except Exception as e:
            self.logger.error("cosmos_db_initialization_failed", error=str(e))
            self._cosmos_client = None
    
    async def _get_container(self):
        """Get Cosmos DB container client."""
        try:
            await self._initialize_cosmos()
            if self._cosmos_client is None:
                return None
            
            cosmos_settings = self.settings.cosmos_db
            database = self._cosmos_client.get_database_client(cosmos_settings.database_name)
            container = database.get_container_client("employees")
            return container
        except Exception as e:
            self.logger.error("get_container_failed", error=str(e))
            return None
    
    async def _list_all_employees(self) -> list:
        """Retrieve all employees from database."""
        try:
            container = await self._get_container()
            if container is None:
                return []
            
            query = "SELECT * FROM c"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            self.logger.error("list_employees_failed", error=str(e))
            return []
    
    async def _retrieve_employee(self, employee_id: str) -> Optional[dict]:
        """Retrieve a specific employee by ID."""
        try:
            container = await self._get_container()
            if container is None:
                return None
            
            # Query for specific employee
            query = f"SELECT * FROM c WHERE c.Employee_ID = '{employee_id}'"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
        except Exception as e:
            self.logger.error("retrieve_employee_failed", error=str(e), employee_id=employee_id)
            return None
    
    async def _retrieve_by_criteria(self, criteria: dict) -> list:
        """Retrieve employees by specific criteria."""
        try:
            container = await self._get_container()
            if container is None:
                return []
            
            # Build WHERE clause from criteria
            where_clauses = []
            for key, value in criteria.items():
                where_clauses.append(f"c.{key} = '{value}'")
            
            where_clause = " AND ".join(where_clauses) if where_clauses else ""
            query = f"SELECT * FROM c WHERE {where_clause}" if where_clause else "SELECT * FROM c"
            
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            self.logger.error("retrieve_by_criteria_failed", error=str(e))
            return []
    
    async def _create_employee(self, employee_data: dict) -> bool:
        """Create a new employee record."""
        try:
            container = await self._get_container()
            if container is None:
                return False
            
            # Ensure id field exists for Cosmos DB
            if "id" not in employee_data:
                employee_data["id"] = employee_data.get("Employee_ID", str(uuid.uuid4()))
            
            container.create_item(body=employee_data)
            self.logger.info("employee_created_successfully", employee_id=employee_data.get("Employee_ID"))
            return True
        except Exception as e:
            self.logger.error("create_employee_failed", error=str(e))
            return False
    
    async def _update_employee(self, employee_id: str, update_data: dict) -> bool:
        """Update an existing employee record."""
        try:
            container = await self._get_container()
            if container is None:
                return False
            
            # Retrieve existing employee
            existing = await self._retrieve_employee(employee_id)
            if not existing:
                self.logger.warning("employee_not_found_for_update", employee_id=employee_id)
                return False
            
            # Merge updates with existing data
            updated_employee = {**existing, **update_data}
            
            # Replace the item
            container.replace_item(item=updated_employee["id"], body=updated_employee)
            self.logger.info("employee_updated_successfully", employee_id=employee_id)
            return True
        except Exception as e:
            self.logger.error("update_employee_failed", error=str(e), employee_id=employee_id)
            return False
    
    async def _delete_employee(self, employee_id: str) -> bool:
        """Delete an employee record."""
        try:
            container = await self._get_container()
            if container is None:
                return False
            
            # Retrieve employee to get the id
            existing = await self._retrieve_employee(employee_id)
            if not existing:
                self.logger.warning("employee_not_found_for_delete", employee_id=employee_id)
                return False
            
            # Delete the item
            container.delete_item(item=existing["id"], partition_key=existing.get("id"))
            self.logger.info("employee_deleted_successfully", employee_id=employee_id)
            return True
        except Exception as e:
            self.logger.error("delete_employee_failed", error=str(e), employee_id=employee_id)
            return False
    
    async def process(self, query: str, conversation_id: str) -> str:
        """
        Process database operations (CRUD) based on user query using LLM.
        
        Args:
            query: User query
            conversation_id: Conversation ID
            
        Returns:
            Operation result
        """
        self.logger.info("processing_database_operation", query=query[:50])
        
        try:
            # Use LLM to determine the operation type and parameters
            operation_prompt = f"""Analyze this database operation request and determine what to do.

User Request: "{query}"

Determine the operation type and respond with a JSON object containing:
{{"operation": "list|retrieve|retrieve_criteria|retrieve_random|create|update|delete", "employee_id": "...", "criteria": {{}}, "data": {{}}, "limit": null}}

- "list": List all employees (no parameters needed)
- "retrieve": Get a specific employee by ID (extract employee_id from request like "EMP123", "John", or employee name)
- "retrieve_criteria": Find employees matching criteria (e.g., Department, Position) 
- "retrieve_random": Get random N employees (extract limit from request like "5 random employees")
- "create": Create a new employee (requires data dict)
- "update": Update an employee (requires employee_id and data dict)
- "delete": Delete an employee (requires employee_id)

IMPORTANT EXTRACTION RULES:
- For "retrieve" operations: Extract employee ID from queries like "show me John details", "employee EMP123", "John's information", etc. Try to match Employee_ID format or employee names.
- For "retrieve_random": Extract the number from phrases like "5 random employees", "give me 3 employees", etc. Default to 5 if not specified.
- For "retrieve_criteria": Extract key-value pairs like department, position, location, etc.

Return ONLY the JSON object, no other text. Make sure limit is a number for retrieve_random operations."""
            
            # Get operation details from LLM
            llm_response = await self.llm.ainvoke([
                {"role": "system", "content": "You are a database operation analyzer. Extract employee IDs, criteria, and limits carefully. Return only valid JSON without any markdown formatting or explanation."},
                {"role": "user", "content": operation_prompt}
            ])
            
            # Parse the response
            response_text = llm_response.content.strip()
            # Extract JSON if wrapped in text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                operation_details = json.loads(json_match.group())
            else:
                operation_details = json.loads(response_text)
            
            operation = operation_details.get("operation", "list")
            
            # Execute appropriate operation
            if operation == "list":
                employees = await self._list_all_employees()
                if not employees:
                    return "No employee records found in the database."
                return self._format_employees(employees)
            
            elif operation == "retrieve":
                employee_id = operation_details.get("employee_id")
                if not employee_id:
                    return "Employee ID is required for retrieve operation. Please specify the employee ID or name."
                
                # Try to find employee by ID first
                employee = await self._retrieve_employee(employee_id)
                
                # If not found by ID, try to find by name
                if not employee:
                    employees = await self._list_all_employees()
                    for emp in employees:
                        if emp.get("Name", "").lower() == employee_id.lower():
                            employee = emp
                            break
                
                if not employee:
                    return f"Employee with ID or name '{employee_id}' not found in the database."
                return self._format_employee_detail(employee)
            
            elif operation == "retrieve_criteria":
                criteria = operation_details.get("criteria", {})
                if not criteria:
                    return "No search criteria provided."
                employees = await self._retrieve_by_criteria(criteria)
                if not employees:
                    return f"No employees found matching criteria: {criteria}"
                return self._format_employees(employees)
            
            elif operation == "retrieve_random":
                limit = operation_details.get("limit", 5)
                try:
                    limit = int(limit) if limit else 5
                except (ValueError, TypeError):
                    limit = 5
                
                employees = await self._list_all_employees()
                if not employees:
                    return "No employee records found in the database."
                
                if len(employees) <= limit:
                    return self._format_employees(employees)
                
                random_employees = random.sample(employees, limit)
                return self._format_employees(random_employees)
            
            elif operation == "create":
                data = operation_details.get("data", {})
                if not data:
                    return "No employee data provided for creation."
                success = await self._create_employee(data)
                if success:
                    return f"Employee created successfully: {data.get('Name', 'Unknown')}"
                else:
                    return "Failed to create employee record."
            
            elif operation == "update":
                employee_id = operation_details.get("employee_id")
                data = operation_details.get("data", {})
                if not employee_id or not data:
                    return "Employee ID and update data are required for update operation."
                success = await self._update_employee(employee_id, data)
                if success:
                    return f"Employee {employee_id} updated successfully."
                else:
                    return f"Failed to update employee {employee_id}."
            
            elif operation == "delete":
                employee_id = operation_details.get("employee_id")
                if not employee_id:
                    return "Employee ID is required for delete operation."
                success = await self._delete_employee(employee_id)
                if success:
                    return f"Employee {employee_id} deleted successfully."
                else:
                    return f"Failed to delete employee {employee_id}."
            
            else:
                return f"Unknown operation type: {operation}"
        
        except json.JSONDecodeError as e:
            self.logger.error("json_parsing_failed", error=str(e))
            return "Failed to parse operation details. Please rephrase your request."
        except Exception as e:
            self.logger.error("database_operation_failed", error=str(e))
            return f"Database operation error: {str(e)}. Please try again."
    
    def _format_employees(self, employees: list) -> str:
        """Format list of employees for display with proper markdown."""
        if not employees:
            return "No employees to display."
        
        formatted = "### 👥 Employee List\n\n"
        
        for i, emp in enumerate(employees, 1):
            name = emp.get("Name", "Unknown")
            employee_id = emp.get("Employee_ID", "N/A")
            position = emp.get("Position", "N/A")
            department = emp.get("Department", "N/A")
            age = emp.get("Age", "N/A")
            
            formatted += f"**{i}. {name}** `{employee_id}`\n"
            formatted += f"   - 💼 Position: {position}\n"
            formatted += f"   - 🏢 Department: {department}\n"
            formatted += f"   - 👤 Age: {age}\n\n"
        
        formatted += f"**Total Employees: {len(employees)}**"
        return formatted
    
    def _format_employee_detail(self, employee: dict) -> str:
        """Format single employee for detailed display with proper markdown."""
        name = employee.get("Name", "Unknown")
        employee_id = employee.get("Employee_ID", "N/A")
        
        formatted = f"### 👤 Employee Details: {name}\n\n"
        formatted += f"**Employee ID:** `{employee_id}`\n\n"
        
        # Organize information in readable sections
        formatted += "#### 📋 Basic Information\n"
        formatted += f"- **Name:** {employee.get('Name', 'N/A')}\n"
        formatted += f"- **Age:** {employee.get('Age', 'N/A')}\n"
        formatted += f"- **Employee ID:** {employee_id}\n\n"
        
        formatted += "#### 💼 Professional Information\n"
        formatted += f"- **Position:** {employee.get('Position', 'N/A')}\n"
        formatted += f"- **Department:** {employee.get('Department', 'N/A')}\n"
        formatted += f"- **Date of Joining:** {employee.get('Date_of_Joining', 'N/A')}\n\n"
        
        # Add any additional fields
        formatted += "#### 📝 Additional Information\n"
        additional_fields = {}
        for key, value in employee.items():
            if key not in ["Name", "Age", "Employee_ID", "Position", "Department", "Date_of_Joining", "id", "_rid", "_self", "_etag", "_attachments", "_ts"]:
                additional_fields[key] = value
        
        if additional_fields:
            for key, value in additional_fields.items():
                # Format key names nicely
                readable_key = key.replace("_", " ").title()
                formatted += f"- **{readable_key}:** {value}\n"
        else:
            formatted += "- No additional information available\n"
        
        return formatted


class EventAndCelebrationAgent(BaseSemanticAgent):
    """Agent for creating celebration posts and managing special occasions at Yash Technologies."""
    
    def __init__(self):
        """Initialize event and celebration agent."""
        super().__init__("EventAndCelebrationAgent")
    
    async def process(self, query: str, conversation_id: str) -> str:
        """
        Create personalized celebration posts and manage special occasions.
        
        Args:
            query: User request for celebration post or event announcement
            conversation_id: Conversation ID
            
        Returns:
            Celebration post or event announcement
        """
        self.logger.info("processing_celebration", query=query[:50])
        
        celebration_prompt = f"""You are the Yash Technologies Event and Celebration Agent, designed to celebrate employee milestones and create a vibrant workplace culture.

User Request: {query}

Your task is to create a personalized, warm, and celebratory response. Follow these guidelines:

**Celebration Categories:**
- Birthdays: Fun, cheerful, personalized wishes
- Work Anniversaries: Professional, appreciative, highlighting contributions
- Marriage Anniversaries: Warm, respectful, family-focused
- New Joiners: Welcoming, informative, team-oriented
- Promotions: Congratulatory, motivational, achievement-focused
- Achievements: Proud, inspirational, team-celebrating
- Farewells/Retirements: Heartfelt, grateful, best wishes for future
- Festivals: Inclusive, joyful, culturally appropriate
- Team Events: Exciting, engaging, detail-oriented

**Tone and Style:**
- Be warm, cheerful, enthusiastic, and celebratory
- Use positive and uplifting language
- Personalize messages with employee details when provided
- Be inclusive and culturally sensitive
- Match the tone to the occasion

**Rules:**
1. Always maintain a positive and celebratory tone
2. Be culturally sensitive and inclusive
3. Use appropriate emojis to make posts engaging (but not excessive)
4. Keep posts concise yet meaningful (100-150 words for social posts)
5. For sensitive occasions (farewells, retirements), be respectful and heartfelt
6. Never include age in birthday posts unless specifically requested
7. Include company values and culture in celebration messages when appropriate

**Post Structure:**
- Start with an engaging opening
- Mention the person/team being celebrated
- Highlight their contributions or significance
- Add a personal touch or fun fact (if available)
- End with well-wishes or call to action
- Include relevant hashtags and emojis

If the request includes specific details (name, department, years of service, achievements), incorporate them naturally into the post.

If the request is about creating a post, provide:
1. Main celebration post (formatted and ready to share)
2. Posting channel recommendations (Teams, email, notice board)
3. Optional image suggestions or themes

Be creative, warm, and make every employee feel valued and appreciated."""
        
        try:
            response = await self.llm.ainvoke([
                {"role": "system", "content": "You are the Yash Technologies Event and Celebration Agent. Create warm, personalized, and celebratory messages that make employees feel valued. Use emojis appropriately for engagement."},
                {"role": "user", "content": celebration_prompt}
            ])
            
            result = response.content
            self.logger.info("celebration_post_created_successfully")
            return result
        
        except Exception as e:
            error_msg = f"Celebration post creation error: {str(e)}"
            self.logger.error("celebration_processing_failed", error=str(e))
            return error_msg
