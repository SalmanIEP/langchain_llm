from langchain_community.tools.playwright.utils import create_sync_playwright_browser
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentType
import time

# Custom wait tool
from langchain.tools import Tool
def wait_seconds(seconds_str: str) -> str:
    seconds = int(seconds_str)
    time.sleep(seconds)
    return f"Waited for {seconds} seconds"

wait_tool = Tool(
    name="wait",
    func=wait_seconds,
    description="Waits for the specified number of seconds. Input: number of seconds as a string."
)

def main():
    # 1. Create browser session (headless=False to see UI)
    browser = create_sync_playwright_browser(headless=False)

    # 2. Build LangChain toolkit
    toolkit = PlayWrightBrowserToolkit.from_browser(sync_browser=browser)
    tools = toolkit.get_tools()
    allowed_tool_names = {"navigate_browser", "click_element", "extract_text", "get_elements", "fill_input"}
    tools = [tool for tool in tools if tool.name in allowed_tool_names]
    tools.append(wait_tool)  # Add wait tool

    # 3. Load Ollama LLM
    llm = Ollama(model="llama3")

    # 4. Create LangChain agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    # 5. Provide natural language prompt
      # 5. Provide natural language prompt
    prompt = (
        "Navigate to Facebook login page and extract the selector for the login button"
    )
    result = agent.run(prompt)
    print("\n--- Agent Result ---\n", result)
if __name__ == "__main__":
    main()