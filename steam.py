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

curCount = 0

def steam_spider() -> list:
    # global lastGameCount
    # lastGameCount = int(df['Link'][0].split(": ")[1])

    all_url = []
    #找到这次游戏总数
    url1 = "https://store.steampowered.com/search/results/?query&start=0&count=50&dynamic_data=&sort_by=_ASC&ignore_preferences=1&os=win&snr=1_7_7_comingsoon_7&filter=comingsoon&infinite=1"
    try:
        response1 = requests.get(url1, headers = header).text
    except:
        print('服务器无响应1')
        try:
            response1 = requests.get(url1, headers = header).text
        except:
            print('服务器无响应2')
            try:
               response1 = requests.get(url1, headers = header).text
            except:
                print('服务器无响应3')
                try:
                    response1 = requests.get(url1, headers = header).text
                except:
                    print('服务器无响应4')
                

    data = json.loads(response1)
    global curNum
    curNum = data["total_count"]

    # #找到所有的url
    # global dif
    # dif = curNum - lastGameCount
    # if(dif%50 == 0):
    #     times = int(dif / 50)
    # else:
    #     times = int(dif / 50) + 1

    # for i in range(0, times):
    #     newUrl = "https://store.steampowered.com/search/results/?query&start=" + str(50 * i) +  "&count=50&dynamic_data=&sort_by=_ASC&ignore_preferences=1&os=win&snr=1_7_7_comingsoon_7&filter=comingsoon&infinite=1"
    #     tempResponse = requests.get(newUrl, headers = header).text
    #     tempData = json.loads(tempResponse)
    #     idAndName = re.findall("https://store.steampowered.com/app/(\d*?)/(.*?)/", tempData["results_html"])
    #     for temp in idAndName:
    #         all_url.append(temp)
    

    # #返回所有url+名字
    # return all_url

    if(curNum%50 == 0):
        times = int(curNum / 50)
    else:
        times = int(curNum / 50) + 1

    for i in range(0, times):
        newUrl = "https://store.steampowered.com/search/results/?query&start=" + str(50 * i) +  "&count=50&dynamic_data=&sort_by=_ASC&ignore_preferences=1&os=win&snr=1_7_7_comingsoon_7&filter=comingsoon&infinite=1"
        tempResponse = requests.get(newUrl, headers = header).text
        tempData = json.loads(tempResponse)
        idAndName = re.findall("https://store.steampowered.com/app/(\d*?)/(.*?)/", tempData["results_html"])
        for temp in idAndName:
            all_url.append(temp)
    
    #print("all_url length: " + str(len(all_url)) + "curNum: " + str(curNum))
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
        return ""
    k = str(a.string).replace('	', '').replace('\n', '').replace('\r', '')
    return k

def developer(soup):   #开发商
    a = soup.find(id="developers_list")
    if a == NULL:
        return ""
    k = str(a.a.string)
    return k

def publisher(soup):   #发行商
    str = ""
    k = soup.find_all(name ="div", attrs={"class":"subtitle column"})
    if k == NULL:
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
        tag = "failed"
        des = "failed"
        dev = "failed"
        pub = "failed"
        print("can't finish")
    return tag,des,dev,pub

if __name__ == "__main__":
    
    #“全部游戏”数据
    gc = pygsheets.authorize(service_file = file_path)
    my_sh = gc.open('Steam每日新收录游戏数据')
    #已有数据
    wks = my_sh[1]
    prev_all_game_data = wks.get_as_df()
    col_link = prev_all_game_data["Link"].tolist()



    # if curNum != lastGameCount:
    #     firstLinkList = []
    #     firstNameList = []
    #     temp = 0
    #     for i in mylist:
    #         if temp < dif:
    #             firstLinkList.append("https://store.steampowered.com/app/" + i[0])
    #             firstNameList.append(i[1])
    #             temp += 1
    #         else:
    #             break

    #现在数据库里的所有游戏数据
    mylist = steam_spider()

    firstLinkList = []
    firstNameList = []

    for i in mylist:
        firstLinkList.append("https://store.steampowered.com/app/" + i[0])
        firstNameList.append(i[1])

    #更新全部游戏数据的table
    gamedata = list(zip(firstNameList, firstLinkList))
    dupdate_all_game_data = pd.DataFrame(gamedata, columns =['Name', 'Link'])
    wk_all_games = my_sh[1]
    wk_all_games.set_dataframe(dupdate_all_game_data,(1, 1))

    #找出和“全部游戏”数据中不同的，即为新内容
    newLink = []
    newName = []

    for i in range(0, len(firstLinkList)):
        if(firstLinkList[i] not in col_link):
            newLink.append(firstLinkList[i])
            newName.append(firstNameList[i])

    #更新“每日新增”界面
    nameList = []
    linkList = []
    tagList = []
    desList = []
    devList = []
    pubList = []

    #存入运行日期
    nameList.append(str(datetime.date.today()))
    linkList.append("")
    tagList.append("")
    desList.append("")
    devList.append("")
    pubList.append("")

    for i in range(0, len(newLink)):
        name = newName[i]
        temp_url = newLink[i]
        try:
            r = requests.get(temp_url, headers=header)
        except:
            print("服务器无响应1")
            try:
                r = requests.get(temp_url, headers=header)
            except:
                print("服务器无响应2")
                try:
                    r = requests.get(temp_url, headers=header)
                except:
                    print("服务器无响应3")

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

    #把两个dataFrame合并在一起
    wk_daily_update_data = my_sh[0]
    data_df = wk_daily_update_data.get_as_df().drop_duplicates(keep=False)
    new_data = pd.concat([df2, data_df])
    wk_daily_update_data.set_dataframe(new_data,(1, 1)) 



