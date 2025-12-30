import os
from src.paths import *
import requests
import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from src.paths import SRC_DIR

BASE_URL = "https://sudrf.cntd.ru"
EDGE_DRIVER_PATH = SRC_DIR / "parser" / "msedgedriver.exe"

class Parser:
    def __init__(self, webdriver_path):
        options = webdriver.EdgeOptions()
        options.add_argument("--start-maximized")
        # options.add_argument("--headless=new")
        self.driver = webdriver.Edge(
            service=Service(webdriver_path),
            options=options
        )
        print("вебдрайвер загружен")

    def __enter__(self):
        return self

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_links_list_page(self, links_list_url, max_scroll=0):
        """
        Возвращает html-код страницы со списком ссылок на документы.
        """
        self.driver.get(links_list_url)
        time.sleep(3)

        last_height = 0
        same_count = 0

        cnt = 0

        while cnt < 120:
            cnt += 1
            if cnt == max_scroll:
                break
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.2)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            print(f"Height: {new_height}")

            if new_height == last_height:
                same_count += 1
                if same_count >= 3:
                    print("Достигнут конец страницы")
                    break
            else:
                same_count = 0

            last_height = new_height

        return self.driver.page_source

    def get_docs_links(self, html):
        """
        Сохраняет список ссылок на документы с главной страницы поиска.
        """
        doc_links = []
        soup = BeautifulSoup(html, "lxml")
        for link in soup.find_all("a", class_="document-list_i_lk"):
            doc_links.append(BASE_URL + link.get("href"))
        return doc_links

    def parse_all(self):
        pass


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
