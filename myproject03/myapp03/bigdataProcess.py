from bs4 import BeautifulSoup
import requests
import re
from matplotlib import font_manager, rc

from myProject03.settings import STATIC_DIR, TEMPLATE_DIR
from wordcloud import WordCloud

import os
from pandas import DataFrame
import folium
from konlpy.tag import Okt
from collections import Counter
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns


# 야구관객수
def attendance(soup):

    tdata = soup.find('table', {'class': 'tData'})
    series = tdata.find('tbody')
    kbdata_spec = series.text
    print(kbdata_spec)
    table_rows = tdata.find_all('tr')

    res = []
    for tr in table_rows:
        td = tr.find_all('td')
        row = [tr.text.strip() for tr in td if tr.text.strip()]
        if row:
            res.append(row)

    df = pd.DataFrame(
        res, columns=["date", "day", "team_1", "team_2", 'place', 'number'])
    df = df.drop(0)

    # 콤마 제거
    df['number'] = df['number'].str.replace(',', '')

    # datetime type으로 변환
    df['date'] = pd.to_datetime(df['date'])

    # 날짜 column을 분리
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['dayofweek'] = df['date'].dt.dayofweek
    df['number'] = df['number'].astype(int)
    df.sort_values('number', ascending=False)
    # print(df)

    font_path = "c:/Windows/fonts/malgun.ttf"
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    matplotlib.rc('font', family=font_name)
    xlabel = ['월', '화', '수', '목', '금', '토', '일']
    plt.figure(figsize=(12, 9))
    x = df.groupby('dayofweek')['number'].sum().keys()
    y = df.groupby('dayofweek')['number'].sum()
    ax = sns.barplot(x, y)
    ax.set(xticklabels=xlabel)
    plt.xlabel('요일')
    plt.ylabel('관객수')
    plt.savefig('./static/images/KBO_attendance.png')


# 워드클라우드
def make_wordCloud(data):

    message = ''

    for item in data:
        if 'message' in item.keys():
            message = message + re.sub(r'[^\w]', ' ', item['message']) + ''

    nlp = Okt()
    message_N = nlp.nouns(message)

    count = Counter(message_N)

    word_count = {}

    for tag, counts in count.most_common(80):
        if(len(str(tag)) > 1):
            word_count[tag] = counts
            print("%s : %d" % (tag, counts))

    font_path = "c:/Windows/fonts/malgun.ttf"
    wc = WordCloud(font_path, background_color='ivory', width=800, height=600)
    cloud = wc.generate_from_frequencies(word_count)

    # cloud
    plt.figure(figsize=(8, 8))
    plt.imshow(cloud)
    plt.axis('off')
    cloud.to_file('./static/images/k_wordCloud.png')


# 지도
def map():
    ex = {'경도': [127.061026, 127.047883, 127.899220, 128.980455, 127.104071, 127.102490, 127.088387, 126.809957, 127.010861, 126.836078, 127.014217, 126.886859, 127.031702, 126.880898, 127.028726, 126.897710, 126.910288, 127.043189, 127.071184, 127.076812, 127.045022, 126.982419, 126.840285, 127.115873, 126.885320, 127.078464, 127.057100, 127.020945, 129.068324, 129.059574, 126.927655, 127.034302, 129.106330, 126.980242, 126.945099, 129.034599, 127.054649, 127.019556, 127.053198, 127.031005, 127.058560, 127.078519, 127.056141, 129.034605, 126.888485, 129.070117, 127.057746, 126.929288, 127.054163, 129.060972],
          '위도': [37.493922, 37.505675, 37.471711, 35.159774, 37.500249, 37.515149, 37.549245, 37.562013, 37.552153, 37.538927, 37.492388, 37.480390, 37.588485, 37.504067, 37.608392, 37.503693, 37.579029, 37.580073, 37.552103, 37.545461, 37.580196, 37.562274, 37.535419, 37.527477, 37.526139, 37.648247, 37.512939, 37.517574, 35.202902, 35.144776, 37.499229, 35.150069, 35.141176, 37.479403, 37.512569, 35.123196, 37.546718, 37.553668, 37.488742, 37.493653, 37.498462, 37.556602, 37.544180, 35.111532, 37.508058, 35.085777, 37.546103, 37.483899, 37.489299, 35.143421],
          '구분': ['음식', '음식', '음식', '음식', '생활서비스', '음식', '음식', '음식', '음식', '음식', '음식', '음식', '음식', '음식', '음식', '음식', '음식', '소매', '음식', '음식', '음식', '음식', '소매', '음식', '소매', '음식', '음식', '음식', '음식', '음식', '음식', '음식', '음식', '음식', '음식', '소매', '음식', '음식', '의료', '음식', '음식', '음식', '소매', '음식', '음식', '음식', '음식', '음식', '음식', '음식']}
    ex = DataFrame(ex)
    lat = ex['위도'].mean()

    long = ex['경도'].mean()
    m = folium.Map([lat, long], zoom_start=10)

    for i in ex.index:
        sub_lat = ex.loc[i, '위도']
        sub_long = ex.loc[i, '경도']

        title = ex.loc[i, '구분']

        folium.Marker([sub_lat, sub_long], tooltip=title).add_to(m)
        m.save(os.path.join(TEMPLATE_DIR, 'bigdata/maptest.html'))


