import time
import base64
import re
from typing import Dict, Any, Optional, List
from playwright.sync_api import sync_playwright, Browser, Page, Playwright, BrowserContext

from backend.tools.registry import registry, RiskLevel
from backend.config import GEMINI_API_KEY

class BrowserManager:
    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._tabs: List[Page] = []

    def _ensure_browser(self):
        if not self._playwright:
            self._playwright = sync_playwright().start()
        if not self._browser or not self._browser.is_connected():
            self._browser = self._playwright.chromium.launch(headless=True)
            self._context = self._browser.new_context(viewport={"width": 1280, "height": 800})
        if not self._page or self._page.is_closed():
            self._page = self._context.new_page()
            self._tabs = [self._page]

    def open_url(self, url: str) -> Dict[str, Any]:
        self._ensure_browser()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
        return {
            "success": True,
            "url": self._page.url,
            "title": self._page.title()
        }

    def navigate(self, url: str) -> Dict[str, Any]:
        return self.open_url(url)

    def new_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        self._ensure_browser()
        new_p = self._context.new_page()
        self._tabs.append(new_p)
        self._page = new_p
        if url:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"
            self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
        return {
            "success": True,
            "tab_index": len(self._tabs) - 1,
            "total_tabs": len(self._tabs),
            "url": self._page.url,
            "title": self._page.title()
        }

    def close_tab(self, index: Optional[int] = None) -> Dict[str, Any]:
        self._ensure_browser()
        if not self._tabs:
            return {"success": False, "message": "No open tabs to close."}
        
        target_idx = index if (index is not None and 0 <= index < len(self._tabs)) else (len(self._tabs) - 1)
        closing_tab = self._tabs.pop(target_idx)
        closing_tab.close()
        
        if self._tabs:
            self._page = self._tabs[-1]
            return {"success": True, "remaining_tabs": len(self._tabs), "active_title": self._page.title()}
        else:
            self._page = None
            return {"success": True, "remaining_tabs": 0, "message": "All tabs closed."}

    def get_tabs(self) -> Dict[str, Any]:
        self._ensure_browser()
        tab_list = []
        for i, tab in enumerate(self._tabs):
            tab_list.append({
                "index": i,
                "title": tab.title(),
                "url": tab.url,
                "is_active": tab == self._page
            })
        return {
            "success": True,
            "total_tabs": len(self._tabs),
            "tabs": tab_list
        }

    def search(self, query: str) -> Dict[str, Any]:
        self._ensure_browser()
        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        self._page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
        
        results = []
        titles = self._page.query_selector_all(".result__title a")
        snippets = self._page.query_selector_all(".result__snippet")
        
        for i in range(min(5, len(titles))):
            try:
                t = titles[i].inner_text().strip()
                href = titles[i].get_attribute("href")
                snip = snippets[i].inner_text().strip() if i < len(snippets) else ""
                if t:
                    results.append({"title": t, "url": href, "snippet": snip})
            except Exception:
                pass

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results or [{"title": f"Search results for '{query}'", "url": search_url}]
        }

    def read_page(self) -> Dict[str, Any]:
        self._ensure_browser()
        title = self._page.title()
        url = self._page.url
        body_text = self._page.inner_text("body")
        clean_text = " ".join(body_text.split())[:2000]

        # Extract accessible links, buttons, and inputs
        links = []
        for a in self._page.query_selector_all("a")[:8]:
            try:
                txt = a.inner_text().strip()
                href = a.get_attribute("href")
                if txt and href:
                    links.append({"text": txt, "href": href})
            except Exception:
                pass

        buttons = []
        for b in self._page.query_selector_all("button, input[type='submit'], input[type='button']")[:6]:
            try:
                btxt = b.inner_text().strip() or b.get_attribute("value") or "Button"
                buttons.append(btxt)
            except Exception:
                pass

        inputs = []
        for inp in self._page.query_selector_all("input[type='text'], input[type='email'], input[type='search'], textarea")[:4]:
            try:
                name = inp.get_attribute("name") or inp.get_attribute("placeholder") or "Input"
                inputs.append(name)
            except Exception:
                pass

        return {
            "success": True,
            "title": title,
            "url": url,
            "text": clean_text,
            "links": links,
            "buttons": buttons,
            "inputs": inputs
        }

    def find_text(self, text: str) -> Dict[str, Any]:
        self._ensure_browser()
        body_text = self._page.inner_text("body")
        found = text.lower() in body_text.lower()
        snippet = ""
        if found:
            idx = body_text.lower().find(text.lower())
            start = max(0, idx - 100)
            end = min(len(body_text), idx + len(text) + 100)
            snippet = body_text[start:end].strip()
        return {
            "success": True,
            "found": found,
            "query_text": text,
            "snippet": snippet or "Text not found on page."
        }

    def click_element(self, selector: str) -> Dict[str, Any]:
        self._ensure_browser()
        # Strategy 1: Direct CSS selector
        try:
            self._page.click(selector, timeout=3000)
            return {"success": True, "message": f"Clicked element matching '{selector}'"}
        except Exception:
            pass

        # Strategy 2: Text matching
        try:
            self._page.click(f"text={selector}", timeout=3000)
            return {"success": True, "message": f"Clicked element with text '{selector}'"}
        except Exception:
            pass

        # Strategy 3: Role / accessible button
        try:
            self._page.get_by_role("button", name=selector).click(timeout=3000)
            return {"success": True, "message": f"Clicked button role '{selector}'"}
        except Exception:
            pass

        # Strategy 4: Role link
        try:
            self._page.get_by_role("link", name=selector).click(timeout=3000)
            return {"success": True, "message": f"Clicked link role '{selector}'"}
        except Exception:
            pass

        return {
            "success": False,
            "error": f"Could not find clickable element matching '{selector}' via DOM or accessibility tree."
        }

    def type_into_field(self, selector: str, text: str) -> Dict[str, Any]:
        self._ensure_browser()
        try:
            self._page.fill(selector, text, timeout=5000)
            return {"success": True, "typed": text, "selector": selector}
        except Exception:
            try:
                self._page.get_by_placeholder(selector).fill(text, timeout=5000)
                return {"success": True, "typed": text, "placeholder": selector}
            except Exception as e:
                return {"success": False, "error": str(e)}

    def select_option(self, selector: str, value: str) -> Dict[str, Any]:
        self._ensure_browser()
        try:
            self._page.select_option(selector, value=value, timeout=5000)
            return {"success": True, "selected": value, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def scroll(self, direction: str = "down") -> Dict[str, Any]:
        self._ensure_browser()
        delta = 600 if direction == "down" else -600
        self._page.mouse.wheel(0, delta)
        return {"success": True, "scrolled": direction}

    def go_back(self) -> Dict[str, Any]:
        self._ensure_browser()
        self._page.go_back(wait_until="domcontentloaded", timeout=10000)
        return {"success": True, "url": self._page.url, "title": self._page.title()}

    def go_forward(self) -> Dict[str, Any]:
        self._ensure_browser()
        self._page.go_forward(wait_until="domcontentloaded", timeout=10000)
        return {"success": True, "url": self._page.url, "title": self._page.title()}

    def refresh(self) -> Dict[str, Any]:
        self._ensure_browser()
        self._page.reload(wait_until="domcontentloaded", timeout=10000)
        return {"success": True, "url": self._page.url, "title": self._page.title()}

    def get_current_url(self) -> Dict[str, Any]:
        self._ensure_browser()
        return {"success": True, "url": self._page.url, "title": self._page.title()}

    def get_page_title(self) -> Dict[str, Any]:
        self._ensure_browser()
        return {"success": True, "title": self._page.title(), "url": self._page.url}

    def screenshot(self) -> Dict[str, Any]:
        self._ensure_browser()
        bytes_data = self._page.screenshot(type="jpeg", quality=70)
        b64 = base64.b64encode(bytes_data).decode("utf-8")
        return {
            "success": True,
            "url": self._page.url,
            "data_url": f"data:image/jpeg;base64,{b64}"
        }

    def submit_form(self, selector: str = "form") -> Dict[str, Any]:
        self._ensure_browser()
        try:
            self._page.eval_on_selector(selector, "form => form.submit()")
            return {"success": True, "message": f"Form '{selector}' submitted successfully."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close_all(self):
        """Emergency stop cleanup."""
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._tabs = []

browser_mgr = BrowserManager()

# --- Registered Browser Agent Tools ---

@registry.register(
    name="browser.open",
    description="Launch browser and navigate to a URL (e.g. 'https://google.com').",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {"url": {"type": "string", "description": "Website URL"}},
        "required": ["url"]
    },
    agent_category="browser"
)
def browser_open(url: str):
    return browser_mgr.open_url(url)

@registry.register(
    name="browser.navigate",
    description="Navigate the active browser page to a new URL.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {"url": {"type": "string", "description": "Target URL"}},
        "required": ["url"]
    },
    agent_category="browser"
)
def browser_navigate(url: str):
    return browser_mgr.navigate(url)

