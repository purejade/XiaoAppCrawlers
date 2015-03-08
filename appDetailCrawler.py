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

IndexUrl = "http://app.mi.com/"
ROOT_DIR = 'G:'+os.sep+'FtpDir'+os.sep+'XIAO_APPS'+os.sep

PAGE_TXT = ROOT_DIR + 'page_txt'
APPS_DETAIL = ROOT_DIR + 'app_details'

app_detail_handler = codecs.open(APPS_DETAIL,'a+','utf-8')

page_txt_handler = codecs.open(PAGE_TXT,'a+','utf-8')
finished_handler = codecs.open(ROOT_DIR+'finished_app_id','a+','utf-8')

headers = {
    "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language" : "zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
    "Accept-Encoding" : "gzip, deflate",
    "Host" :  "app.mi.com",
    "User-Agent" :  "Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0",
    "Connection" : "keep-alive",
    "Cache-Control" : "no-cache",
}

freeze_time = 300

class XiaoAppsDetailsCrawler(threading.Thread):
    def __init__(self):
        super(XiaoAppsDetailsCrawler, self).__init__(name = 'xiaoappdetailcrawler')
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.setDaemon(True)
        self.page_queue = Queue.Queue()
        self.freeze_time = freeze_time


    def trim(self,text):
        text = text.replace('<br />',' ')
        text = text.replace('<br>',' ')
        return text

    def GetAppDetails(self,url):
        resp = self.session.get(url)
        with open('tmp.html','wb') as f:
            f.write(resp.content)
        content = resp.content
        url_infos = {}

        template = '<div class="intro-titles"><p>(.*?)</p><h3>(.*?)</h3><p class="special-font action"><b>分类：</b>(.*?)<span style="margin'
        app_intros = re.search(re.compile(template),content)
        company = app_intros.group(1)
        product = app_intros.group(2)
        category = app_intros.group(3)
        url_infos['company'] = company
        url_infos['product'] = product
        url_infos['category'] = category

        template = '<a href="/download/(\d+)" class="download">直接下载</a> </div></div>'
        app_info_down = re.search(re.compile(template),content)
        app_info_down = app_info_down.group(1)
        print app_info_down

        url_infos['app_info_down'] = app_info_down

        app_text_start = content.find('应用介绍')
        content = content[app_text_start:]
        template = '<p class="pslide">(.*?)</p>'
        app_text = re.search(re.compile(template),content)
        app_text = app_text.group(1)
        print self.trim(app_text)

        url_infos['app_text'] = self.trim(app_text)

        app_special_start = content.find('新版特性')
        content = content[app_special_start:]
        app_special_text = '<p class="pslide">(.*?)</p>'
        app_special_text = re.search(re.compile(app_special_text),content)
        app_special_text = app_special_text.group(1)
        print self.trim(app_special_text)

        url_infos['app_special_text'] = self.trim(app_special_text)

        app_relation_start = content.find('相关应用')
        template = '<a href="/detail/(\d+)">'
        app_relation = re.compile(template)
        app_relations = re.findall(app_relation,content)
        app_relations_set = []
        for id in app_relations:
            app_relations_set.append(id)
        print set(app_relations_set)
        url_infos['app_relations_set'] = set(app_relations_set)
        app_detail_handler.write(json.dumps(url_infos))
        app_detail_handler.write(os.linesep)


    def run(self):
        try:
            url = 'http://app.mi.com/detail/78008'
            self.GetAppDetails(url)
        except Exception as e:
            print str(e)
            pass


if __name__ == "__main__":

    appDetailsCrawler = XiaoAppsDetailsCrawler()
    appDetailsCrawler.start()

    appDetailsCrawler.join()

    print "over"