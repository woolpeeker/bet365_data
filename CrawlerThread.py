from selenium import webdriver
from selenium.common.exceptions import TimeoutException

from matchParser import MatchParser
from Crawler import Crawler
from utils import get_logger

import multiprocessing as mp
import datetime, time, logging, traceback
from collections import deque
from queue import Empty


class CrawlerThread(Crawler):
    def __init__(self, name):
        super(CrawlerThread, self).__init__(name)
        self.queue = mp.Queue(maxsize=200)
        self.process = mp.Process(target=self.run, name=name)
        self.process.start()

    # The only function for main_thread to deploy jobs
    def add_match(self, match):
        self.queue.put_nowait(match)

    def run(self):
        self.logger=get_logger(self.name)
        self.logger.info('function run')
        while True:
            try:
                self.work()
            except:
                self.logger.warning(traceback.format_exc())
                self.logger.warning('Restart work')

    def work(self):
        self.logger.info('function work')
        self.FLAG = {
            'restart': False,
            'last_parse': datetime.datetime.now()
        }
        self.matchList = deque(maxlen=100)
        self._open()
        self.parser = MatchParser(self.browser,self.logger)
        while True:
            try:
                self.FLAG['last_start_work_loop']=datetime.datetime.now()
                self.work_loop()
                if self.FLAG['restart']:
                    self.logger.warning('break in work.')
                    break
                used_time=datetime.datetime.now()-self.FLAG['last_start_work_loop']
                self.logger.info('work loop used time %.2fs'%used_time.total_seconds())
                if used_time<datetime.timedelta(seconds=10):
                    time.sleep(10-used_time.total_seconds())
            except:
                self.logger.info(traceback.format_exc())

        self.logger.warning('browser close.')
        self.browser.close()

    def work_loop(self):
        self.fill_matchList()
        self.logger.info('function work_loop')
        for match in self.matchList:
            if self.FLAG['restart']:
                break
            if self.gotomatch(match):
                result = self.parser.parse(match)
                self.logger.info('get result: %s' % result)
                # TODO: save the result
                self.FLAG['last_parse'] = datetime.datetime.now()
                try:
                    self.click_soccer()
                except TimeoutException as e:
                    self.logger.info('no soccer section, sleep 1 mininute')
                    time.sleep(60)
            else:
                continue

    def fill_matchList(self):
        #get out of match from Queue, and put it to deque
        self.logger.info('function fill_MatchList')
        while True:
            try:
                match = self.queue.get_nowait()
                if match not in self.matchList:
                    self.matchList.append(match)
                    self.logger.info('Fill matchList: %s' % str(match))
            except Empty:
                self.logger.info('fill_matchList finished.')
                break

    def gotomatch(self, match):
        self.logger.info('function gotomach %s' % str(match))
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

    def click_overview(self):
        overview = self.wait4elem('//div[contains(@class,"ip-ControlBar_BBarItem ")]')
        overview.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]')

    def click_soccer(self):
        self.logger.info('function click soccer')
        try:
            self.click_overview()
            soccer_button = self.wait4elem('//div[@class="ipo-ClassificationBarButtonBase_Label "][text()="Soccer"]')
            soccer_button.click()
            return True
        except TimeoutException as e:
            self.logger.info('TimeOut: click_soccer')
            return False

    def _open(self):
        self.logger.info('function open')
        self.browser = webdriver.Firefox()
        self.browser.get('https://www.365838.com/en')
        self.open_time = datetime.datetime.now()

        self.wait4elem('//div[@id="dBlur"][contains(@style,"hidden;")]', timeout=150)
        # click the welcome sports banner and inplay section
        entry_banner = self.browser.find_element_by_xpath('//div[@id="dv1"]')
        entry_banner.click()
        inplay_banner = self.wait4elem('//a[@class="hm-BigButton "][text()="In-Play"]', timeout=150)
        inplay_banner.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]', timeout=150)
