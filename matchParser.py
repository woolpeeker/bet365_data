import logging, re, time
import traceback
import numpy as np
import pandas as pd

from Crawler import Crawler

#TODO: add parse more odds, such as corner, goals
class MatchParser(Crawler):
    def __init__(self, browser, logger):
        self.browser = browser
        self.logger=logger

    def parse(self, match):
        self.logger.info('function MatchParser.parse args:%s' % str(match))
        for _ in range(2):
            try:
                result = {'league': match[1]}
                result.update(self.parse_minute())
                result.update(self.parse_gridcell())
                result.update(self.parse_all_stats())
                result.update(self.parse_odd())
                return result
            except Exception as e:
                self.logger.error('Error when parsing match %s' % str(match))
                self.logger.error(traceback.format_exc())
                self.logger.warning('MatchParser refresh browser')
                self.browser.refresh()
        return {}

    def parse_minute(self):
        self.logger.debug('function parse_minute')
        result = {}
        minute = self.wait4elem('//div[@class="ipe-SoccerHeaderLayout_ExtraData "]').text
        result['minute'] = self.__parse_time__(minute)

        team_names = self.xpaths('//div[@class="ipe-SoccerGridColumn_TeamName "]/div[@class="ipe-SoccerGridCell "]')
        result['team_name_h'] = team_names[0].text
        result['team_name_a'] = team_names[1].text
        self.logger.debug('result:%s'%result)
        return result

    def parse_gridcell(self):
        self.logger.debug('function parse_gridcell')
        tmp_result = {}
        xpath, xpaths = self.xpath, self.xpaths
        corner = self.xpaths(
            '//div[contains(@class,"ipe-SoccerGridColumn_ICorner ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['corner'] = [self.__parse_gidcell_int__(x.text) for x in corner]
        yellow = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IYellowCard ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['yellow'] = [self.__parse_gidcell_int__(x.text) for x in yellow]
        red = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IRedCard ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['red'] = [self.__parse_gidcell_int__(x.text) for x in red]
        throw = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IThrowIn ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['throw'] = [self.__parse_gidcell_int__(x.text) for x in throw]
        freekick = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IFreeKick ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['freekick'] = [self.__parse_gidcell_int__(x.text) for x in freekick]
        goalkick = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IGoalKick ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['goalkick'] = [self.__parse_gidcell_int__(x.text) for x in goalkick]
        penalty = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IPenalty ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['penalty'] = [self.__parse_gidcell_int__(x.text) for x in penalty]
        goal = xpaths('//div[contains(@class,"ipe-SoccerGridColumn_IGoal ")]/div[@class="ipe-SoccerGridCell "]')
        tmp_result['goal'] = [self.__parse_gidcell_int__(x.text) for x in goal]

        result = {}
        for k, v in tmp_result.items():
            result[k + '_h'], result[k + '_a'] = v

        self.logger.debug('result: %s' % result)
        return result

    def parse_all_stats(self):
        self.logger.debug('function parse_all_stats')
        result = {}
        xpath, xpaths = self.xpath, self.xpaths
        self.wait4elem('//div[contains(@class,"lv-ButtonBar ")]')
        button = xpaths('//div[contains(@class,"lv-ButtonBar_MatchLive lv-ButtonBar_MatchLive-1 ")]')
        if button:
            tmp_result = {}
            button[0].click()
            self.wait4elem('//div[@class="ml1-PossessionHistoryCanvas "]')
            titles = xpaths('//div[contains(@class,"ml1-AllStats_Title ")]')
            titles = [x.text for x in titles]

            stats1 = xpaths(
                '//span[contains(@class, "ml1-SoccerStatsBar_MiniBarValue-1 ")]|//div[contains(@class,"ml1-StatWheel_Team1Text ")]')
            stats2 = xpaths(
                '//span[contains(@class, "ml1-SoccerStatsBar_MiniBarValue-2 ")]|//div[contains(@class,"ml1-StatWheel_Team2Text ")]')
            stats1 = [self.__parse_gidcell_int__(x.text) for x in stats1]
            stats2 = [self.__parse_gidcell_int__(x.text) for x in stats2]
            stats = [stats1, stats2]
            stats = np.array(stats)

            for i in range(len(titles)):
                result[titles[i] + '_h'] = stats[0, i]
                result[titles[i] + '_a'] = stats[1, i]
        self.logger.debug('result: %s' % result)
        return result

    def parse_odd(self):
        self.logger.debug('function parse_odd')
        xpath, xpaths = self.xpath, self.xpaths
        market_groups = xpaths('//div[@class="gl-MarketGroup "]')
        for market in market_groups[0:min(8, len(market_groups))]:
            fulltime_group = market.find_elements_by_xpath(
                './/span[contains(@class,"gl-MarketGroupButton_Text")][text()="Fulltime Result"]/../..')
            if fulltime_group:
                odds=xpaths('.//span[@class="gl-Participant_Odds"]', section=fulltime_group[0])
                try:
                    odds = [float(x.text) for x in odds]
                except ValueError as e:
                    odds = [np.NaN] * 3
            else:
                odds = [np.NaN] * 3
        result = {'odds_home': odds[0],
                  'odds_draw': odds[1],
                  'odds_away': odds[2]}
        self.logger.debug('result: %s' % result)
        return result


    def __parse_time__(self, string):
        match_result = re.match('(\d+):(\d+)', string)
        if match_result:
            minute = int(match_result.group(1))
            second = int(match_result.group(2))
            return minute
        else:
            self.logger.warning('parse time wrong format')
            return np.NaN


    def __parse_gidcell_int__(self, string):
        # used for SoccerGridCell int
        # temperarily for stats
        if string.isdigit():
            return int(string)
        elif string == '':
            return np.NaN
        else:
            self.logger.warning('Raise ValueError:GridCell Int:%d' % string)
            raise ValueError('ValueError:GridCell Int:%d' % string)