@registry.register(
    name="browser.newTab",
    description="Open a new browser tab with an optional URL.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {"url": {"type": "string", "description": "Optional URL for new tab"}},
        "required": []
    },
    agent_category="browser"
)
def browser_new_tab(url: Optional[str] = None):
    return browser_mgr.new_tab(url)

@registry.register(
    name="browser.closeTab",
    description="Close the active or specified browser tab.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={
        "type": "object",
        "properties": {"index": {"type": "integer", "description": "Tab index to close"}},
        "required": []
    },
    agent_category="browser"
)
def browser_close_tab(index: Optional[int] = None):
    return browser_mgr.close_tab(index)

@registry.register(
    name="browser.getTabs",
    description="Get list of all open browser tabs and active status.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={"type": "object", "properties": {}, "required": []},
    agent_category="browser"
)
def browser_get_tabs():
    return browser_mgr.get_tabs()

@registry.register(
    name="browser.getCurrentUrl",
    description="Get URL and title of the currently active browser page.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={"type": "object", "properties": {}, "required": []},
    agent_category="browser"
)
def browser_get_current_url():
    return browser_mgr.get_current_url()

@registry.register(
    name="browser.getPageTitle",
    description="Get the title of the currently active browser page.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={"type": "object", "properties": {}, "required": []},
    agent_category="browser"
)
def browser_get_page_title():
    return browser_mgr.get_page_title()

