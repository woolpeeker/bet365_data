from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

import datetime
import time
import traceback
import os
import multiprocessing as mp

from Crawler import Crawler
from utils import get_logger

NT = 2


class MainThread(Crawler):
    def __init__(self, name='MainThead'):
        self.name = name
        self.logger=get_logger(name=self.name)
        super(MainThread, self).__init__(name)
        self.out_queue = mp.Queue(maxsize=1000)
        self.browserPID = mp.Value('i', 0)

        self.process = mp.Process(target=self.run, name=name)
        self.process.daemon = True
        self.process.start()


    def run(self):
        self.logger.info('Mainthread start')
        while True:
            try:
                self.work_loop()
            except:
                self.logger.error(traceback.format_exc())
            finally:
                self._close()
                self.logger.info('work_loop restarting...')

    def work_loop(self):
        self._open()
        while True:
            self.logger.info('work_loop start.')
            if not self.click_soccer():
                self.logger.info('No Soccer Section. Waiting 3 min.')
                time.sleep(3 * 60)
                continue
            self.wait4elem('//span[@class="ipo-TeamStack_TeamWrapper"]')
            teams_league = self._get_team_names()
            self.logger.info('Found %d match' % len(teams_league))
            self.logger.info('teams_leagues:%s' % teams_league)
            for elem in teams_league:
                self.out_queue.put_nowait(elem)
            self.logger.info('Put elem to quenes. Sleep 3 minutes.')
            time.sleep(60 * 3)

    def _open(self):
        self.logger.debug('function _open')
        options = Options()
        options.headless = True
        self.browser = webdriver.Firefox(options=options)
        with self.browserPID.get_lock():
            self.browserPID.value = self.browser.service.process.pid
        self.logger.info('browserPID=%d'%self.browserPID.value)
        self.browser.get('https://www.bet365.com/en')
        self.init_time = datetime.datetime.now()

        self.wait4elem('//div[@id="dBlur"][contains(@style,"hidden;")]', timeout=300)
        # click the welcome sports banner and inplay section
        entry_banner = self.browser.find_element_by_xpath('//div[@id="dv1"]')
        entry_banner.click()
        inplay_banner = self.wait4elem('//a[@class="hm-BigButton "][text()="In-Play"]', timeout=300)
        inplay_banner.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]', timeout=300)

    def _close(self):
        self.logger.warning('browser close')
        try:
            self.browser.quit()
        except Exception as e:
            self.logger.error('browser close fail.')
            self.logger.error(traceback.format_exc())

    def _get_team_names(self):
        # team_names is a list that each elem is a tuple represent a match
        # (list of team, league name)
        result = []
        leagues = self.xpaths('//div[contains(@class,"ipo-CompetitionButton_NameLabel ")]/../..')
        for league in leagues:
            league_name=self.xpaths('.//div[contains(@class, "ipo-CompetitionButton_NameLabel")]',section=league)[0].text
            match_list = self.xpaths('.//div[contains(@class,"ipo-Fixture_ScoreDisplay")]',section=league)
            if not match_list:
                self.logger.warning('No match in %s' % league_name)
                continue
            for m in match_list:
                team_names = self.xpaths('.//span[contains(@class,"ipo-TeamStack_TeamWrapper")]', m)
                if not team_names:
                    self.logger.warning('No team in %s' % league_name)
                    continue
                team_names = tuple([x.text for x in team_names][:2])
                result.append((team_names, league_name))
        return result

    def click_overview(self):
        overview = self.wait4elem('//div[contains(@class,"ip-ControlBar_BBarItem ")]')
        overview.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]')

    def click_soccer(self):
        self.logger.info('click soccer')
        retry_times=2
        for i in range(retry_times):
            try:
                self.click_overview()
                soccer_button = self.wait4elem('//div[@class="ipo-ClassificationBarButtonBase_Label "][text()="Soccer"]')
                soccer_button.click()
                return True
            except TimeoutException as e:
                self.logger.warning('TimeOut: click soccer.')
                if i<retry_times:
                    self.logger.warning('refresh and retry')
                    self.browser.refresh()
                else:
                    self.logger.warning('excced retry times')
                return False