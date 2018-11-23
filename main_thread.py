from selenium.common.exceptions import TimeoutException
from selenium import webdriver

import datetime
import queue
import time
import threading
import traceback
from collections import deque

from Crawler import Crawler
from CrawlerThread import CrawlerThread
from Saver import Saver
from utils import get_logger

NT = 2


class MainThread(Crawler):
    def __init__(self):
        super(MainThread, self).__init__('MainThead')
        self.n_thread = NT
        self.logger=get_logger('MainThead')
        self.crawlerList = []
        self.oldMatches = deque(maxlen=300)
        self.saver = Saver()

    def run(self):
        self.logger.info('Mainthread start')
        self.crawlerList = [CrawlerThread('crawlerThread_%d' % i) for i in range(self.n_thread)]
        self.save_thread = threading.Thread(target=self.save_result)
        self.save_thread.setDaemon(True)
        self.save_thread.start()
        while True:
            try:
                self.work_loop()
            except:
                self.logger.error(traceback.format_exc())
            finally:
                self._close()
                self.logger.info('work_loop restarting...')

    def work_loop(self):
        self.FLAG = {
            'restart': False,
            'last_new_match': datetime.datetime.now(),
            'last_restart': datetime.datetime.now(),
        }
        self.watch_dog()
        self._open()
        while True:
            self.logger.info('work_loop start.')
            if self.FLAG['restart']:
                self.logger.warning('restart flag on, work loop break.')
                break
            if not self.click_soccer():
                self.logger.info('No Soccer Section. Waiting 3 min.')
                time.sleep(3 * 60)
                continue
            self.wait4elem('//span[@class="ipo-TeamStack_TeamWrapper"]')
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
            self.oldMatches.append(elem)
            self.FLAG['last_new_match'] = datetime.datetime.now()
            self.crawlerList[i % self.n_thread].add_match(elem)
            i=i+1

    def save_result(self):
        while True:
            for crawler in self.crawlerList:
                try:
                    result=crawler.o_queue.get(True,2)
                    self.saver.insert(result)
                except queue.Empty as e:
                    continue
                except Exception as e:
                    self.logger.error('save_result error:')
                    self.logger.error(traceback.format_exc())


    def _open(self):
        self.logger.debug('function _open')
        self.browser = webdriver.Firefox()
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
            time.sleep(10)
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

    def watch_dog(self):
        if not 'watch_dog' in self.FLAG or not self.FLAG['watch_dog']:
            self.watchDogThread = threading.Thread(target=self.watch_dog_worker)
            self.watchDogThread.setDaemon(True)
            self.watchDogThread.start()
            self.FLAG['watch_dog']=True

    def watch_dog_worker(self):
        self.logger.info('watch_dog_worker start')
        while True:
            now=datetime.datetime.now()
            last_new_match_delta=now - self.FLAG['last_new_match']
            last_restart_delta = now - self.FLAG['last_restart']
            if last_new_match_delta.total_seconds() > 1800:
                self.logger.warning('last_new_match_delta excceeds maximum')
                self.FLAG['restart']=True
                break
            elif last_restart_delta.total_seconds() > 1800:
                self.logger.warning('last_restart_delta excceeds maximum')
                self.FLAG['restart']=True
                break
            time.sleep(120)
        self.FLAG['watch_dog']=False
        self.logger.info('watch_dog_worker exit')


if __name__ == '__main__':
    mainThread = MainThread()
    mainThread.run()