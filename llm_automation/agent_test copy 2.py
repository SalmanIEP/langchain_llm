from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import init_chat_model
from langchain.tools import Tool
from langchain_community.tools.playwright.utils import create_sync_playwright_browser
import time
import getpass
import os

if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

def get_html(page) -> str:
    try:
        return page.content()
    except Exception as e:
        return f"Error getting HTML: {e}"

def get_all_elements(page, tag: str = "*") -> str:
    try:
        return page.content()
    except Exception as e:
        return f"Error getting HTML: {e}"

def wait_seconds(seconds_str: str) -> str:
    seconds = int(seconds_str)
    time.sleep(seconds)
    return f"Waited for {seconds} seconds"

def navigate(page, url: str) -> str:
    try:
        page.goto(url, timeout=30000)
        return f"Navigated to {url}"
    except Exception as e:
        return f"Error navigating to {url}: {e}"

def click(page, selector: str) -> str:
    if ":contains" in selector or ":has-text" in selector:
        return "Error: ':contains' and ':has-text' are not valid CSS selectors."
    try:
        page.wait_for_selector(selector, state="visible", timeout=10000)
        el = page.query_selector(selector)
        if el:
            el.scroll_into_view_if_needed()
            el.click(timeout=5000)
            return f"Clicked {selector}"
        else:
            return f"Element {selector} not found"
    except Exception as e:
        return f"Error clicking {selector}: {e}"

def type_text(page, args: str) -> str:
    try:
        selector, text = args.split("|", 1)
        page.wait_for_selector(selector, state="visible", timeout=10000)
        el = page.query_selector(selector)
        if el:
            el.fill(text)
            return f"Typed '{text}' into {selector}"
        else:
            return f"Element {selector} not found"
    except Exception as e:
        return f"Error typing in {selector}: {e}"

def hover(page, selector: str) -> str:
    try:
        page.wait_for_selector(selector, state="visible", timeout=10000)
        el = page.query_selector(selector)
        if el:
            el.hover()
            return f"Hovered over {selector}"
        else:
            return f"Element {selector} not found"
    except Exception as e:
        return f"Error hovering {selector}: {e}"

def extract_text(page, selector: str) -> str:
    try:
        page.wait_for_selector(selector, state="visible", timeout=10000)
        el = page.query_selector(selector)
        if el:
            return el.inner_text()
        else:
            return f"Element {selector} not found"
    except Exception as e:
        return f"Error extracting text from {selector}: {e}"

def get_elements(page, selector: str) -> str:
    try:
        page.wait_for_selector(selector, state="visible", timeout=10000)
        els = page.query_selector_all(selector)
        return f"Found {len(els)} elements for {selector}"
    except Exception as e:
        return f"Error getting elements for {selector}: {e}"

def main():
    browser = create_sync_playwright_browser(headless=False)
    context = browser.new_context()
    page = context.new_page()

    tools = [
        Tool(
            name="navigate",
            func=lambda url: navigate(page, url),
            description="Navigate to a URL. Input: URL string."
        ),
        Tool(
            name="click",
            func=lambda selector: click(page, selector),
            description="Clicks an element after ensuring it is visible and scrolled into view. Input: selector string. Only use valid CSS selectors."
        ),
        Tool(
            name="type",
            func=lambda args: type_text(page, args),
            description="Types text into an input. Input: 'selector|text' (use | to separate)."
        ),
        Tool(
            name="hover",
            func=lambda selector: hover(page, selector),
            description="Hovers over an element. Input: selector string."
        ),
        Tool(
            name="extract_text",
            func=lambda selector: extract_text(page, selector),
            description="Extracts inner text from an element. Input: selector string."
        ),
        Tool(
            name="get_elements",
            func=lambda selector: get_elements(page, selector),
            description="Gets the number of elements matching a selector. Input: selector string."
        ),
        Tool(
            name="wait",
            func=wait_seconds,
            description="Waits for the specified number of seconds. Input: number of seconds as a string."
        ),
        Tool(
           name="get_all_elements",
           func=lambda tag="*": get_all_elements(page, tag),
           description="Lists all elements of a given tag (default all), their selectors, and their visible text. Input: tag name (e.g., 'button', 'a', 'input', or '*' for all)."
        ),
    ]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    # --- First prompt: run the workflow ---
    workflow_prompt = (
        "navigate to https://www.humanfocus.org.uk/CBTByB/his/login/entry, "
        "wait for 10 seconds, "
        "get_html, "
        "login to the site using the following details: "
        "Organisation Identifier: test, "
        "Person Identifier: sohaila, "
        "password: 12345678, "
        "verify the validation message."
    )
    result = agent.run(workflow_prompt)
    print("\n--- Agent Result ---\n", result)

    # --- Second prompt: code generation ---
    codegen_prompt = (
        "Generate a complete Playwright Python script that performs the following steps: "
        + workflow_prompt
        + " Use valid selectors and dummy data where needed."
    )
    codegen_result = llm.invoke(codegen_prompt)
    print("\n--- Playwright Script ---\n", codegen_result)

    browser.close()

if __name__ == "__main__":
    main()