@registry.register(
    name="browser.search",
    description="Perform web search within browser and return top result links.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Search query"}},
        "required": ["query"]
    },
    agent_category="browser"
)
def browser_search(query: str):
    return browser_mgr.search(query)

@registry.register(
    name="browser.readPage",
    description="Extract main structured content (title, url, text, links, buttons, inputs) from active page.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={"type": "object", "properties": {}, "required": []},
    agent_category="browser"
)
def browser_read_page():
    return browser_mgr.read_page()

@registry.register(
    name="browser.findText",
    description="Search for specific keywords or deadline information on active page.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={
        "type": "object",
        "properties": {"text": {"type": "string", "description": "Text or keyword to search"}},
        "required": ["text"]
    },
    agent_category="browser"
)
def browser_find_text(text: str):
    return browser_mgr.find_text(text)

@registry.register(
    name="browser.clickElement",
    description="Click a DOM element by CSS selector, text, or accessible role (CONFIRM if sensitive).",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {"selector": {"type": "string", "description": "CSS selector, button text, or role"}},
        "required": ["selector"]
    },
    agent_category="browser"
)
def browser_click_element(selector: str):
    return browser_mgr.click_element(selector)

@registry.register(
    name="browser.typeIntoField",
    description="Type text into an input box, search field, or form area.",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector or placeholder"},
            "text": {"type": "string", "description": "Text to fill"}
        },
        "required": ["selector", "text"]
    },
    agent_category="browser"
)
def browser_type_into_field(selector: str, text: str):
    return browser_mgr.type_into_field(selector, text)

@registry.register(
    name="browser.selectOption",
    description="Select a dropdown option by value or text.",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector of select element"},
            "value": {"type": "string", "description": "Option value"}
        },
        "required": ["selector", "value"]
    },
    agent_category="browser"
)
def browser_select_option(selector: str, value: str):
    return browser_mgr.select_option(selector, value)

@registry.register(
    name="browser.scroll",
    description="Scroll browser page up or down.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={
        "type": "object",
        "properties": {"direction": {"type": "string", "enum": ["up", "down"], "description": "Scroll direction"}},
        "required": ["direction"]
    },
    agent_category="browser"
)
def browser_scroll(direction: str = "down"):
    return browser_mgr.scroll(direction)

@registry.register(
    name="browser.goBack",
    description="Navigate backward in browser history.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={"type": "object", "properties": {}, "required": []},
    agent_category="browser"
)
def browser_go_back():
    return browser_mgr.go_back()

@registry.register(
    name="browser.goForward",
    description="Navigate forward in browser history.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={"type": "object", "properties": {}, "required": []},
    agent_category="browser"
)
def browser_go_forward():
    return browser_mgr.go_forward()

@registry.register(
    name="browser.refresh",
    description="Reload the active browser page.",
    risk_level=RiskLevel.LOW_RISK,
    parameters={"type": "object", "properties": {}, "required": []},
    agent_category="browser"
)
def browser_refresh():
    return browser_mgr.refresh()

@registry.register(
    name="browser.screenshot",
    description="Capture screenshot of the currently active browser page.",
    risk_level=RiskLevel.READ_ONLY,
    parameters={"type": "object", "properties": {}, "required": []},
    agent_category="browser"
)
def browser_screenshot():
    return browser_mgr.screenshot()

@registry.register(
    name="browser.submitForm",
    description="Submit a web form (CONFIRM: requires confirmation).",
    risk_level=RiskLevel.CONFIRM,
    parameters={
        "type": "object",
        "properties": {"selector": {"type": "string", "description": "Form selector (default 'form')"}},
        "required": []
    },
    agent_category="browser"
)
def browser_submit_form(selector: str = "form"):
    return browser_mgr.submit_form(selector)
