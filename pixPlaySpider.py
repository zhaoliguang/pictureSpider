__author__ = 'pizza'
#coding:utf-8
import urllib2
import urllib
import re
import tool
import os
import sys
import time
import socket
import Queue
import threading
from functools import wraps
#图片Url链接Queue
imageUrlList = Queue.Queue(0)
#捕获图片数量
imageGetCount = 0
#已下载图片数量
imageDownloadCount = 0
empty = False

class Spider:

    #页面初始化
    def __init__(self):
        self.siteURL = 'http://pixabay.com/zh/photos/'
        self.tool = tool.Tool()
        self.postdata={
            'username':'pizzaZhao',
            'password':'pizzaZhao',
            'next':''
        }
        self.sleep_download_time = 2
        self.timeout = 60
        self.count = 0
        self.headers = {
            "User-Agent":'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
        }
        
    def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
        def deco_retry(f):

            @wraps(f)
            def f_retry(*args, **kwargs):
                mtries, mdelay = tries, delay
                while mtries > 1:
                    try:
                        return f(*args, **kwargs)
                    except ExceptionToCheck as e:
                        msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                        if logger:
                            logger.warning(msg)
                        else:
                            print(msg)
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                return f(*args, **kwargs)

            return f_retry  # true decorator
        return deco_retry
    
    @retry(Exception, tries=5)
    def getPage(self,content,pageIndex):
        url = self.siteURL +"?q=" + str(content) +"&horizontal=horizontal&order=best&cat="+"&pagi=" + str(pageIndex)
        postData = urllib.urlencode(self.postdata)
        time.sleep(self.sleep_download_time)
        request = urllib2.Request(url, postData, self.headers)

        try:
           
           response = urllib2.urlopen(request)
           #print u'response:',response
           responseText = response.read()
           #print u'responseText:',responseText
           response.close()
           return responseText

        except urllib2.HTTPError, e:
            time.sleep(20)
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code

        except urllib2.URLError, e:
            time.sleep(20)
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
        except socket.timeout as e:
            print "-----socket timout:",e
        except Exception , e:
            time.sleep(10)
            print u'解码网页内容错误:',e


    def getAllImg(self,content,pageIndex):
        page = self.getPage(content,pageIndex)
        #print u'page:',page
        if not page:
            return [];
        pattern = re.compile('<div id="photo_grid" class="flex_grid">(.*?)<span id="paginator_clone"',re.S)
        #图片列表
        try:
            
            content = re.search(pattern, str(page))
            # print u'content:',content
            #从代码中提取图片地址
            patternImg = re.compile('<img.*?src="(.*?)"',re.S)
            
            if content and content.group(1):
                images = re.findall(patternImg,content.group(1))
                print u'images:',images
                return images
            return [];
        except Exception , e:
            print u'获取图片错误:',e

    
	
	
    #传入图片地址，文件名，保存单张图片
    @retry(Exception, tries=5)
    def saveImg(self,imageURL,fileName):
#        print u"图片url地址:",imageURL
        try:
            time.sleep(self.sleep_download_time)
            request = urllib2.urlopen(imageURL)
            data = request.read()
            request.close()
            f = open(fileName, 'wb')
            f.write(data)
            f.close()


        except UnicodeDecodeError as e:
            print '-----UnicodeDecodeErrorurl:',imageURL
        except urllib2.HTTPError, e:
            time.sleep(20)
            print 'The server couldn\'t fulfill the request.',imageURL
            print 'Error code: ', e.code

        except urllib2.URLError, e:
            time.sleep(20)
            print 'We failed to reach a server.',imageURL
            print 'Reason: ', e.reason

        except socket.timeout as e:
            print "-----socket timout:",imageURL
        except Exception , e:
            print u'保存图片错误:',e
            #创建新目录
    def mkdir(self,path):
        path = path.strip()
        rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/\:*?"<>|'
        path = re.sub(rstr, "", path)
        isExists=os.path.exists(path)
        # 判断结果
        if not isExists:
            os.makedirs(path)
            return True
        else:
            # 如果目录存在则不创建，并提示目录已存在
            return False

    #将一页图片保存起来
    def saveImageInfo(self,content,pageIndex):
        
        images = self.getAllImg(content,pageIndex)
        
        global empty
        global imageUrlList
        global imageGetCount
        if not images:
            print u"查找不到资源：",content
            empty = True
            return
        else:
            empty = False
            for image in images:
                self.mkdir(content)
                if imageDownloadCount > 70:
                    print u"该资源下载到达70个,停止查找"
                    break
                contentText = ""
                fileName = ""
                index2 = image.index('.')
                fileName = content + "/" + image[-16:]

                imagerurl = 'http://pixabay.com'+image
                imageUrlList.put(imagerurl)
                global imageGetCount
                imageGetCount = imageGetCount+1
#                self.saveImg(imagerurl,fileName)
                time.sleep(2)
                download = getImage(fileName)
                download.start()


    def saveImagesInfo(self,content,start,end):
        global empty
        global imageDownloadCount
        for i in range(start,end+1):
            if empty or imageDownloadCount>70:
                return
            self.saveImageInfo(content,i)
            print u'查找不到内容退出saveImageInfo'


class getImage(threading.Thread):
    def __init__(self,filename):
        threading.Thread.__init__(self)
        self.filename = filename
    def run(self):
        print u'开始下载图片...'

        while(True):
            global imageUrlList
            global imageDownloadCount
            global imageGetCount
            print u'目前捕获图片数量:',imageGetCount
            print u'已下载图片数量:',imageDownloadCount
            imageURL = imageUrlList.get()
            print u'该下载图片地址',imageURL
            try:
                time.sleep(2)
                request = urllib2.urlopen(imageURL)
                data = request.read()
                request.close()
                f = open(self.filename, 'wb')
                f.write(data)
                f.close()

                imageDownloadCount = imageDownloadCount + 1
                if(imageUrlList.empty()):
                    break

            except UnicodeDecodeError as e:
                print '-----UnicodeDecodeErrorurl:',imageURL
            except urllib2.HTTPError, e:
                time.sleep(20)
                print 'The server couldn\'t fulfill the request.',imageURL
                print 'Error code: ', e.code

            except urllib2.URLError, e:
                time.sleep(20)
                print 'We failed to reach a server.',imageURL
                print 'Reason: ', e.reason

            except socket.timeout as e:
                print "-----socket timout:",imageURL
            except Exception,e:
                print u'保存图片错误',e








file = open(sys.argv[1])
line = file.readline()
listCsv = []
while line!='':
       line = line.strip('\n')
       line = line.replace('+'," ")
       listCsv.append(line)
       line = file.readline()

spider = Spider()
socket.setdefaulttimeout(spider.timeout)
for trial in listCsv:
    dir =trial + "/"
    print u"查找资源：",trial
    isExists=os.path.exists(dir)
    if isExists:
        print u"已存在，查找下一项："
        continue
    
    global empty
    global imageUrlList
    global imageDownloadCount
    global imageGetCount
    empty = False
    imageUrlList = Queue.Queue(0)
    imageDownloadCount=0
    imageGetCount=0
    spider.saveImagesInfo(trial,1,10)
    print u'差不到内容退回主菜单'
    
print u'退出程序'
