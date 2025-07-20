from langchain.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun


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