def weather_crawing(last_date, weather):

    data = requests.get(
        'https://www.weather.go.kr/weather/forecast/mid-term-rss3.jsp?stnld=108')

    html = data.text
    print(html)
    soup = BeautifulSoup(html, 'lxml')

    # 딕을 하나 만들고
    for i in soup.find_all('location'):
        # 키값하나에 벨류가 13개 들어감
        weather[i.find('city').text] = []
        for j in i.find_all('data'):
            temp = []
            if (len(last_date) == 0) or (j.find('tmef').text > last_date[0]['tmef']):
                temp.append(j.find('tmef').text)
                temp.append(j.find('wf').text)
                temp.append(j.find('tmn').text)
                temp.append(j.find('tmx').text)
                weather[i.find('city').string].append(temp)
    weather[i.find('city').string].append(temp)
    # print(temp)


def weather_make_chart(result, wfs, dcounts):
    font_location = "c:/Windows/fonts/malgun.ttf"
    font_name = font_manager.FontProperties(fname=font_location).get_name()
    rc('font', family=font_name)

    high = []
    low = []
    xdata = []

    for row in result.values_list():
        high.append(row[5])
        low.append(row[4])
        xdata.append(row[2].split('-')[2])

    plt.cla()
    plt.figure(figsize=(10, 6))
    plt.plot(xdata, low, label='최저기온')
    plt.plot(xdata, high, label='최고기온')
    plt.legend()
    plt.savefig(os.path.join(
        STATIC_DIR, 'images\\weather_busan.png'), dpi=300)

    plt.cla()
    plt.bar(wfs, dcounts)
    plt.savefig(os.path.join(
        STATIC_DIR, 'images\\weather_bar.png'), dpi=300)

    plt.cla()
    plt.pie(dcounts, labels=wfs, autopct='%.1f%%')
    plt.savefig(os.path.join(
        STATIC_DIR, 'images\\weather_pie.png'), dpi=300)


# 여러개의 이미지를 넣을려고 딕 만듦
    image_dic = {
        'plot':  'weather_busan.png',
        'bar':  'weather_bar.png',
        'pie':  'weather_pie.png'
    }
    return image_dic


def melon_crawing(datas):
    header = {'User-Agent': 'Mozilla/5.0'}
    req = requests.get(
        'https://www.melon.com/chart/week/index.htm', headers=header)
    soup = BeautifulSoup(req.text, 'html.parser')

    melon = soup.select_one('div > table > tbody')

    for chart in melon.select('tr'):
        rank = chart.select_one('span.rank').get_text().strip()
        Music = re.sub('\n', '', chart.select_one(
            'div.ellipsis.rank01 > span > a').get_text().strip())
        singer = re.sub('\n', '', chart.select_one(
            'div.ellipsis.rank02 > span > a').get_text().strip())
        album = chart.select_one(
            'td:nth-child(7) > div > div > div > a').get_text()

        tmp = {'rank': rank,
               'Music': Music,
               'singer': singer,
               'album': album}
        datas.append(tmp)
