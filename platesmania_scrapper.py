###LIBRARIES
import urllib, bs4, requests, pymongo, time, numpy as np
import http.client as httplib
from tqdm import tqdm
import pandas as pd, multiprocessing as mp
import itertools as it, os
import time, random
from io import BytesIO
from PIL import Image
import pickle as pkl
from tqdm import tqdm
from joblib import Parallel, delayed

import proxy_utilities as pu
import database_utilities as du

import argparse




"""========================================="""
parser = argparse.ArgumentParser()
parser.add_argument('--max_images',  default=-1, type=int,  help='Maximum number of images to download')
parser.add_argument('--car_classes', nargs='+', default=[], help='Only parse specific car classes.')
parser.add_argument('--use_proxy',   action='store_true',   help='Use proxies. Requires a previous extraction of proxies to proxies.npy')
opt = parser.parse_args()
opt.max_images = np.inf if opt.max_images==-1 else opt.max_images
opt.counter    = 0



"""========================================="""
### SCRAPPER VARIABLES ###
DOWNLOAD_DELAY = 0.6 #Delay after every call to
SCRAP_DELAY    = 0.3
CHECK_INTERNET = True
TIME_FUNCTIONS = False
USE_PROXY = opt.use_proxy
BASE_URL  = 'http://platesmania.com'
PRIME_URL = 'http://platesmania.com/avto?&lang=en'
HEADER    = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
             'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
             'Accept-Encoding': 'none',
             'Accept-Language': 'en-US,en;q=0.8',
             'Connection': 'keep-alive'}






