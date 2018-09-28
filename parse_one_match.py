from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, ElementNotVisibleException
from selenium.webdriver.common.action_chains import ActionChains

import re, time, logging
import numpy as np
import pandas as pd
import traceback
import datetime

def parse_time(string):
    match_result=re.match('(\d+):(\d+)',string)
    if match_result:
        minute=int(match_result.group(1))
        second=int(match_result.group(2))
        return minute
    else:
        logging.warning('parse time wrong format')
        return -1

def parse_gidcell_int(string):
    #used for SoccerGridCell int
    #temperarily for stats
    if string.isdigit():
        return int(string)
    elif string=='':
        return np.NaN
    else:
        logging.warning('Raise ValueError:GridCell Int:%d'%string)
        raise ValueError('ValueError:GridCell Int:%d'%string)

def parse_one_match(browser,league,saver):

    for i in range(3):
        try:
            _parse_one_match(browser,league,saver)
            break
        except (StaleElementReferenceException,TimeoutException) as e:
            logging.warning(traceback.format_exc())
            logging.warning('refreshing')
            browser.refresh()
            time.sleep(5)
            logging.warning('retry')
    else:
        logging.error('Parsing_one_match fails, turn to upper page')

def parse_odd1(market):
    # gl-MarketGroupContainer
    odds = market.find_elements_by_xpath('.//span[@class="gl-Participant_Odds"]')
    odds = [float(x.text) for x in odds]
    return odds

def parse_odd2(market):
    # gl-MarketGroupContainer gl-MarketGroupContainer_HasLabels
    labelCol = market.find_element_by_xpath('.//div[contains(@class,"gl-MarketLabel ")]')
    valuesCols = market.find_elements_by_xpath('.//div[contains(@class,"gl-MarketValues ")]')

    index = labelCol.find_elements_by_xpath('.//span')
    index = [x.text for x in index]
    index = index

    odds, columns = [], []
    for col in valuesCols:
        col_header = col.find_element_by_xpath('.//div[contains(@class,"gl-MarketColumnHeader ")]')
        columns.append(col_header.text)
        o = col.find_elements_by_xpath('.//span[@class="gl-ParticipantOddsOnly_Odds"]')
        o = [float(x.text) for x in o]
        odds.append(o)
    odds = np.array(odds).T
    odds = pd.DataFrame(odds, index=index, columns=columns)
    return odds

