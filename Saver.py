import datetime
import traceback

import pymysql
from utils import get_logger

sql_cmd = {
    'create_table': "CREATE TABLE inplay ( \
 id int NOT NULL AUTO_INCREMENT, PRIMARY KEY (id),\
 insert_time datetime NOT NULL, \
 crawler varchar(255), \
 fp char(255) NOT NULL, \
 league char(255), date Date NOT NULL, \
 team_h char(255) NOT NULL, team_a char(255) NOT NULL, minute smallint NOT NULL, \
 corner_h smallint, corner_a smallint, \
 yellow_h smallint, yellow_a smallint, \
 red_h smallint, red_a smallint, \
 throw_h smallint, throw_a smallint, \
 freekick_h smallint, freekick_a smallint, \
 goalkick_h smallint, goalkick_a smallint, \
 penalty_h smallint, penalty_a smallint, \
 goal_h smallint, goal_a smallint, \
 attacks_h smallint, attacks_a smallint, \
 dangerous_attacks_h smallint, dangerous_attacks_a smallint, \
 possession_h smallint, possession_a smallint, \
 on_target_h smallint, on_target_a smallint, \
 off_target_h smallint, off_target_a smallint, \
 odds_fulltime varchar(255), odds_double varchar(255), \
 odds_corners varchar(255), odds_asian_corners varchar(255),\
 odds_match_goals varchar(255), odds_alter_goals varchar(255), \
 odds_goals_odd_even varchar(255), odds_most_corners varchar(255));"
}


class Saver:
    def __init__(self, name='saver'):
        self.name=name
        self.logger=get_logger(self.name)
        self.conn = pymysql.connect(host="localhost", user="root", password="123456", database="soccer", charset='utf8', autocommit=True)
        if not self.exist_table():
            self.create_table()

    def exist_table(self):
        sql = "SELECT table_name FROM information_schema.TABLES WHERE table_schema = 'soccer' and table_name = 'inplay';"
        with self.conn.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchone()
        if result is None:
            self.logger.info("table doesn't exists")
            return False
        else:
            self.logger.info('table exists')
            return True

    def create_table(self):
        self.logger.info('create_table')
        sql = sql_cmd['create_table']
        with self.conn.cursor() as cur:
            try:
                cur.execute(sql)
            except:
                self.logger.error(traceback.format_exc())
                self.conn.rollback()
        if not self.exist_table():
            self.logger.error('create table Fails.')
            raise Exception('create table Fails.')
        else:
            self.logger.info('create table successful')

    def sql_query(self, sql, sql_args):
        self.logger.debug('sql_query: %s args: %s' % (sql, sql_args))
        with self.conn.cursor() as cur:
            cur.execute(sql, sql_args)
            result = cur.fetchall()
        return result

    def process_vals(self,vals):
        converted=[]
        for v in vals:
            if v is None:
                converted.append(None)
            elif isinstance(v, datetime.date):
                converted.append(str(v))
            elif isinstance(v,(int, float, str)):
                converted.append(v)
            else:
                converted.append(str(v))
                self.logger.error("Unexpected datatype, just str it: %s" % type(v))
        return converted

    def sql_insert(self, sample):
        self.logger.debug('sql_insert: %s' % sample)
        assert type(sample) == dict
        try:
            sample['insert_time'] = datetime.datetime.now()
            keys = ','.join(sample.keys())
            vals = self.process_vals(sample.values())
            holder=lambda num: ','.join(['%s']*num)
            sql = 'INSERT INTO inplay ({keys}) VALUES ({vals});'.format(keys=keys,vals=holder(len(vals)))
            sql_args=vals
            self.logger.debug('sql: %s args: %s'%(sql,sql_args))
            with self.conn.cursor() as cur:
                cur.execute(sql, sql_args)
        except Exception as e:
            self.logger.error('sql_insert error: %s' % sample)
            self.logger.error(traceback.format_exc())
        self.logger.debug('sql_insert success: %s' % sample)

    def insert(self, input):
        self.logger.debug('insert: %s'%input)
        today = datetime.date.today()
        same_team_set = self.sql_query("SELECT id, date, minute FROM inplay WHERE team_h=%s and team_a=%s ORDER BY id;",(input['team_h'], input['team_a']))
        if not same_team_set:
            self.logger.debug('same_team_set is empty')
            date = today
        else:
            id, last_date, last_minute = same_team_set[-1]
            delta = today - last_date
            if delta.total_seconds() < 24 * 3600:
                date = last_date
            else:
                date = today
            if input['minute'] == 90 and input['minute'] < last_minute:
                input['minute'] = -1
            if date == last_date and input['minute'] == last_minute:
                return
        input['date'] = date
        input['fp'] = '##'.join([str(input[k]) for k in ['league', 'date', 'team_h', 'team_a']])
        self.sql_insert(input)
