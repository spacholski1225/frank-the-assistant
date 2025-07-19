from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from tools import add
import os

def setup_llm_from_env():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        openai_api_key=api_key,
        base_url=api_base
    )

    return llm

if __name__ == "__main__":
    agent_tools=[add]

    system_prompt = SystemMessage(
        """You are a Math genius who can solve math problems. Solve the
        problems provided by the user, by using only tools available. 
        Do not solve the problem yourself"""
    )

    agent_graph=create_react_agent(
        model=setup_llm_from_env(), 
        prompt=system_prompt,
        tools=agent_tools,
        debug=True)

    inputs = {"messages":[("user","what is the sum of 2 and 3 ?")]}

    result = agent_graph.invoke(inputs)

    print(f"Agent returned : {result['messages'][-1].content} \n")

    print("Step by Step execution : ")
    for message in result['messages']:
        print(message.pretty_repr())
