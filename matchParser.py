import re
import traceback
import json

from Crawler import Crawler

class MatchParser(Crawler):
    def __init__(self, browser, logger):
        super(MatchParser, self).__init__('Match_parser')
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
                result = self.key_convert(result)
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
        result['team_h'] = team_names[0].text
        result['team_a'] = team_names[1].text
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

            for i in range(len(titles)):
                result[titles[i] + '_h'] = stats[0][i]
                result[titles[i] + '_a'] = stats[1][i]
        self.logger.debug('result: %s' % result)
        return result

    def parse_odd(self):
        result={}
        self.logger.debug('function parse_odd')
        xpath, xpaths = self.xpath, self.xpaths
        markets = xpaths('//div[@class="ipe-EventViewDetail_MarketGrid gl-MarketGrid "]')
        if not markets:
            self.logger.warning('No market_groups')
            return result
        markets=markets[0]

        #Full time odds
        fulltime = self._parse_odds_market(markets,'Fulltime Result')
        result['odds_fulltime']=json.dumps(fulltime)

        #double chance
        double = self._parse_odds_market(markets,'Double Chance')
        result['odds_double']=json.dumps(double)

        #goals
        match_goals=self._parse_odds_market(markets, 'Match Goals')
        alter_goals=self._parse_odds_market(markets, 'Alternative Match Goals')
        odd_even=self._parse_odds_market(markets, 'Goals Odd/Even')
        result['odds_match_goals']=json.dumps(match_goals)
        result['odds_alter_goals']=json.dumps(alter_goals)
        result['odds_goals_odd_even']=json.dumps(odd_even)

        #corner
        corners=self._parse_odds_market(markets, 'Match Corners')
        result['odds_corners'] = json.dumps(corners)
        asian_corners= self._parse_odds_market(markets, 'Asian Corners')
        result['odds_asian_corners'] = json.dumps(asian_corners)
        most_corners = self._parse_odds_market(markets, 'Most Corners')
        result['odds_most_corners']=json.dumps(most_corners)

        self.logger.debug('result: %s' % result)
        return result

    def _parse_odds_market(self, markets, name):
        odds = []
        group = markets.find_elements_by_xpath(
            './/span[contains(@class,"gl-MarketGroupButton_Text")][text()="%s"]/../..' % name)
        if group:
            group = group[0]
            if group.find_elements_by_xpath('.//span[@class="gl-MarketGroupButton_CurrentlySuspended"]'):
                self.logger.info('%s is suspended. Pass' % name)
                return odds
            market_button =  group.find_element_by_xpath('.//span[contains(@class,"gl-MarketGroupButton_Text")][text()="%s"]/..' % name)
            if 'gl-MarketGroup_Open' not in market_button.get_attribute("class"):
                market_button.click()
                self.wait4elem('.//span[contains(@class,"gl-MarketGroupButton_Text")][text()="%s"]/../../div[contains(@class, "gl-MarketGroup_Wrapper")]' % name)
            odds = self.xpaths('.//span', section=group)
            odds = [x.text for x in odds]
        return odds

    def key_convert(self,result):
        converted={}
        for k,v in result.items():
            k=k.lower().replace('%','')
            k=re.sub(' +','_',k)
            k = re.sub('_+', '_', k)
            converted[k]=v
        return converted

    def __parse_time__(self, string):
        match_result = re.match('(\d+):(\d+)', string)
        if match_result:
            minute = int(match_result.group(1))
            second = int(match_result.group(2))
            return minute
        else:
            self.logger.warning('parse time wrong format')
            return None


    def __parse_gidcell_int__(self, string):
        # used for SoccerGridCell int
        # temperarily for stats
        if string.isdigit():
            return int(string)
        elif string == '':
            return None
        else:
            self.logger.warning('Raise ValueError:GridCell Int:%d' % string)
            raise ValueError('ValueError:GridCell Int:%d' % string)