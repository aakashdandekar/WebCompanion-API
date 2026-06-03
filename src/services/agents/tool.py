from langchain.tools import tool
from playwright.async_api import async_playwright

tags = [
    "p", 
    "div", 
    "h1", 
    "h2", 
    "h3", 
    "h4", 
    "h5", 
    "h6",
    "label",
    "input"
]

@tool
def webScrape(url: str) -> any:
    """
    This tool is used to scrape website.
    This tool take url as input.    
    """
    try:
        with async_playwright() as scraper:
            browser = scraper.cromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, wait_until="networkidle")

            data_tags = {}
            for tag in tags:
                data_tags[tag] = page.eval_on_selector_all(
                    tag, 
                    """
                    elements => elements.map(e => {
                        text: e.innertext
                    });
                    """
                )

            data = {
                "title": page.title(),
                "url": page.url(),
                "links": page.eval_on_selector_all(
                    "a",
                    """
                    elements => element.map(e => {
                        text: e.innerText,
                        href: e.href
                    });
                    """
                ),
                "text": page.locator("body").inner_text(),
                "data-tags": data_tags
            }

            browser.close()
        
        return data

    except Exception as e:
        print(f"Error: {e}")