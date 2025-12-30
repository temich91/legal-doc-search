import re
import requests
from bs4 import BeautifulSoup

class Chunker:
    def get_paragraphs(self, doc_url, without_title=True):
        """
        Разделяет html-разметку фабулы на абзацы в чистом виде.
        """
        st = 2 if without_title else 0 # пропустить заголовок

        keywords = ["рассмотрев материалы дела", "установил", "у с т а н о в и л", "решил", "р е ш и л"]
        paragraphs = []

        doc_html = requests.get(doc_url).text
        soup = BeautifulSoup(doc_html, "lxml")
        div = soup.find("div", class_="document-text_block")
        for p in div.find_all("p", recursive=True)[st:]:
            text = p.get_text(separator=" ", strip=True)

            kw_flag = False
            for keyword in keywords:
                if keyword in text.lower():
                    kw_flag = True
                    break
            if kw_flag:
                break

            text = re.sub(r"\s+([,.;:])", r"\1", text)
            text = re.sub(r"\s{2,}", " ", text)

            if text:
                paragraphs.append(text + "\n")
        return paragraphs

    def chunk_paragraphs(self, paragraphs, min_chars= 200, max_chars= 1000):
        """
        Объединяет абзацы в чанки по размеру.
        """
        chunks = []
        buffer = ""
        for p in paragraphs:
            if not buffer:
                buffer = p
                continue

            if len(buffer) < min_chars:
                buffer = buffer + " " + p
            else:
                chunks.append(buffer.strip())
                buffer = p

            if len(buffer) >= max_chars:
                chunks.append(buffer.strip())
                buffer = ""

        if buffer:
            chunks.append(buffer.strip())

        return chunks
