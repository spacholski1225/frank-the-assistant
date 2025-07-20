from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from typing import Type, Optional, List
import os
from dotenv import load_dotenv

load_dotenv()


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "Useful for searching information on the internet when you need current information or facts about any topic"
    
    def __init__(self):
        super().__init__()
        self._search = DuckDuckGoSearchRun()
    
    def _run(self, query: str) -> str:
        try:
            results = self._search.run(query)
            return results
        except Exception as e:
            return f"Error during search: {str(e)}"
    
    def _arun(self, query: str):
        raise NotImplementedError("WebSearchTool does not support async")


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
            return_intermediate_steps=True
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
    
    def chat(self, message: str) -> str:
        """
        Simple chat interface for web search agent
        
        Args:
            message (str): User message/query
            
        Returns:
            str: Agent's response
        """
        result = self.search(message)
        return result["answer"]


def create_websearch_agent(model_name: str = "gpt-3.5-turbo") -> WebSearchAgent:
    """
    Factory function to create a web search agent
    
    Args:
        model_name (str): OpenAI model to use
        
    Returns:
        WebSearchAgent: Configured web search agent
    """
    return WebSearchAgent(model_name=model_name)