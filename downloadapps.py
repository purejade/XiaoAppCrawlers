#!/usr/bin/env python
#-*-coding: utf-8-*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import threading
import time
import re
import os
import requests
import Queue
import json
import codecs
import urllib2

IndexUrl = "http://app.mi.com/"
ROOT_DIR = 'G:'+os.sep+'FtpDir'+os.sep+'NEW_XIAO_APPS'+os.sep+'APK'+os.sep

finished_downloader_file = ROOT_DIR+'finished_download_id'


finished_downloader = codecs.open(ROOT_DIR+'finished_download_id','a+','utf-8')

failed_downloader = codecs.open(ROOT_DIR+'failed_download_id','a+','utf-8')

# finished_handler = codecs.open(ROOT_DIR+'finished_app_id','a+','utf-8')
AppIdQueue = Queue.Queue()

FINISHED_MAP = {}

headers = {
    "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language" : "zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
    "Accept-Encoding" : "gzip, deflate,sdch",
    "Host" :  "app.mi.com",
    "User-Agent" :  "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36",
    "Connection" : "keep-alive",
    "Cache-Control" : "no-cache",
}

freeze_time = 300

lock = threading.Lock()

class DownloaderApps(threading.Thread):
    def __init__(self,name):
        super(DownloaderApps,self).__init__(name=name)
        self.setDaemon(True)
        self.name = name
        self.session = requests.session()
        self.session.headers.update(headers)

    def Downloader(self,url_id):

        apkfilename = ROOT_DIR+str(url_id)+'.apk'
        print url_id+' is downloading....'
        try:
            # self.session.headers['Referer'] = 'http://app.mi.com/detail/'+str(url_id)
            # print 'http://app.mi.com/download/'+str(url_id)
            self.session.headers['Host'] = 'app.mi.com'
            resp = self.session.get('http://app.mi.com/download/'+str(url_id),timeout = 100,allow_redirects=False)
            if not resp or resp.status_code != 200:
                failed_downloader.write(url_id)
                failed_downloader.write(os.linesep)
                return
            content = resp.content
            template = '<a href="(.*?)">here</a>'
            real_url = re.compile(template)
            real_url = re.search(real_url,content).group(1)
            apkrealname = real_url[real_url.rfind('/')+1:]
            apkrealname = urllib2.unquote(apkrealname)
            self.session.headers['Host'] = 'f3.market.xiaomi.com'
            resp = self.session.get(real_url,timeout = 100)
            if not resp:
                failed_downloader.write(url_id)
                failed_downloader.write(os.linesep)
                return
            content = resp.content
            with open(apkfilename,'wb') as f:
                f.write(content)
            if lock.acquire():
                finished_downloader.write(url_id+'|'+apkrealname)
                print url_id+' is over!'
                finished_downloader.write(os.linesep)
                lock.release()
        except Exception as e:
            print str(e)
            print url_id
            failed_downloader.write(url_id)
            failed_downloader.write(os.linesep)

    def run(self):
        while AppIdQueue.empty() == False:
            try:
                app_id = AppIdQueue.get()
                self.Downloader(app_id)
                AppIdQueue.task_done()
            except Exception as e:
                print str(e)
                print app_id
                AppIdQueue.task_done()


if __name__ == "__main__":

    if os.path.exists(finished_downloader_file):
        with open(finished_downloader_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    FINISHED_MAP[line] = 1

    start = time.clock()
    ROOT = 'G:'+os.sep+'FtpDir'+os.sep+'NEW_XIAO_APPS'+os.sep
    app_handler = codecs.open(ROOT+'finished_app_id','rb','utf-8')
    for app_id in app_handler:
        app_id = app_id.strip()
        if app_id:
           AppIdQueue.put(app_id)

    threads = []
    thraed_num = 8
    for i in range(thraed_num):
        downloader = DownloaderApps(str(i))
        threads.append(downloader)
        downloader.start()

    # url_id = '42036'
    # downloader = DownloaderApps('0')
    # downloader.Downloader(url_id)

    for thread in threads:
        thread.join()

    print time.clock() - start
    print "over"
