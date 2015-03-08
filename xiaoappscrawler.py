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

page_txt_handler = codecs.open(PAGE_TXT,'a+','utf-8')
finished_handler = codecs.open(ROOT_DIR+'finished_app_id','a+','utf-8')
app_detail_handler = codecs.open(APPS_DETAIL,'a+','utf-8')

# finished_handler = codecs.open(ROOT_DIR+'finished_app_id','a+','utf-8')
CategoryQueue = Queue.Queue()

FINISHED_MAP = {}

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

class XiaoAppsCrawlerByCategory(threading.Thread):
    def __init__(self,name):
        super(XiaoAppsCrawlerByCategory,self).__init__(name=name)
        self.setDaemon(True)
        self.name = name
        self.setDaemon(True)
        self.page_queue = Queue.Queue()
        self.session = requests.session()
        self.session.headers.update(headers)

    def GetAppDetails(self,url):
        try:
            app_code = url[url.find('/')+1:]
            if FINISHED_MAP.has_key(app_code):
                return

            resp = self.session.get(url)
            content = resp.content
            url_infos = {}


            url_infos['app_code'] = app_code

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
            # print app_info_down

            url_infos['app_info_down'] = app_info_down

            app_text_start = content.find('应用介绍')
            content = content[app_text_start:]
            template = '<p class="pslide">(.*?)</p>'
            app_text = re.search(re.compile(template),content)
            app_text = app_text.group(1)
            # print self.trim(app_text)

            url_infos['app_text'] = self.trim(app_text)

            app_special_start = content.find('新版特性')
            content = content[app_special_start:]
            app_special_text = '<p class="pslide">(.*?)</p>'
            app_special_text = re.search(re.compile(app_special_text),content)
            app_special_text = app_special_text.group(1)
            # print self.trim(app_special_text)

            url_infos['app_special_text'] = self.trim(app_special_text)

            app_relation_start = content.find('相关应用')
            template = '<a href="/detail/(\d+)">'
            app_relation = re.compile(template)
            app_relations = re.findall(app_relation,content)
            app_relations_set = []
            for id in app_relations:
                app_relations_set.append(id)
            # print set(app_relations_set)
            url_infos['app_relations_set'] = set(app_relations_set)
            app_detail_handler.write(json.dumps(url_infos))
            app_detail_handler.write(os.linesep)
            finished_handler.write(app_code)
            finished_handler.write(os.linesep)
        except Exception as e:
            print str(e)
            print url

    def GetAllPagesByCategory(self,category_id):

        filename = codecs.open(ROOT_DIR + str(category_id),'a+','utf-8')
        index = 0
        while True:
            url = 'http://app.mi.com/categotyAllListApi?page='+str(index)+'&categoryId='+str(category_id)+'&pageSize=1000'
            resp = self.session.get(url)
            try:
                jsonData = json.loads(resp.content)
            except Exception as e:
                print str(e)
                break
            if not jsonData:
                break
            if not jsonData['data']:
                break
            for app in jsonData["data"]:
                filename.write(json.dumps(app))
                filename.write(os.linesep)
                self.page_queue.put('http://app.mi.com/detail/'+str(app["appId"]))
                detail_url = 'http://app.mi.com/detail/'+str(app["appId"])
                self.GetAppDetails(detail_url)
                page_txt_handler.write('http://app.mi.com/detail/'+str(app["appId"]))
                page_txt_handler.write(os.linesep)
            index = index + 1
            time.sleep(5)
        print category_id + 'over'
        filename.close()

    def run(self):
        while CategoryQueue.empty() == False:
            try:
                category_id = CategoryQueue.get()
                self.GetAllPagesByCategory(category_id)
                CategoryQueue.task_done()
            except Exception as e:
                print str(e)
                print category_id
                CategoryQueue.task_done()

class XiaoAppsCrawler():
    def __init__(self):

        self.session = requests.Session()
        self.session.headers.update(headers)
        self.freeze_time = freeze_time


    def cmp(self,x,y):
        if int(x) < int(y):
            return -1
        elif int(x) > int(y):
            return 1
        else:
            return 0

    def GetAllCategories(self):

        resp = self.session.get(IndexUrl)
        open('index.html','wb').write(resp.content)

        categories = r'<a  href="/category/(\d+?)">'
        categories_pattern = re.compile(categories)
        if not resp:
            print "the inet is not connected!"
            return
        categories_urls = categories_pattern.findall(resp.content)
        sortedArray = sorted(set(categories_urls),cmp = self.cmp ,reverse=False)
        for url in sortedArray:
            # index_url = IndexUrl+'category/'+str(url)
            # self.GetAllPagesByCategory(url)
            CategoryQueue.put(str(url))
            break



        # for thread in threads:
        #     thread.join()

        # time.sleep(100)


    def run(self):
        self.GetAllCategories()

if __name__ == "__main__":

    if os.path.exists(ROOT_DIR+'finished_app_id'):
        with open(ROOT_DIR+'finished_app_id') as f:
            for line in f:
                line = line.strip()
                if line:
                    FINISHED_MAP[line] = 1

    xiaoAppsCrawler = XiaoAppsCrawler()

    xiaoAppsCrawler.run()

    xiaoappscrawlerbycategory = XiaoAppsCrawlerByCategory('0')
    # threads.append(xiaoappscrawlerbycategory)
    xiaoappscrawlerbycategory.start()

    xiaoappscrawlerbycategory.join()
    print "over"