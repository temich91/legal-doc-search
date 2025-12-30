import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.service import Service

class Parser:
    def __init__(self, webdriver_path):
        self.base_url = "https://sudrf.cntd.ru"
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
            doc_links.append(self.base_url + link.get("href"))
        return doc_links

    def parse_all(self):
        pass
