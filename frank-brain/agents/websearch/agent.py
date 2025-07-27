from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from typing import Type, Optional, List
import os
from dotenv import load_dotenv
from .tools import WebSearchTool

load_dotenv()


class WebSearchAgent:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.tools = [WebSearchTool()]
        
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            max_iterations=3,  # Limit iterations to prevent timeout
            max_execution_time=30  # 30 second timeout
        )
    
    def search(self, query: str) -> dict:
        """
        Search for information based on user query
        
        Args:
            query (str): User's search query
            
        Returns:
            dict: Search results with answer and intermediate steps
        """
        try:
            result = self.agent.invoke({"input": query})
            
            return {
                "answer": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "success": True
            }
        except Exception as e:
            return {
                "answer": f"Error during search: {str(e)}",
                "intermediate_steps": [],
                "success": False
            }