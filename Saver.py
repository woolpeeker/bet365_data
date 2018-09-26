
import os, glob, re
import pandas as pd
import numpy as np
import datetime
import pickle
from utils import log

class Saver:
    def __init__(self,prefix_path):
        self.prefix_path=prefix_path
        self.file=prefix_path+'.pkl'
        self.bak_fn=self._get_new_bak_filename()
        if os.path.exists(self.file):
            self.data=pickle.load(open(self.file,'rb'))
        else:
            self.data=pd.DataFrame(columns=['name','minute','date','data'])

    def save(self,input):
        #find the kickoff date and check need store
        today=datetime.date.today()
        name=' '.join(input['name'])
        sel_name=self.data[self.data['name']==name]
        if sel_name.empty:
            date=today
        else:
            sel_name.sort_values(['date'])
            delta=datetime.date.today()-sel_name.iloc[-1]['date']
            if delta.total_seconds()<2*25*3600:
                date=sel_name.iloc[-1]['date']
            else:
                date=today

        sample={}
        sample['name']=name
        sample['date']=date
        sample['minute']=input['minute']
        sample['data']=input
        self.data=self.data.append(sample,ignore_index=True)
        if len(self.data)%1000000==0:
            self.flush()

    def _get_new_bak_filename(self):
        filelist=glob.glob("%s.*.pkl"%self.prefix_path)
        filelist=sorted(filelist)
        if not filelist:
            num=0
        else:
            num=max([int(re.search('(\d+).pkl',x).group(1)) for x in filelist])
            num=int(num)+1
        bak_file='%s.%d.pkl'%(self.prefix_path,num)
        return bak_file

    def flush(self):
        log('Saver flush data...')
        pickle.dump(self.data,open(self.bak_fn,'wb'))
        pickle.dump(self.data,open(self.file,'wb'))