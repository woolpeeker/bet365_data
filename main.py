from main_thread import MainThread
from CrawlerThread import CrawlerThread
from Saver import Saver
import utils
import os
import threading, queue, traceback, time, datetime
from collections import deque

class Manager:
    def __init__(self, name='Manager'):
        self.name = name
        self.logger = utils.get_logger(self.name)

        self.crawlerNum=2
        self.mainThread = MainThread()
        self.crawlerList = [CrawlerThread('crawlerThread_%d' % i) for i in range(self.crawlerNum)]

        self.save_thread = threading.Thread(target=self.save_result)
        self.save_thread.setDaemon(True)
        self.save_thread.start()

        #else
        self.oldMatches = deque(maxlen=500)

    def run(self):
        self.FLAG = {'last_restart': datetime.datetime.now()}
        while True:
            self.check_restart(15)
            self.deploy_jobs()
            self.logger.info('sleep 1 min.')
            time.sleep(60)


    def save_result(self):
        self.saver = Saver()
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

    # Find new matches,and put it to crawlerThreads.
    def deploy_jobs(self):
        self.logger.info('function deploy_jobs')
        teams_leagues=[]
        while True:
            try:
                elem = self.mainThread.out_queue.get_nowait()
                teams_leagues.append(elem)
            except queue.Empty as e:
                break
        i = 0
        for elem in teams_leagues:
            if elem in self.oldMatches:
                continue
            self.logger.info('add_match: %s' % str(elem))
            self.oldMatches.append(elem)
            self.crawlerList[i % self.crawlerNum].add_match(elem)
            i=i+1

    def check_restart(self, minites):
        self.logger.info('function check_restart')
        last_restart_delta = datetime.datetime.now() - self.FLAG['last_restart']
        if last_restart_delta.total_seconds() > 60 * minites:
            self.logger.info('time exceed, restart all process')
            self.taskkill(self.mainThread.process.pid)
            for p in self.crawlerList:
                self.taskkill(p.process.pid)
            self.oldMatches = deque(maxlen=100)
            self.mainThread = MainThread()
            self.crawlerList= [CrawlerThread('crawlerThread_%d' % i) for i in range(self.crawlerNum)]
            self.FLAG['last_restart'] = datetime.datetime.now()

    def taskkill(self, pid):
        self.logger.info('function taskkill')
        try:
            order='taskkill /PID %d /T /F' % pid
            self.logger.info('order: '+order)
            killtask = os.popen(order)
            ret = killtask.read()
            killtask.close()
            utils.clean_rust_mozprofile('C:\\Users\\luojiapeng\\AppData\\Local\\Temp')
            self.logger.info('taskkill result: ' + ret)
        except:
            self.logger.error(traceback.format_exc())

if __name__ == '__main__':
    manager = Manager()
    manager.run()