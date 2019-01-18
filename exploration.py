###LIBRARIES
import urllib, bs4, requests, pymongo, time, numpy as np
from tqdm import tqdm
import pandas as pd
import itertools as it, os
import time, random
from io import BytesIO
from PIL import Image



"""=========================================="""
### Scrapper Variables
DOWNLOAD_DELAY = 0.5
BASE_URL  = 'http://platesmania.com'
PRIME_URL = 'http://platesmania.com/avto?&lang=en'
HEADER    = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
             'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
             'Accept-Encoding': 'none',
             'Accept-Language': 'en-US,en;q=0.8',
             'Connection': 'keep-alive'}


#First Website Access
response = requests.get(PRIME_URL, timeout=10)
html     = bs4.BeautifulSoup(response.text, 'html.parser')

#All available car types
options = html.select('a[class="tooltips"]')
options = [x for x in options if 'catalog' in str(x)]
options = {x.text:BASE_URL+'/'+x.attrs['href'] for x in options}

#Get all model links for a specfic car subclass
response = requests.get(options['Aston Martin'], timeout=10)
html     = bs4.BeautifulSoup(response.text, 'html.parser')

subclasses = html.select('div[class="headline"]')
subclasses = [[y for y in x.select('a') if 'catalog' in str(y)][0] for x in subclasses]
subclasses = {x.text:BASE_URL+''+x.attrs['href'] for x in subclasses}

#Extract Info for one specific car subclass
response = requests.get(subclasses['Virage'], timeout=10)
html     = bs4.BeautifulSoup(response.text, 'html.parser')
all_imgs = html.select('a[class="pull-right"]')[0].attrs['href']

#In List of available car models within a subclass, get all possible car image lists
response = requests.get(BASE_URL+all_imgs, timeout=10)
html     = bs4.BeautifulSoup(response.text, 'html.parser')

n_car_pages = np.clip(np.ceil(int(html.select('h1[class="pull-left"]')[0].text.split(' ')[-1])/10),None,99).astype(int)
# n_car_pages  = len(html.select('ul[class="pagination"]')[0].select('a'))-2
car_settings = [x.split('=')[-1] for x in all_imgs.split('markaavto')[-1].split('&')]
avail_image_pages_4_subclass = [BASE_URL+'/gallery.php?&markaavto={}&model={}&start={}'.format(car_settings[0], car_settings[1], car_page_num) for car_page_num in range(n_car_pages)]

#In multi-image page, get all available links to single image pages
first_page = avail_image_pages_4_subclass[0]
response = requests.get(first_page, timeout=10)
first_page
html     = bs4.BeautifulSoup(response.text, 'html.parser')

single_image_page_urls = [BASE_URL+x for x in list(set([x.attrs['href'] for x in html.select('div[class="container content"]')[0].select('a') if 'img alt' in str(x)]))]
single_image_page_url  = single_image_page_urls[0]

#In single image page, get link to high-res-img-page
response = requests.get(single_image_page_url, timeout=10)
html     = bs4.BeautifulSoup(response.text, 'html.parser')

main_content = html.select('div[class="container content"]')[0]

high_res_img_page_url  = BASE_URL+[x for x in main_content.select('a') if "img-responsive" in str(x)][0].attrs['href']

platenum       = html.select('h1[class="pull-left"]')[0].text.replace('\t','').replace('\n','')
plate_pic_url  = html.select('img[class="img-responsive center-block margin-bottom-20"]')[0].attrs['src']
plate_info     = html.select('img[class="img-responsive center-block margin-bottom-20"]')[0].attrs['alt']
likes          = html.select('a[data-toggle="modal"]')[0].text.split(' ')[-1]
origin_info    = [x for x in html.select('h3[class="panel-title"]') if 'a href' in str(x)][0].text


#Get final downloadable link
response = requests.get(high_res_img_page_url, timeout=10)
html     = bs4.BeautifulSoup(response.text, 'html.parser')
img_href = [x for x in html.select('img') if 'img-responsive' in str(x)][0].attrs['src']

#Download Image
request          = urllib.request.Request(img_href,None,HEADER)
response         = urllib.request.urlopen(request)
downloaded_image = response.read()
downloaded_image = Image.open(BytesIO(downloaded_image))
