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
USE_PROXY      = False
DOWNLOAD_DELAY = 0.5
BASE_URL  = 'http://platesmania.com'
PRIME_URL = 'http://platesmania.com/avto?&lang=en'
HEADER    = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
             'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
             'Accept-Encoding': 'none',
             'Accept-Language': 'en-US,en;q=0.8',
             'Connection': 'keep-alive'}



"""==============================================="""
#For a given url, request a response
def get_response(url):
    response = requests.get(url, headers=HEADER, timeout=20)
    response.raise_for_status()
    return response


#For a given url, request a response and parse to html via BeautifulSoup
def get_response_and_soup(url):
    response = get_response(url)
    if response is not None:
        return bs4.BeautifulSoup(response.text, 'html.parser')
    else:
        return None




"""=================================================="""
html = get_response_and_soup(PRIME_URL)

#All available car types
options = html.select('a[class="tooltips"]')
options = [x for x in options if 'catalog' in str(x)]
options = {x.text:{'url':BASE_URL+'/'+x.attrs['href'], 'n_images':int(x.attrs['data-original-title'].split(' ')[0])} for x in options}

suboptions = {}

for key,content in tqdm(options.items(), position=0):
    try:
        html = get_response_and_soup(content['url'])

        subclasses = html.select('div[class="headline"]')
        subclasses = [[y for y in x.select('a') if 'catalog' in str(y)][0] for x in subclasses]
        subclasses = {x.text:BASE_URL+''+x.attrs['href'] for x in subclasses}

        for subkey, subcontent in tqdm(subclasses.items(), position=1):
            try:
                html   = get_response_and_soup(subcontent)
                n_imgs = int(html.select('a[class="pull-right"]')[0].text.split(' ')[0].replace('.',''))
                suboptions[key+' '+subkey] = n_imgs
            except:
                pass
    except:
        pass
    time.sleep(0.3*(1+random.random()))

import pickle as pkl
pkl.dump({'finegrained':suboptions, 'models':options},open(os.getcwd()+'/freq.pkl','wb'))

# import os
# res = pkl.load(open(os.getcwd()+'/freq.pkl','rb'))
res = suboptions

import matplotlib.pyplot as plt
x,y = [],[]
for key,val in res['finegrained'].items():
    x.append(key)
    y.append(val)

import numpy as np
np.sum(y)
plt.style.use('ggplot')
expstr = 'Max #Images: {0}, {1:2.1f}% above 100 images in subclasses'.format(np.sum(y), np.sum(np.array(y)>100)/len(y)*100)
f,ax = plt.subplots(1,2)
ax[0].plot(y)
ax[0].set_xlabel('Numeric Car Class')
ax[0].set_ylabel('#Images/Class')
for xx in np.argsort(y)[-20:]:
    ax[0].text(xx,y[xx],x[xx])
ax[1].semilogy(sorted(y, key=lambda x: -x))
ax[1].set_xlabel('Sorted Numeric Car Class')
ax[1].set_ylabel('Log #Images/Class')
f.suptitle(expstr, fontsize=15)
f.set_size_inches(25,18)
plt.savefig('occurences.svg')
plt.show()
