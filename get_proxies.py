###LIBRARIES
import urllib, bs4, requests, pymongo, time, numpy as np
from tqdm import tqdm
import pandas as pd
import itertools as it, os
import time, random
from tqdm import tqdm
from joblib import Parallel, delayed
import argparse



""" ======================================== """
parser = argparse.ArgumentParser()
parser.add_argument('--proxyserver', default='hidemyna', type=str, help='server to extract proxies from.')
parser.add_argument('--n_fastest',   default=150, type=int, help='Only use <n_fastest> proxies.')
opt = parser.parse_in()



""" ======================================== """
if opt.proxyserver=='freeproxylist':
    url = "https://free-proxy-list.net/" # the source
    try:
        print('Looking for available proxies... ',end='')
        time.sleep(1)
        req = urllib.request.Request(url,headers=HEADER)
        open_url = urllib.request.urlopen(req)
        data = open_url.read()

        soup = bs4.BeautifulSoup(data,'html.parser')
        proxy_data = soup.find_all('tr')

        Pr_list, Countries = [],[]
        for i in proxy_data[1:-1]:
            if 'class="hm"' in str(i):
                Pr = "{0}:{1}".format(bs4.BeautifulSoup(str(list(i)[0]),'html.parser').text,bs4.BeautifulSoup(str(list(i)[1]),'html.parser').text)
                Countries.append(list(i)[3].text)
                Pr_list.append(Pr)
        #Pr_list = [x for x in Pr_list if not np.sum([y.isalpha() for y in x]) and x!=':']
        Pr_list   = Pr_list[:-1]
        Countries = Countries[:-1]

        ### SAVE EXTRACTED PROXIES FOR LATER USE
        random.shuffle(Pr_list)
        np.save('proxies.npy',Pr_list)

        print('Found', len(Pr_list), 'proxies.')


    except error:
        raise Exception('\nError when extracting proxies from {}: {}.'.format(url, error))
    random.shuffle(Pr_list)
    return Pr_list
else:
    url = "https://hidemyna.me/en/proxy-list/"
    try:
        print('Looking for available proxies... ',end='')
        time.sleep(1)

        from selenium import webdriver

        """
        This website uses cloudflare for bot protection. To counter this, we call the url in a controlled chrome instance
        via the selenium package. To do so:

        Download/extract chromedriver from http://chromedriver.storage.googleapis.com/index.html?path=2.24/ and place it in this folder (os.getcwd()).
        """
        #NOTE: This will open a Google Chrome instance, in which the url will be loaded to!
        driver = webdriver.Chrome(os.getcwd()+'/chromedriver')
        driver.get(url)
        #WAIT FOR CLOUDFLARE TO FINISH CHECKING AND GIVING ACCESS
        time.sleep(10)

        ### EXTRACT PAGINATION LINKS
        table = driver.find_element_by_xpath('//*[@id="content-section"]/section[1]/div/div[4]')
        table_html = table.get_attribute('innerHTML')
        table_html = bs4.BeautifulSoup(table_html)
        k = [x.find('a').attrs['href'] for x in table_html.find_all('li') if 'class' not in str(x) and 'span' not in str(x)]
        low = int(k[0].split('tart=')[-1].split('#')[0])
        up  = int(k[-1].split('tart=')[-1].split('#')[0])
        table_links = [url+'?start={}#list'.format(x) for x in [0]+list(range(low,up,low))+[up]]

        ### START SCRAPING PROXY ADDRESSES
        n_pages_to_scrap = len(table_links) #Number of table pages to work through. To ensure recency of the proxies, take e.g. the first 40 pages, i.e. n_pages_to_scrap = 40
        Pr_list = []

        for table_link in tqdm(table_links[:n_pages_to_scrap]):
            driver.get(table_link)
            table = driver.find_element_by_xpath('//*[@id="content-section"]/section[1]/div/table')
            table_html = table.get_attribute('innerHTML')
            table_html = bs4.BeautifulSoup(table_html)
            trs = table_html.find('tbody').find_all('tr')
            for tr in trs:
                tm = tr.find_all('td')
                Pr_list.append((tm[0].text,tm[1].text,int(tm[3].text.split(' ')[0]),tm[2].text))

        driver.close()


        ### SORT BY SPEED AND TAKE <n_proxies_2_take> fastest proxies.
        Pr_list = sorted(Pr_list, key=lambda x: x[2])
        Pr_list = ['{}:{}'.format(x[0],x[1]) for x in Pr_list]
        n_proxies_2_take = opt.n_fastest
        print('Found', len(Pr_list), 'proxies. Taking {} fastest.'.format(n_proxies_2_take))
        Pr_list = Pr_list[:n_proxies_2_take]

        ### SAVE EXTRACTED PROXIES FOR LATER USE
        random.shuffle(Pr_list)
        np.save('proxies.npy',Pr_list)

    except error:
        raise Exception('\nError when extracting proxies from {}: {}.'.format(url, error))
