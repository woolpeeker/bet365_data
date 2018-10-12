from selenium.common.exceptions import TimeoutException
from selenium import webdriver

import datetime
import logging
import time
import traceback

from Crawler import Crawler
from CrawlerThread import CrawlerThread
from utils import get_logger

NT = 2


class MainThread(Crawler):
    def __init__(self):
        super(MainThread, self).__init__('MainThead')
        self.n_thread = NT
        self.logger=get_logger('MainThead')
        self.crawlerList = []
        self.oldMatches = set()

    def run(self):
        self.work()

    def work(self):
        self.crawlerList = [CrawlerThread('crawlerThread_%d' % i) for i in range(self.n_thread)]
        while True:
            try:
                self.work_loop()
            except:
                self.logger.error(traceback.format_exc())

    def work_loop(self):
        self.FLAG = {
            'restart': False,
            'last_new_match': datetime.datetime.now()
        }
        self._open()
        while True:
            self.logger.info('work_loop start.')
            if self.FLAG['restart']:
                self.logger.warning('work loop break.')
                break
            if not self.click_soccer():
                self.logger.info('No Soccer Section. Waiting 3 min.')
                time.sleep(3 * 60)
                continue
            teams_league = self._get_team_names()
            self.logger.info('Found %d match' % len(teams_league))
            self.deploy_jobs(teams_league)
            self.logger.info('Put elem to quenes. Sleep 3 minutes.')
            time.sleep(60 * 3)

    # Find new matches,and put it to crawlerThreads.
    def deploy_jobs(self, teams_league):
        self.logger.info('function deploy_jobs')
        i = 0
        for elem in teams_league:
            if elem in self.oldMatches:
                continue
            self.logger.info('add_match: %s' % str(elem))
            self.crawlerList[i % self.n_thread].add_match(elem)
            i=i+1

        self.oldMatches |= set(teams_league)
        self.FLAG['last_new_match'] = datetime.datetime.now()

    def _open(self):
        self.browser = webdriver.Firefox()
        self.browser.get('https://www.365838.com/en')
        self.init_time = datetime.datetime.now()

        self.wait4elem('//div[@id="dBlur"][contains(@style,"hidden;")]', timeout=300)
        # click the welcome sports banner and inplay section
        entry_banner = self.browser.find_element_by_xpath('//div[@id="dv1"]')
        entry_banner.click()
        inplay_banner = self.wait4elem('//a[@class="hm-BigButton "][text()="In-Play"]', timeout=300)
        inplay_banner.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]', timeout=300)

    def _get_team_names(self):
        # team_names is a list that each elem is a tuple represent a match
        # (list of team, league name)
        result = []
        leagues = self.xpaths('//div[contains(@class,"ipo-CompetitionButton_NameLabel ")]')
        leagues = [x.text for x in leagues]
        for league_name in leagues:
            league_elem = self.xpaths(
                '//div[contains(@class,"ipo-Competition ")]/div/div[text()="%s"]/../..' % league_name)
            if not league_elem:
                self.logger.warning('league %s disappear' % league_name)
                continue
            match_list = self.xpaths('.//div[contains(@class,"ipo-Fixture_ScoreDisplay")]',
                                     section=league_elem[0])
            if not match_list:
                self.logger.warning('No match in %s' % league_name)
                continue
            for m in match_list:
                team_names = self.xpaths('.//span[contains(@class,"ipo-TeamStack_TeamWrapper")]', m)
                if not team_names:
                    self.logger.warning('team disappear in %s' % league_name)
                    continue
                team_names = tuple([x.text for x in team_names][:2])
                result.append((team_names, league_name))
        return result

    def click_overview(self):
        overview = self.wait4elem('//div[contains(@class,"ip-ControlBar_BBarItem ")]')
        overview.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]')

    def click_soccer(self):
        try:
            self.click_overview()
            soccer_button = self.wait4elem('//div[@class="ipo-ClassificationBarButtonBase_Label "][text()="Soccer"]')
            soccer_button.click()
            return True
        except TimeoutException as e:
            self.logger.info('TimeOut: click soccer.')
            return False


if __name__ == '__main__':
    mainThread = MainThread()
    mainThread.run()
