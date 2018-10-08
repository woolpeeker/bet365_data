
from selenium import webdriver
from parse_one_match import parse_one_match

from Crawler import Crawler
import multiprocessing as mp
import datetime
import time

class CrawlerThread(Crawler):
    def __init__(self, name):
        super(CrawlerThread, self).__init__()
        self.queue = mp.Queue(maxsize=100)
        self.process = mp.Process(target=self.run, name=name)
        self.process.start()

    def add_match(self, match):
        self.queue.put_nowait(match)

    def run(self):
        self.matchList=[]
        pass

    def get_match(self,):
        pass
    
    def work(self):
        self._open()
        self.work_loop()

    def work_loop(self):
        pass


    def _open(self):
        self.browser=webdriver.Chrome()
        self.browser.get('https://www.365838.com/en')
        self.init_time = datetime.datetime.now()

        self.wait4elem('//div[@id="dBlur"][contains(@style,"hidden;")]', timeout=300)
        # click the welcome sports banner and inplay section
        entry_banner = self.browser.find_element_by_xpath('//div[@id="dv1"]')
        entry_banner.click()
        inplay_banner = self.wait4elem('//a[@class="hm-BigButton "][text()="In-Play"]', timeout=300)
        inplay_banner.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]', timeout=300)