def _parse_one_match(browser,league,saver):
    result={}
    result['league']=league
    def wait4elem(xpath_str,browser=browser,timeout=20):
        element = WebDriverWait(browser, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath_str))
        )
        return element
    def xpath(xpath_str,browser=browser):
        return browser.find_element_by_xpath(xpath_str)
    def xpaths(xpath_str,browser=browser):
        return browser.find_elements_by_xpath(xpath_str)
    
    minute=wait4elem('//div[@class="ipe-SoccerHeaderLayout_ExtraData "]').text
    result['minute']=parse_time(minute)
    
    team_names=xpaths('//div[@class="ipe-SoccerGridColumn_TeamName "]/div[@class="ipe-SoccerGridCell "]')
    result['name']=[x.text for x in team_names]
    logstr='parsing '+' '.join(result['name'])
    logstr.encode(encoding='utf-8')
    logging.info(logstr)

    #=====================================================================
    #======================ScoccerGridCells===============================
    corner=xpaths('//div[contains(@class,"ipe-SoccerGridColumn_ICorner ")]/div[@class="ipe-SoccerGridCell "]')
    result['corner']=[parse_gidcell_int(x.text) for x in corner]
    yellow=xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IYellowCard ")]/div[@class="ipe-SoccerGridCell "]')
    result['yellow']=[parse_gidcell_int(x.text) for x in yellow]
    red=xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IRedCard ")]/div[@class="ipe-SoccerGridCell "]')
    result['red']=[parse_gidcell_int(x.text) for x in red]
    throw=xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IThrowIn ")]/div[@class="ipe-SoccerGridCell "]')
    result['throw']=[parse_gidcell_int(x.text) for x in throw]
    freekick=xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IFreeKick ")]/div[@class="ipe-SoccerGridCell "]')
    result['freekick']=[parse_gidcell_int(x.text) for x in freekick]
    goalkick=xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IGoalKick ")]/div[@class="ipe-SoccerGridCell "]')
    result['goalkick']=[parse_gidcell_int(x.text) for x in goalkick]
    penalty=xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IPenalty ")]/div[@class="ipe-SoccerGridCell "]')
    result['penalty']=[parse_gidcell_int(x.text) for x in penalty]
    goal=xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IGoal ")]/div[@class="ipe-SoccerGridCell "]')
    result['goal']=[parse_gidcell_int(x.text) for x in goal]

    #==============================================================
    #======================All Stats===============================
    wait4elem('//div[contains(@class,"lv-ButtonBar ")]')
    button=xpaths('//div[contains(@class,"lv-ButtonBar_MatchLive lv-ButtonBar_MatchLive-1 ")]')
    if button:
        button[0].click()
        wait4elem('//div[@class="ml1-PossessionHistoryCanvas "]')
        titles=xpaths('//div[contains(@class,"ml1-AllStats_Title ")]')
        result['titles']=[x.text for x in titles]

        stats1=xpaths('//span[contains(@class, "ml1-SoccerStatsBar_MiniBarValue-1 ")]|//div[contains(@class,"ml1-StatWheel_Team1Text ")]')
        stats2=xpaths('//span[contains(@class, "ml1-SoccerStatsBar_MiniBarValue-2 ")]|//div[contains(@class,"ml1-StatWheel_Team2Text ")]')
        stats1=[parse_gidcell_int(x.text) for x in stats1]
        stats2=[parse_gidcell_int(x.text) for x in stats2]
        stats=[stats1,stats2]
        result['stats']=np.array(stats)
        '''
        hidden_button=browser.find_elements_by_xpath('//div[@class="ml1-MatchLiveSoccerModule_ShowHide "]')
        if hidden_button:
            hidden_button=hidden_button[0]
            for i in range(3):
                ActionChains(browser).move_to_element(button[0]).perform()
                ActionChains(browser).move_to_element(hidden_button).click(hidden_button).perform()
                if browser.find_elements_by_xpath('//div[contains(@class,"ml1-PitchAndEvents-eventsvisible ")]'):
                    break
                time.sleep(1)
            else:
                raise Exception("stats hidden button can't be click")

            #freekick
            freekick_button=wait4elem('//div[text()="Free Kicks"]')
            freekick_button.click()

            pitch=wait4elem('//div[@class="ml1-LocationEventsOverlay "]')
            home_fk=pitch.find_elements_by_xpath('.//div[@class="ml1-LocationEvent_FreekicksHome "]')
            away_fk=pitch.find_elements_by_xpath('.//div[@class="ml1-LocationEvent_FreekicksAway "]')

            pitch_pos=pitch.location
            pitch_size=pitch.size
            x_start=pitch_pos['x']
            width=pitch_size['width']
            home_fk_pos=[x.location for x in home_fk]
            home_fk_size=[x.size for x in home_fk]
            home_fk_x=[home_fk_pos[i]['x']-x_start+home_fk_size[i]['width']/2 for i in range(len(home_fk_pos))]
            home_fk_isfront=[1 if x>width/2 else 0 for x in home_fk_x]
            home_fk_front=sum(home_fk_isfront)
            home_fk_back=len(home_fk_isfront)-home_fk_front

            away_fk_pos=[x.location for x in away_fk]
            away_fk_size=[x.size for x in away_fk]
            away_fk_x=[away_fk_pos[i]['x']-x_start+away_fk_size[i]['width']/2 for i in range(len(away_fk_pos))]
            away_fk_isfront=[1 if x<width/2 else 0 for x in away_fk_x]
            away_fk_front=sum(away_fk_isfront)
            away_fk_back=len(away_fk_isfront)-away_fk_front
        else:
            home_fk_front=np.NaN
            home_fk_back=np.NaN
            away_fk_front=np.NaN
            away_fk_back=np.NaN

        result['home_fk_front']=home_fk_front
        result['home_fk_back']=home_fk_back
        result['away_fk_front']=away_fk_front
        result['away_fk_back']=away_fk_back
        '''
    #================================================================================
    #===================================Odds=========================================
    odds=parse_odd(browser)
    result['odds']=odds
    saver.save(result)
    logging.info('minute=%d parse finished.'%result['minute'])


def parse_odd(browser):
    market_groups = browser.find_elements_by_xpath('//div[@class="gl-MarketGroup "]')
    odds = {}
    for market in market_groups[0:min(8, len(market_groups))]:
        market_button = market.find_element_by_xpath('.//div[contains(@class,"gl-MarketGroupButton ")]')
        market_head = market_button.find_element_by_xpath('./span').text
        if 'gl-MarketGroup_Open ' not in market_button.get_attribute('class'):
            for i in range(3):
                try:
                    market_button.find_element_by_xpath('./span').click()
                    break
                except: continue
            else:
                logging.warning("market's menu can't be open")
                continue
            time.sleep(0.5)
        container = market.find_element_by_xpath('.//div[contains(@class,"gl-MarketGroup_Wrapper ")]/div')
        att = container.get_attribute('class')
        try:
            if '3-Way' in market_head:
                continue
            if att == 'gl-MarketGroupContainer ':
                odds[market_head] = parse_odd1(container)
            if att == 'gl-MarketGroupContainer gl-MarketGroupContainer_HasLabels ':
                odds[market_head] = parse_odd2(container)
        except Exception as e:
            logging.warning(traceback.format_exc())
            logging.warning("Error during parsing odds in %s" % market_head)
    return odds