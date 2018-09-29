from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException,NoSuchElementException,TimeoutException,WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import logging

import traceback
import re, time
import numpy as np
import pandas as pd
import datetime

from parse_one_match import parse_one_match
from Saver import Saver



class Crawler:
    def __init__(self, out_path):
        self.out_path=out_path
        self.saver=Saver('data/data')
        self.round_time=3*60
        self.browser=webdriver.Chrome()
        self.init_time=datetime.datetime.now()

    def flush(self):
        self.saver.flush()
    
    def run(self):
        self.browser.get('https://www.365838.com/en')
        self.wait4elem('//div[@id="dBlur"][contains(@style,"hidden;")]',timeout=300)

        #click the welcome sports banner and inplay section
        entry_banner=self.browser.find_element_by_xpath('//div[@id="dv1"]')
        entry_banner.click()
        inplay_banner=self.wait4elem('//a[@class="hm-BigButton "][text()="In-Play"]',timeout=300)
        inplay_banner.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]',timeout=300)
        self._parse()

    def xpath(self,xpath,section=None):
        if section==None:
            section=self.browser
        return section.find_element_by_xpath(xpath)

    def xpaths(self,xpath,section=None):
        if section==None:
            section=self.browser
        return section.find_elements_by_xpath(xpath)

    def _parse(self):
        now=None
        flush_time=None
        through_flag=False
        while True:
            before=now
            now=datetime.datetime.now()
            if flush_time is None:
                flush_time=now
            if flush_time is not None and now-flush_time>datetime.timedelta(seconds=600):
                self.flush()
                flush_time=now
            if before is not None and through_flag:
                delta=now-before
                wait_time=max(0, self.round_time - delta.total_seconds())
                if wait_time>0:
                    if now-self.init_time>datetime.timedelta(seconds=5*3600):
                        logging.info('5 hour round. should restart to free memory.')
                        self.close()
                    logging.info('wait for next round.')
                    time.sleep(wait_time)

            try:
                logging.info('start.')
                self.click_soccer()

                leagues=self.browser.find_elements_by_xpath('//div[contains(@class,"ipo-CompetitionButton_NameLabel ")]')
                leagues=[x.text for x in leagues]

                for league in leagues:
                    league_elem=self.xpaths('//div[contains(@class,"ipo-Competition ")]/div/div[text()="%s"]/../..'%league)
                    if not league_elem:
                        continue
                    team_names=[]
                    match_list=league_elem[0].find_elements_by_xpath('.//div[contains(@class,"ipo-Fixture_ScoreDisplay")]')
                    for m in match_list:
                        team_name=m.find_elements_by_xpath('.//span[contains(@class,"ipo-TeamStack_TeamWrapper")]')
                        team_names.append([x.text for x in team_name])
                    for team_name in team_names:
                        try:
                            t1=self.xpaths('//div/span[@class="ipo-TeamStack_TeamWrapper"][text()="%s"]'%team_name[0])
                            t2=self.xpaths('//div/span[@class="ipo-TeamStack_TeamWrapper"][text()="%s"]'%team_name[1])
                            if t1:
                                ActionChains(self.browser).move_to_element_with_offset(t1[0], 2, 0).click(t1[0]).perform()
                            elif t2:
                                ActionChains(self.browser).move_to_element_with_offset(t2[0], 2, 0).click(t2[0]).perform()
                            else:
                                continue
                            self.wait4elem('//div[@class="ipe-SoccerHeaderLayout_ExtraData "]',timeout=30)
                            for i in range(3):
                                try:
                                    parse_one_match(self.browser,league,saver=self.saver)
                                    break
                                except Exception as e:
                                    logging.error(traceback.format_exc())
                                    continue
                            #Go back to mainlist
                            self.click_overview()
                        except WebDriverException as e:
                            logging.error(traceback.format_exc())
                            break
                        except:
                            logging.error(traceback.format_exc())
                            continue
                through_flag=True
            except Exception as e:
                logging.warning(traceback.format_exc())
                logging.warning('refreshing')
                self.browser.refresh()
                self.click_overview(timeout=30)

    def click_overview(self, timeout=5):
        overview = self.wait4elem('//div[contains(@class,"ip-ControlBar_BBarItem ")]', timeout=timeout)
        overview.click()
        self.wait4elem('//div[contains(@class,"ipo-Fixture_ScoreDisplay")]', timeout=30)

    # after click overview
    def click_soccer(self):
        while True:
            try:
                self.click_overview()
                soccer_button=self.wait4elem('//div[@class="ipo-ClassificationBarButtonBase_Label "][text()="Soccer"]',timeout=30)
                soccer_button.click()
                break
            except TimeoutException as e:
                logging.info('No Soccer Section. Waiting 5 min.')
                time.sleep(300)
                self.browser.refresh()

    def wait4elem(self, xpath_str, timeout=5):
        element = WebDriverWait(self.browser, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath_str))
        )
        return element

    def close(self):
        try:
            self.flush()
            self.browser.close()
        except:
            logging.error(traceback.format_exc())
            logging.error('crawler close fail.')


def set_logging():
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    logging.basicConfig(level=logging.INFO,datefmt='%m-%d %H:%M:%S')
    file_handler = logging.FileHandler("main.log", "a",encoding="UTF-8")
    file_handler.setFormatter(formatter)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.getLogger('').addHandler(file_handler)


if __name__=='__main__':
    set_logging()
    while True:
        crawler=Crawler('data/data')
        try:
            crawler.run()
        except Exception as e:
            logging.error(traceback.format_exc())
            crawler.close()
            del crawler
            logging.error("===========================================================")
            logging.error('Fatal Error: Crawler Restart.')
            logging.error("===========================================================")
