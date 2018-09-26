
import datetime

def log(string):
    now=datetime.datetime.now()
    print('[%s] %s'%(now, string))