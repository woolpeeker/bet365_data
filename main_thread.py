from selenium.common.exceptions import TimeoutException
from selenium import webdriver

import datetime
import logging
import time
import multiprocessing as mp

from Crawler import Crawler
from CrawlerThread import CrawlerThread

NT = 4


class MainThread(Crawler):
    def __init__(self):
        super(MainThread, self).__init__()
        self.n_thread = NT
        self._set_logging()
        self.flags = dict()
        self.crawlerList = []
        self.oldMatches = set()

        self.init_flags()

    def run(self):
        self.work()

    def _open(self):
        self.browser = webdriver.Chrome()
        self.browser.get('https://www.365838.com/en')
        self.init_time = datetime.datetime.now()

        self.wait4elem('//div[@id="dBlur"][contains(@style,"hidden;")]', timeout=300)
        # click the welcome sports banner and inplay section
        entry_banner = self.browser.find_element_by_xpath('//div[@id="dv1"]')
        entry_banner.click()
        inplay_banner = self.wait4elem('//a[@class="hm-BigButton "][text()="In-Play"]', timeout=300)
        inplay_banner.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]', timeout=300)

    def init_flags(self):
        self.flags['has_soccer'] = True
        self.flags['last_parse'] = datetime.datetime.now()

    def work(self):
        #TODO fake a process for debug
        self.crawlerList = [CrawlerThread('crawlerThread_%d' % i) for i in range(self.n_thread)]
        self._open()
        self.work_loop()

    def work_loop(self):
        while True:
            logging.info('start.')
            if not self.click_soccer():
                logging.info('No Soccer Section. Waiting 3 min.')
                time.sleep(3 * 60)
                continue
            teams_league = self._get_team_names()
            logging.info('Found %d match' % len(teams_league))
            self.deploy_jobs(teams_league)
            logging.info('Put elem to quenes. Sleep 3 minutes.')
            time.sleep(60 * 3)

    # Find new matches,and put it to crawlerThreads.
    def deploy_jobs(self, teams_league):
        i = 0
        for elem in teams_league:
            if elem in self.oldMatches:
                continue
            self.threadList[i % self.n_thread].add_match(elem)
        self.oldMatches.intersection_update(teams_league)

    def _get_team_names(self):
        # team_names is a list that each elem is a tuple represent a match
        # (list of team, league name)
        team_names = []
        leagues = self.xpaths('//div[contains(@class,"ipo-CompetitionButton_NameLabel ")]')
        leagues = [x.text for x in leagues]
        for league_name in leagues:
            league_elem = self.xpaths(
                '//div[contains(@class,"ipo-Competition ")]/div/div[text()="%s"]/../..' % league_name)
            if not league_elem:
                logging.warning('league %s disappear' % league_name)
                continue
            match_list = self.xpaths('.//div[contains(@class,"ipo-Fixture_ScoreDisplay")]',
                                     section=league_elem[0])
            if not match_list:
                logging.warning('No match in %s' % league_name)
                continue
            for m in match_list:
                team_names = self.xpaths('.//span[contains(@class,"ipo-TeamStack_TeamWrapper")]', m)
                if not team_names:
                    logging.warning('team disappear in %s' % league_name)
                    continue
                team_names = [x.text for x in team_names][:2]
                team_names.append((team_names, league_name))
        return team_names

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
            return False


if __name__ == '__main__':
    mainThread = MainThread()
    mainThread.run()
