from asyncio.windows_events import NULL
import requests
from bs4 import BeautifulSoup
import json
import re
import pandas as pd
import pygsheets
import datetime
import os.path


header = {
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/85.0.4183.102 Safari/537.36', 
        'Accept-Language': 'zh-CN '
    }

base_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(base_path, 'credentials.json')
num_path = os.path.join(base_path, 'lastCount.txt')

curCount = 0

def steam_spider(lastNum) -> list:
    #找到这次游戏总数
    url1 = "https://store.steampowered.com/search/results/?query&start=0&count=50&dynamic_data=&sort_by=_ASC&ignore_preferences=1&os=win&snr=1_7_7_comingsoon_7&filter=comingsoon&infinite=1"
    try:
        response1 = requests.get(url1, headers = header).text
    except:
        print("当前主页面爬取失败")
        return
    data = json.loads(response1)
    global curNum
    curNum = data["total_count"]

    #找到所有的url
    global dif
    dif = curNum - lastNum
    if(dif%50 == 0):
        times = int(dif / 50)
    else:
        times = int(dif / 50) + 1

    all_url = []
    for i in range(0, times):
        newUrl = "https://store.steampowered.com/search/results/?query&start=" + str(50 * i) +  "&count=50&dynamic_data=&sort_by=_ASC&ignore_preferences=1&os=win&snr=1_7_7_comingsoon_7&filter=comingsoon&infinite=1"
        print(newUrl)
        tempResponse = requests.get(newUrl, headers = header).text
        tempData = json.loads(tempResponse)
        idAndName = re.findall("https://store.steampowered.com/app/(\d*?)/(.*?)/", tempData["results_html"])
        for temp in idAndName:
            all_url.append(temp)
            print(temp)
    

    #返回所有url+名字
    return all_url

def taglist(soup):#标签列表
    list1=[]
    a = soup.find_all(class_="app_tag")
    for i in a:
        k = str(i.string).replace('	', '').replace('\n', '').replace('\r', '')
        if k == '+':
            pass
        else:
            list1.append(k)
    list1 = str(' '.join(list1))
    return list1

def description(soup):  #游戏描述
    a = soup.find(class_="game_description_snippet")
    if a == NULL:
        print("null")
        return ""
    k = str(a.string).replace('	', '').replace('\n', '').replace('\r', '')
    return k

def developer(soup):   #开发商
    a = soup.find(id="developers_list")
    if a == NULL:
        print("null")
        return ""
    k = str(a.a.string)
    return k

def publisher(soup):   #发行商
    str = ""
    k = soup.find_all(name ="div", attrs={"class":"subtitle column"})
    if k == NULL:
        print("null")
        return ""
    for i in k:
        if(i.string == "发行商:"):
            for name in i.parent.find_all(name = "a"):
                str += name.string + ", "
    
    return str


def getdetail(soup):
    tag, des, dev, pub = ' ', ' ', ' ', ' '
    try:
        tag = taglist(soup)
        des = description(soup)
        dev = developer(soup)
        pub = publisher(soup)
    except:
        print("can't finish")
    return tag,des,dev, pub

if __name__ == "__main__":

    #找到上一次的游戏总数
    file = open(num_path, "r")
    lastGameCount = int(file.readline())
    file.close()

    print("lastGameCount: " + str(lastGameCount))

    mylist = steam_spider(lastGameCount)
    firstLinkList = []
    firstNameList = []
    temp = 0
    for i in mylist:
        if temp < dif:
            firstLinkList.append("https://store.steampowered.com/app/" + i[0])
            firstNameList.append(i[1])
            temp += 1
        else:
            break

    print("currentGameCount: " + str(curNum))

    if curNum != lastGameCount:

        nameList = []
        linkList = []
        tagList = []
        desList = []
        devList = []
        pubList = []

        #存入运行日期
        nameList.append("收入日期：" + str(datetime.date.today()))
        linkList.append("")
        tagList.append("")
        desList.append("")
        devList.append("")
        pubList.append("")

        for i in range(0, len(firstLinkList)):
            name = firstNameList[i]
            temp_url = firstLinkList[i]
            try:
                r = requests.get(temp_url, headers=header)
            except:
                print("服务器无响应")

            soup = BeautifulSoup(r.text, 'lxml')
            temp_tuple = getdetail(soup)

            nameList.append(name)
            linkList.append(temp_url)
            tagList.append(temp_tuple[0])
            desList.append(temp_tuple[1])
            devList.append(temp_tuple[2])
            pubList.append(temp_tuple[3])

        #加一个空行
        nameList.append("   ")
        linkList.append("   ")
        tagList.append("   ")
        desList.append("   ")
        devList.append("   ")
        pubList.append("   ")
        
        allList = list(zip(nameList, linkList, tagList, desList, devList, pubList))
        df2 = pd.DataFrame(allList, columns =['Name', 'Link', 'Tag', 'Description', "Developer", "Publisher"])

        #写到Google sheet里
        #authorization
        gc = pygsheets.authorize(service_file = file_path)
        #open the google spreadsheet ('pysheeetsTest' exists)
        my_sh = gc.open('Steam每日新收录游戏数据')
        #select the first sheet
        wks = my_sh[0]
        #update the first sheet with df, starting at cell B2

        #wks.set_dataframe(df2,(1, 1))

        prev_data = wks.get_as_df()
        new_data = pd.concat([df2, prev_data])
        wks.set_dataframe(new_data,(1, 1))

        #把新数据写进文件里
        file = open(num_path, "w")
        file.write(str(curNum))
        file.close()
