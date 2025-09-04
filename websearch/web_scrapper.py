import requests
from bs4 import BeautifulSoup

class EnchancedWebScrapperTool:
    def __init__(self):
        self.name="WebScrapper"
        self.description=""

    def run(self, url : str) -> str:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/117.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for script in soup(["script", "style", "footer", "nav", "aside"]):
                script.extract()

            text = soup.get_text(separator="\n", strip=True)

            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
            text = "\n".join(chunk for chunk in chunks)

            max_length = 4000

            if len(text) > max_length:
                text = text[:max_length]

            return f"Content from {url}:\n\n{text}"
        
        except Exception as e:
            return f"Error scrappin {url}:{str(e)}"