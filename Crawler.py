
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


import logging

class Crawler:
    def __init__(self,name="Unknown"):
        self.name=name

    def wait4elem(self, xpath_str, timeout=30):
        element = WebDriverWait(self.browser, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath_str))
        )
        return element

    def xpath(self, xpath, section=None):
        if section is None:
            section = self.browser
        return section.find_element_by_xpath(xpath)

    def xpaths(self, xpath, section=None):
        if section is None:
            section = self.browser
        return section.find_elements_by_xpath(xpath)

    def _set_logging(self):
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        file_handler = logging.FileHandler(self.name+".log", "a", encoding="UTF-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        console.setLevel(logging.WARN)
        logging.getLogger(self.name).addHandler(console)
        logging.getLogger(self.name).addHandler(file_handler)
