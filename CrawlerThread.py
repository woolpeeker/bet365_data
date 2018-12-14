from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options

from matchParser import MatchParser
from Crawler import Crawler
import utils

import multiprocessing as mp
import datetime, time, traceback, os
from collections import deque
from queue import Empty



#TODO:WatchDog
class CrawlerThread(Crawler):
    def __init__(self, name):
        super(CrawlerThread, self).__init__(name)
        self.logger=utils.get_logger(self.name)
        self.i_queue = mp.Queue(maxsize=500)
        self.o_queue = mp.Queue(maxsize=1000)
        self.browserPID = mp.Value('i', 0)
        self.rust_path='C:\\Users\\luojiapeng\\AppData\\Local\\Temp\\rust_mozprofile.*'
        self.process = mp.Process(target=self.run, name=name)
        self.process.daemon=True
        self.process.start()

    # The only function for main_thread to deploy jobs
    def add_match(self, match):
        self.i_queue.put_nowait(match)

    def run(self):
        self.logger.info('Process start')
        self.matchList = deque(maxlen=150)
        while True:
            try:
                self.work()
            except:
                self.logger.warning(traceback.format_exc())
            finally:
                self._close()
                self.logger.warning('work restarting...')

    def work(self):
        self.logger.info('function work')
        self.FLAG = {}
        self._open()
        self.parser = MatchParser(self.browser,self.logger)
        while True:
            try:
                self.FLAG['last_start_work_loop']=datetime.datetime.now() #for too short work_loop, Not for watchdog
                self.work_loop()
                used_time=datetime.datetime.now()-self.FLAG['last_start_work_loop']
                self.logger.info('work loop used time %.2fs'%used_time.total_seconds())
                if used_time.total_seconds()<20:
                    t=20-used_time.total_seconds()
                    self.logger.info('work loop sleep for %.2f second'%t)
                    time.sleep(t)
            except:
                self.logger.info(traceback.format_exc())

    def work_loop(self):
        self.fill_matchList()
        self.logger.info('function work_loop')
        matches = self.filter_matchList()
        for match in matches:
            if self.gotomatch(match):
                result = self.parser.parse(match)
                result['crawler'] = self.name
                if result:
                    self.o_queue.put_nowait(result)
                    self.logger.info('get result: %s' % result)
                    self.FLAG['last_parse'] = datetime.datetime.now()
            self.click_soccer()

    def filter_matchList(self):
        teams=[x.text for x in self.xpaths('//span[@class="ipo-TeamStack_TeamWrapper"]')]
        matches=filter(lambda x: x[0][0] in teams or x[0][1] in teams, self.matchList)
        return list(matches)

    def fill_matchList(self):
        #get out of match from Queue, and put it to deque
        self.logger.info('function fill_MatchList')
        while True:
            try:
                match = self.i_queue.get(True,2)
                if match not in self.matchList:
                    self.matchList.append(match)
                    self.logger.info('Fill matchList: %s' % str(match))
            except Empty:
                self.logger.info('fill_matchList finished.')
                break

    def gotomatch(self, match):
        self.logger.info('function gotomatch %s' % str(match))
        team_names, league = match
        t1 = self.xpaths('//div/span[@class="ipo-TeamStack_TeamWrapper"][text()="%s"]' % team_names[0])
        t2 = self.xpaths('//div/span[@class="ipo-TeamStack_TeamWrapper"][text()="%s"]' % team_names[1])
        if t1:
            t1[0].click()
        elif t2:
            t2[0].click()
        else:
            self.logger.warning('cannot click. return False.')
            return False
        try:
            self.wait4elem('//div[@class="ipe-SoccerHeaderLayout_ExtraData "]')
        except TimeoutException as e:
            self.logger.warning('gotomatch timeout.')
            return False
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
        options = Options()
        options.headless = True
        self.browser = webdriver.Firefox(options=options)
        with self.browserPID.get_lock():
            self.browserPID.value = self.browser.service.process.pid
        self.logger.info('browserPID=%d'%self.browserPID.value)
        self.browser.get('https://www.bet365.com/en')
        self.open_time = datetime.datetime.now()

        self.wait4elem('//div[@id="dBlur"][contains(@style,"hidden;")]', timeout=150)
        # click the welcome sports banner and inplay section
        entry_banner = self.browser.find_element_by_xpath('//div[@id="dv1"]')
        entry_banner.click()
        inplay_banner = self.wait4elem('//a[@class="hm-BigButton "][text()="In-Play"]', timeout=150)
        inplay_banner.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]', timeout=150)

    def _close(self):
        self.logger.warning('browser close')
        try:
            self.browser.quit()
            time.sleep(10)
        except Exception as e:
            self.logger.error('browser close fail.')
            self.logger.error(traceback.format_exc())