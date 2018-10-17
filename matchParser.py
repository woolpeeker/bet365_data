import logging, re, time
import traceback
import numpy as np
import pandas as pd

from Crawler import Crawler


class MatchParser(Crawler):
    def __init__(self, browser):
        self.browser = browser

    def parse(self, match):
        result = {}
        result.update(self.parse_time())
        result.update(self.parse_gridcell())
        result.update(self.parse_all_stats())
        result.update(self.parse_odd())
        return result

    def parse_time(self):
        result = {}
        minute = self.wait4elem('//div[@class="ipe-SoccerHeaderLayout_ExtraData "]').text
        result['minute'] = parse_time(minute)

        team_names = self.xpaths('//div[@class="ipe-SoccerGridColumn_TeamName "]/div[@class="ipe-SoccerGridCell "]')
        result['team_name_h'] = team_names[0].text
        result['team_name_a'] = team_names[1].text
        logstr = 'parsing ' + ' '.join(result['name'])
        logstr.encode(encoding='utf-8')
        logging.info(logstr)
        return result

    def parse_gridcell(self):
        tmp_result = {}
        xpath, xpaths = self.xpath, self.xpaths
        corner = self.xpaths(
            '//div[contains(@class,"ipe-SoccerGridColumn_ICorner ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['corner'] = [parse_gidcell_int(x.text) for x in corner]
        yellow = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IYellowCard ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['yellow'] = [parse_gidcell_int(x.text) for x in yellow]
        red = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IRedCard ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['red'] = [parse_gidcell_int(x.text) for x in red]
        throw = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IThrowIn ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['throw'] = [parse_gidcell_int(x.text) for x in throw]
        freekick = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IFreeKick ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['freekick'] = [parse_gidcell_int(x.text) for x in freekick]
        goalkick = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IGoalKick ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['goalkick'] = [parse_gidcell_int(x.text) for x in goalkick]
        penalty = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IPenalty ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['penalty'] = [parse_gidcell_int(x.text) for x in penalty]
        goal = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IGoal ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['goal'] = [parse_gidcell_int(x.text) for x in goal]

        result={}
        for k,v in tmp_result.items():
            result[k+'_h'],result[k+'_a']=v
        return result

    def parse_all_stats(self):
        result = {}
        xpath, xpaths = self.xpath, self.xpaths
        self.wait4elem('//div[contains(@class,"lv-ButtonBar ")]')
        button = xpaths('//div[contains(@class,"lv-ButtonBar_MatchLive lv-ButtonBar_MatchLive-1 ")]')
        if button:
            button[0].click()
            self.wait4elem('//div[@class="ml1-PossessionHistoryCanvas "]')
            titles = xpaths('//div[contains(@class,"ml1-AllStats_Title ")]')
            result['titles'] = [x.text for x in titles]

            stats1 = xpaths(
                '//span[contains(@class, "ml1-SoccerStatsBar_MiniBarValue-1 ")]|//div[contains(@class,"ml1-StatWheel_Team1Text ")]')
            stats2 = xpaths(
                '//span[contains(@class, "ml1-SoccerStatsBar_MiniBarValue-2 ")]|//div[contains(@class,"ml1-StatWheel_Team2Text ")]')
            stats1 = [parse_gidcell_int(x.text) for x in stats1]
            stats2 = [parse_gidcell_int(x.text) for x in stats2]
            stats = [stats1, stats2]
            result['stats'] = np.array(stats)
        return result

    def parse_odd(self):
        xpath, xpaths = self.xpath, self.xpaths
        market_groups = xpaths('//div[@class="gl-MarketGroup "]')
        for market in market_groups[0:min(8, len(market_groups))]:
            fulltime_group = market.find_element_by_xpath('.//span[contains(@class,"gl-MarketGroupButton_Text")][text()="Fulltime Result"]/../..')
            self.xpaths('.//span[@class="gl-Participant_Odds"]',section=fulltime_group)
            try:
                odds = [float(x.text) for x in odds]
            except ValueError as e:
                odds = [np.NaN] * 3
        result={'odds_home':odds[0],
                'odds_draw':odds[1],
                'odds_away':odds[2]}
        return result


def parse_time(string):
    match_result = re.match('(\d+):(\d+)', string)
    if match_result:
        minute = int(match_result.group(1))
        second = int(match_result.group(2))
        return minute
    else:
        logging.warning('parse time wrong format')
        return np.NaN


def parse_gidcell_int(string):
    # used for SoccerGridCell int
    # temperarily for stats
    if string.isdigit():
        return int(string)
    elif string == '':
        return np.NaN
    else:
        logging.warning('Raise ValueError:GridCell Int:%d' % string)
        raise ValueError('ValueError:GridCell Int:%d' % string)
