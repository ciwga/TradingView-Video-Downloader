#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from datetime import datetime
from tqdm import tqdm
import time
import requests
import json
import os
import argparse
import sys
import platform


class tradingview_video_dl():
    '''TradingView Video Downloader'''
    def __init__(self, username, url):
        self.username = username
        self.base_url = url
        self.counter = 0

        try:
            os.mkdir('_TradingView_Videos')
        except FileExistsError:
            pass
        os.chdir('_TradingView_Videos')

    def _userAgent(self):
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'

    def _http_header(self, *args):
        header = {
            "User-Agent": self._userAgent()
        }
        if args:
            for arg in args:
                header["Range"] = f"bytes={arg}-"
        return header

    def timestamp(self, date):
        date_format = '%a, %d %b %Y %H:%M:%S GMT'
        strp = datetime.strptime(date, date_format)
        return time.mktime(strp.timetuple())

    def fix_filename(self, document_name):
        document_name = document_name.replace('/', '\u2215')
        if platform.system() == 'Windows':
            document_name = document_name.replace('?', '\ufe16').replace(':', '\uff1a').replace('|', '\uff5c')
            document_name = document_name.replace('*', '\uff0a').replace('<', '\ufe64')
            document_name = document_name.replace('>', '\ufe65').replace('\\', '\ufe68').replace('\"', '\uff02')
        return document_name

    def downloader(self, total_size, document_name, initial_byte, tmp_name, container_video, file_date):
        with open(tmp_name, 'ab') as video_file:
            with tqdm(total=total_size,
                        desc=document_name,
                        initial=initial_byte,
                        unit='B',
                        colour='blue',
                        dynamic_ncols=True,
                        unit_scale=True,
                        unit_divisor=1024) as pbar:
                for chunk in container_video.iter_content(chunk_size=1024):
                    if chunk:
                        pbar.update(len(chunk))
                        video_file.write(chunk)
                        video_file.flush()
        os.rename(tmp_name, document_name+'.mp4')
        os.utime(document_name+'.mp4', (file_date, file_date))

    def _video_data(self, container_url):
        soup3 = BeautifulSoup(container_url.content, 'html.parser')
        document_name = soup3.find('h1', attrs={'class': 'tv-chart-view__title-name js-chart-view__name'}).text
        document_name = self.fix_filename(document_name)
        if os.path.exists(document_name+'.mp4'):
            print(f'[{document_name}] already downloaded...')
        else:
            tmp_name = document_name + '.incomplete'
            initial_byte = int(os.path.exists(tmp_name) and
                                os.path.getsize(tmp_name))
            try:
                video_url = soup3.find('video', attrs={'class': 'tv-chart-view__video js-video-content'}).get('src')
                container_video = requests.get(video_url, headers=self._http_header(initial_byte), stream=True)
                total_size = int(container_video.headers['content-length'])
                file_date = self.timestamp(container_video.headers['Last-Modified'])
                self.downloader(total_size, document_name, initial_byte, tmp_name, container_video, file_date)
            except AttributeError:
                print('Video Not Found!')
                sys.exit()

    def _page_numbers(self):
        page = requests.get(self.base_url, headers=self._http_header())
        if page.status_code == 200 and 'tv-empty-card__text' not in page.text:
            soup1 = BeautifulSoup(page.content, 'html.parser')
            data_page = [int(z.get('data-page'))
                        for z in soup1.find_all('a', attrs={'class': 'tv-feed-pagination__page tv-feed-pagination__page--narrow js-page-reference'})]      
            if data_page:
                pass
            else:
                data_page = [0, 1]
        else:
            print("Hashtag not found!")
            sys.exit()

        return max(data_page)

    def multiple_video(self):
        for number in range(1, self._page_numbers()+1):
            hashtag_page = requests.get(self.base_url+'page-'+str(number), headers=self._http_header())
            soup2 = BeautifulSoup(hashtag_page.content, 'html.parser')
            dataset = [card.get('data-card') for card in\
                       soup2.find_all('div', attrs={'class': 'tv-feed__item tv-feed-layout__card-item'})]
            for data in dataset:
                data_dict = json.loads(data)
                if data_dict['author']['username'] == self.username:
                    while (self.counter < 1):
                        if self.counter == 0:
                            try:
                                os.mkdir(self.username)
                            except FileExistsError:
                                pass
                            os.chdir(self.username)
                            self.counter = 1
                    container_url = requests.get(data_dict['data']['published_url'], headers=self._http_header())
                    self._video_data(container_url)
    
    def a_video(self):
        container_url = requests.get(self.base_url, headers=self._http_header())
        try:
            os.mkdir(self.username)
        except FileExistsError:
            pass
        os.chdir(self.username)
        self._video_data(container_url)

def tradingview_video_dl_cli():
    parser = argparse.ArgumentParser(description='Tradingview Video Downloader for an username from hashtag')
    parser.add_argument('-u', dest='username', type=str, required=True, help='Enter an username which has videos you want to download')
    parser.add_argument('-a', dest='url', type=str, required=True, help='# (e.g: https://tradingview.com/ideas/{hashtag}/ or\
                                                                         a video link: https://tr.tradingview.com/chart/BTCUSD/DB89e7hu/)')
    args = parser.parse_args()
    run = tradingview_video_dl(args.username, args.url)
    if 'chart' in args.url:
        run.a_video()
    else:
        run.multiple_video()


# url = "https://tr.tradingview.com/ideas/teknikanalizegitimi/"
# url = "https://tr.tradingview.com/chart/BTCUSD/DB89e7hu/"
# run = tradingview_video_dl('MegalodonTrading', url)
# if __name__ == '__main__':
#     if 'chart' in url:
#         run.a_video()
#     else:
#         run.multiple_video()

if __name__ == '__main__':
    tradingview_video_dl_cli()
