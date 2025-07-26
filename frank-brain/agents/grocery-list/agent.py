from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from typing import Type, Optional, List
import os
from dotenv import load_dotenv
from .tools import GroceryListTool

load_dotenv()


class GroceryListAgent:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1, api_url: str = "http://100.77.2.1:8051/convert-text"):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.tools = [GroceryListTool(api_url=api_url)]
        
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
    
    def convert_text_to_grocery_list(self, text: str) -> dict:
        """
        Convert text to a grocery list using AI
        
        Args:
            text (str): Text containing information about groceries, recipes, or shopping needs
            
        Returns:
            dict: Results with grocery list and intermediate steps
        """
        try:
            query = f"Convert this text to a grocery list: {text}"
            result = self.agent.invoke({"input": query})
            
            return {
                "grocery_list": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "success": True
            }
        except Exception as e:
            return {
                "grocery_list": f"Error during conversion: {str(e)}",
                "intermediate_steps": [],
                "success": False
            }