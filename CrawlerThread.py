from selenium import webdriver
from parse_one_match import parse_one_match
from matchParser import MatchParser
from Crawler import Crawler

import multiprocessing as mp
import datetime, time, logging, traceback
from collections import deque
from queue import Empty


class CrawlerThread(Crawler):
    def __init__(self, name):
        super(CrawlerThread, self).__init__()
        self.queue = mp.Queue(maxsize=100)
        self.process = mp.Process(target=self.run, name=name)
        self.process.start()

    # The only function for main_thread to deploy jobs
    def add_match(self, match):
        self.queue.put_nowait(match)

    def run(self):
        while True:
            try:
                self.work()
            except Exception as e:
                logging.error(traceback.format_exc())
                self.restart()


    def work(self):
        self._open()
        self.parser = MatchParser(self.browser)
        self.matchList = deque(maxlen=100)
        self.fill_matchList()
        for match in self.matchList:
            if self.gotomatch(match):
                result = MatchParser.parse(self, match)
                # TODO: save the result

    def fill_matchList(self):
        while True:
            try:
                match = self.queue.get_nowait()
                if match not in self.matchList:
                    self.matchList.append(match)
            except Empty:
                break

    def gotomatch(self, match):
        team_names, league = match
        t1 = self.xpaths('//div/span[@class="ipo-TeamStack_TeamWrapper"][text()="%s"]' % team_names[0])
        t2 = self.xpaths('//div/span[@class="ipo-TeamStack_TeamWrapper"][text()="%s"]' % team_names[1])
        if t1:
            t1[0].click()
        elif t2:
            t2[0].click()
        else:
            return False
        self.wait4elem('//div[@class="ipe-SoccerHeaderLayout_ExtraData "]')
        return True

    def _open(self):
        self.browser = webdriver.Chrome()
        self.browser.get('https://www.365838.com/en')
        self.open_time = datetime.datetime.now()

        self.wait4elem('//div[@id="dBlur"][contains(@style,"hidden;")]', timeout=150)
        # click the welcome sports banner and inplay section
        entry_banner = self.browser.find_element_by_xpath('//div[@id="dv1"]')
        entry_banner.click()
        inplay_banner = self.wait4elem('//a[@class="hm-BigButton "][text()="In-Play"]', timeout=150)
        inplay_banner.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]', timeout=150)
