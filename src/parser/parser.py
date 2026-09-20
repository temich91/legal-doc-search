import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class Parser:
    def __init__(self, webdriver_path):
        self.base_url = "https://sudrf.cntd.ru"
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=options)
        print("вебдрайвер загружен")

    def __enter__(self):
        return self

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_docs_links(self, links_list_url, max_scroll=0):
        """
        Возвращает html-код страницы со списком ссылок на документы.
        """
        self.driver.get(links_list_url)

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
        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.document-list_i_lk")))

        docs_links_elements = self.driver.find_elements(By.CSS_SELECTOR, "a.document-list_i_lk")
        links = [el.get_attribute("href") for el in docs_links_elements]
        return links

    def parse_all(self):
        pass
