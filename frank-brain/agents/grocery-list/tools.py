from langchain.tools import BaseTool
import requests
import json


class GroceryListTool(BaseTool):
    name: str = "grocery_list_converter"
    description: str = "Converts text to a grocery list using AI. Useful when you need to extract grocery items from any text input like recipes, shopping notes, or meal plans."
    
    def __init__(self, api_url: str = "http://100.77.2.1:8051/convert-text"):
        super().__init__()
        self.api_url = api_url
    
    def _run(self, text: str) -> str:
        try:
            payload = {"text": text}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                self.api_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                items = result.get("items", [])
                return f"Grocery list items extracted:\n" + "\n".join(f"- {item}" for item in items)
            else:
                return f"Error: API returned status {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The grocery list service may be unavailable."
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to grocery list service. Please ensure the service is running."
        except Exception as e:
            return f"Error during grocery list conversion: {str(e)}"
    
    def _arun(self, text: str):
        raise NotImplementedError("GroceryListTool does not support async")