""" ====================================================== """
def main():
    """ ====================================================== """
    print('Starting scrapping from {}...\n'.format(PRIME_URL))

    ### Init proxy handler if required
    if USE_PROXY:
        proxyhandler = pu.ProxyHandler()
        proxyhandler.update_proxy()
        print('Started proxy service!\n')
    else:
        print('Not using proxy service!\n')

    ### Initialize Database
    database, retrieved_elements, not_yet_retrieved, not_retrievable = du.start_database()


    """ ====================================================== """
    #For a given url, request a response
    def get_response(url, retry_timeout=2, retry_counts=1, not_retrievable=not_retrievable):
        if USE_PROXY:
            try:
                response = requests.get(url, headers=HEADER, proxies=proxyhandler.proxy_dict,timeout=10)
                reponse.raise_for_status()
                return response
            except:
                if retry_counts > 0:
                    time.sleep(retry_timeout)
                    return get_response(url, retry_timeout=2*retry_timeout, retry_counts=retry_counts-1)
                elif retry_counts==0:
                    proxyhandler.update_proxy()
                    return get_response(url, retry_timeout=retry_timeout, retry_counts=-1)
                else:
                    not_retrievable.insert_one({'url':url})
                    return None
        else:
            try:
                response = requests.get(url, headers=HEADER, timeout=10)
                response.raise_for_status()
                return response
            except:
                if retry_counts > 0:
                    time.sleep(retry_timeout)
                    return get_response(url, retry_timeout=2*retry_timeout, retry_counts=retry_counts-1)
                not_retrievable.insert_one({'url':url})
                return None


    #For a given url, request a response and parse to html via BeautifulSoup
    def get_response_and_soup(url, **kwargs):
        response = get_response(url, **kwargs)
        if response is not None:
            return bs4.BeautifulSoup(response.text, 'html.parser')
        else:
            return None


    #Put a timer on a function to ensure that it does not run indefinitely.
    #If it finishes earlier, simply continue.
    def timer(f_hold, wait=15, *largs):
        def slave(f_hold, return_dict, *largs):
            return_dict['result'] = f_hold(*largs)

        manager     = mp.Manager()
        return_dict = manager.dict()

        inp = (f_hold,)+(return_dict,)+largs
        p   = mp.Process(target=slave, args=inp)
        p.start()
        p.join(wait)
        to_ret = return_dict.values()
        p.terminate()


        if len(to_ret):
            return tuple(to_ret) if len(to_ret)>1 else to_ret[0]


    # Check for consistent internet connection. If not available, hold until available again
    def check_internet():
        no_internet=True
        while no_internet:
            conn = httplib.HTTPConnection("www.google.com", timeout=1)
            try:
                conn.request("HEAD", "/")
                conn.close()
                no_internet = False
            except:
                conn.close()
                no_internet = True
                time.sleep(1)

    #Get all model links for a specfic car subclass
    def scrap_car_model_urls(database, retrieved_elements, not_yet_retrieved, not_retrievable, load=False, options=None):
        if load:
            if 'retrieved_elements' in database.list_collection_names():
                elem_to_retrieve = list(set([(tuple(x['name']),x['url']) for x in not_yet_retrieved.find({},{'_id':0})])-set([((x['model'],x['submodel']),x['url']) for x in retrieved_elements.find({},{'_id':0,'image':0})]))
                elem_to_retrieve = [{'name':x[0], 'url':x[1]} for x in elem_to_retrieve]
            else:
                elem_to_retrieve = not_yet_retrieved.find({},{'_id':0})
        else:
            print('Getting car class setup and pushing to database... ',end='')
            def get_subclasses(key, url):
                try:
                    response  = get_response(url)
                    html     = bs4.BeautifulSoup(response.text, 'html.parser')
                    subclasses = html.select('div[class="headline"]')
                    subclasses = [[y for y in x.select('a') if 'catalog' in str(y)][0] for x in subclasses]
                    subclasses = {(key,x.text):BASE_URL+''+x.attrs['href'] for x in subclasses}
                    time.sleep(DOWNLOAD_DELAY * (1+random.random()*0.2))
                    return subclasses
                except:
                    raise Exception('Encountered an error when getting car classes!')

            assert options is not None, 'Please input possible car class options!'
            # res = Parallel(n_jobs=2)(delayed(get_subclasses)(key, item['url']) for key,item in tqdm(options.items()))
            res = []
            for key,item in tqdm(options.items()):
                res.append(get_subclasses(key, item['url']))

            elem_to_retrieve = {}
            for sub_dict in res:
                elem_to_retrieve.update(sub_dict)

            pkl.dump(elem_to_retrieve, open(os.getcwd()+'/all_car_categories.pkl','wb'))
            elem_to_retrieve = [{'name':key, 'url':item} for key,item in elem_to_retrieve.items()]
            _  = not_yet_retrieved.insert_many(elem_to_retrieve)
            print('Done.')
        return elem_to_retrieve

    #Per Car subclass, recover all the relevant url information
    def extract_info_for_car_subclass(subclass_url):
        #Get all model links for a specfic car subclass

        #subclasses_url = res[47][('Aston Martin', 'Virage')]
        #Extract Info for one specific car subclass
        try:
            html     = get_response_and_soup(subclass_url)
            all_imgs = html.select('a[class="pull-right"]')[0].attrs['href']
            #In List of available car models within a subclass, get all possible car image lists
            html         = get_response_and_soup(BASE_URL+all_imgs)
            n_car_pages = np.clip(np.ceil(int(html.select('h1[class="pull-left"]')[0].text.split(' ')[-1])/10),None,99).astype(int)
            # n_car_pages  = len(html.select('ul[class="pagination"]')[0].select('a'))
            car_settings = [x.split('=')[-1] for x in all_imgs.split('markaavto')[-1].split('&')]
            if n_car_pages>1:
                avail_image_pages_4_subclass = [BASE_URL+'/gallery.php?&markaavto={}&model={}&start={}'.format(car_settings[0], car_settings[1], car_page_num) for car_page_num in range(n_car_pages)]
            else:
                avail_image_pages_4_subclass = [BASE_URL+'/gallery.php?&markaavto={}&model={}&start={}'.format(car_settings[0], car_settings[1], 0)]

            single_image_page_urls = []
            for page in avail_image_pages_4_subclass:
                html  = get_response_and_soup(page)
                single_image_page_urls.extend([BASE_URL+x for x in list(set([x.attrs['href'] for x in html.select('div[class="container content"]')[0].select('a') if 'img alt' in str(x)]))])
                time.sleep(DOWNLOAD_DELAY*(1+random.random()*0.2))

            return single_image_page_urls
        except:
            return None

    #Get url to high resolution image version from single-car page
    def get_image_url(single_page_url):
        try:
            html         = get_response_and_soup(single_page_url)
            main_content = html.select('div[class="container content"]')[0]
            high_res_img_page_url  = BASE_URL+[x for x in main_content.select('a') if "img-responsive" in str(x)][0].attrs['href']

            try:
                platenum       = html.select('h1[class="pull-left"]')[0].text.replace('\t','').replace('\n','')
            except:
                platenum       = None
            try:
                plate_pic      = download(html.select('img[class="img-responsive center-block margin-bottom-20"]')[0].attrs['src'])
            except:
                plate_pic      = None
            try:
                plate_info     = html.select('img[class="img-responsive center-block margin-bottom-20"]')[0].attrs['alt']
            except:
                plate_info     = None
            try:
                likes          = html.select('a[data-toggle="modal"]')[0].text.split(' ')[-1]
            except:
                likes          = None
            try:
                origin_info    = [x for x in html.select('h3[class="panel-title"]') if 'a href' in str(x)][0].text
            except:
                origin_info    = None

            infos = {'plate_number':platenum, 'plate_pic': plate_pic, 'plate_info':plate_info, 'likes':likes, 'origin_info':origin_info}


            #Get final downloadable link
            html     = get_response_and_soup(high_res_img_page_url)
            img_href = [x for x in html.select('img') if 'img-responsive' in str(x)][0].attrs['src']

            return img_href, infos
        except:
            return None


    ### Function to download image from main-image page
    def download(image_url, return_bytes=True):
        try:
            request          = urllib.request.Request(image_url,None,HEADER)
            response         = urllib.request.urlopen(request)
            downloaded_image = response.read()
            if return_bytes: return downloaded_image

            downloaded_image = Image.open(BytesIO(downloaded_image))
            return downloaded_image
        except:
            return None

    ### Concatenation of all functions for one car subclass
    def work_one_car_class(data_dict, retrieved_elements, not_retrievable):
        try:
            if TIME_FUNCTIONS:
                #Time link extractor to 300 seconds
                single_image_page_urls = timer(extract_info_for_car_subclass,300,data_dict['url'])
            else:
                single_image_page_urls = extract_info_for_car_subclass(data_dict['url'])

            if single_image_page_urls is not None:
                image_iterator = tqdm(single_image_page_urls, position=1)
                for single_page_url in image_iterator:
                    try:
                        if TIME_FUNCTIONS:
                            #Give 10 seconds to get image download link and infos. If the limit is reached,
                            #an error is thrown (incorrect number of arguments) and caught. This sample will then
                            #be bypassed.
                            image_iterator.set_description('Getting download info... ')
                            download_link, infos   = timer(get_image_url,15,single_page_url)
                            image_iterator.set_description('Downloading image... ')
                            downloaded_image       = timer(download,15,download_link)
                        else:
                            image_iterator.set_description('Getting download info... ')
                            download_link, infos   = get_image_url(single_page_url)
                            image_iterator.set_description('Downloading image... ')
                            downloaded_image       = download(download_link)

                        image_iterator.set_description('Inserting to database... ')
                        info_dict = {'model':data_dict['name'][0], 'submodel':data_dict['name'][1], 'image':downloaded_image, 'download_link':download_link, 'url':data_dict['url']}
                        info_dict.update(infos)
                        retrieved_elements.insert_one(info_dict)
                        time.sleep(DOWNLOAD_DELAY*(1+random.random()*0.2))
                        opt.counter += 1
                    except:
                        not_retrievable.insert_one({'url':single_page_url})
                    if opt.counter>=opt.max_images:
                        print('REACHED MAX NUMBER OF IMAGES: {} - SCRAPPING TERMINATED.'.format(opt.max_images))
                        import sys
                        sys.exit()
            else:
                pass
        except:
            pass

        if CHECK_INTERNET: check_internet()

    """ ================================================== """
    ### First Website Access
    html = get_response_and_soup(PRIME_URL)
    #All available car types
    options = html.select('a[class="tooltips"]')
    options = [x for x in options if 'catalog' in str(x)]
    options = {x.text:{'url':BASE_URL+'/'+x.attrs['href'], 'n_images':int(x.attrs['data-original-title'].split(' ')[0])} for x in options}
    if len(opt.car_classes): options = {key:item for key,item in options.items() if key in opt.car_classes}

    n_avail_images = np.sum([x['n_images'] for _,x in options.items()])
    print('Number of available images to scrap: {}\n'.format(n_avail_images))

    # delete_collection_elements(retrieved_elements)

    ### GET LIST OF ELEMENTS TO RETRIEVE (-> CAR CLASSES)
    print('Checking remaining car classes to scrap... ',end='')
    time.sleep(0.5)
    elem_to_retrieve = scrap_car_model_urls(database, retrieved_elements, not_yet_retrieved, not_retrievable, load=True, options=options)
    print('Done.\n')


    """ ================================================== """
    ### START EXTRACTING AND DOWNLOADING ELEMENTS
    # _ = Parallel(n_jobs=2, prefer='threads')(delayed(work_one_car_class)(data_dict, retrieved_elements) for data_dict in tqdm(elem_to_retrieve, desc='Scrapping car classes', position=0))
    class_iterator = tqdm(elem_to_retrieve, position=0)
    for data_dict in class_iterator:
        class_iterator.set_description('Working on {}/{}...'.format(data_dict['name'][0], data_dict['name'][1]))
        work_one_car_class(data_dict, retrieved_elements, not_retrievable)








if __name__ == '__main__':
    main()
