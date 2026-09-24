import re
from urllib.parse import urljoin
from typing import Optional
from bs4 import BeautifulSoup, Comment

from app.api.schemas import ExtractedDocument
from app.engine.crawler.frontier import URLFrontier

class DocumentExtractor:
    BOILERPLATE_TAGS = {
        "script", "style", "nav", "footer", "header",
        "aside", "form", "noscript", "svg", "iframe", "button"
    }

    @classmethod
    def extract(cls, url: str, html: str) -> Optional[ExtractedDocument]:
        if not html or not html.strip():
            return None
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            soup = BeautifulSoup(html, "html.parser")

        #remove comments
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        #extract title
        title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()
        else:
            h1 = soup.find("h1")
            title = h1.get_text().strip() if h1 else url

        #snippet extraction
        snippet = ""
        meta_desc = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if meta_desc and meta_desc.get("content"):
            snippet = meta_desc["content"].strip()
        else:
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                snippet = og_desc["content"].strip()

        #links associated to the webpage
        outlinks: set[str] = set()
        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag["href"].strip()

            #ignore contact details and js src
            if raw_href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue

            # Convert relative URLs to absolute
            absolute_url = urljoin(url, raw_href)
            canonical = URLFrontier.canonicalize_url(absolute_url)
            if canonical and canonical != url:
                outlinks.add(canonical)

        #clean the boilerplate tags so that details look easy
        for tag in soup.find_all(cls.BOILERPLATE_TAGS):
            tag.decompose()

        raw_text = soup.get_text(separator=" ", strip=True)
        cleaned_text = re.sub(r"\s+", " ", raw_text).strip()

        if not snippet and cleaned_text:
            snippet = cleaned_text[:250] + ("..." if len(cleaned_text) > 250 else "")

        if len(cleaned_text) < 50:
            return None

        return ExtractedDocument(
            url=url,
            title=title or url,
            snippet=snippet,
            text_content=cleaned_text,
            outlinks=sorted(list(outlinks)),
            content_length=len(cleaned_text),
        )
    