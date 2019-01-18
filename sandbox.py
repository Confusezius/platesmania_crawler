###LIBRARIES
import urllib, bs4, requests, pymongo, time, numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import pandas as pd
import itertools as it, os
import time, random
from io import BytesIO
from PIL import Image



"""=========================================="""
### Scrapper Variables
DOWNLOAD_DELAY = 0.8
BASE_URL  = 'http://platesmania.com'
PRIME_URL = 'http://platesmania.com/avto?&lang=en'
HEADER    = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
             'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
             'Accept-Encoding': 'none',
             'Accept-Language': 'en-US,en;q=0.8',
             'Connection': 'keep-alive'}


"""=========================================="""
# MONGODB config
MONGODB_SERVER, MONGODB_PORT = "localhost", 27017
MONGODB_DB_NAME              = "platemania_cars_retrieval"
MONGODB_RETRIEVED_ELEMENTS = "retrieved_elements"
MONGODB_NOT_YET_RETRIEVED  = "not_yet_retrieved"
MONGODB_NOT_RETRIEVABLE    = "not_retrievable"


"""=========================================="""
### Connect via PyMongo-Client
client           = pymongo.MongoClient(MONGODB_SERVER, MONGODB_PORT)

database           = client[MONGODB_DB_NAME]
retrieved_elements = database[MONGODB_RETRIEVED_ELEMENTS]
not_yet_retrieved  = database[MONGODB_NOT_YET_RETRIEVED]
not_retrievable    = database[MONGODB_NOT_RETRIEVABLE]

def delete_collection_elements(coll):
    for item in coll.find(): coll.delete_one(item)

# delete_collection_elements(retrieved_elements)
retrieved_elements.estimated_document_count()
not_yet_retrieved.estimated_document_count()
not_retrievable.estimated_document_count()
# du.n_elem_coll(retrieved_elements)

elem_to_retrieve = list(set([(tuple(x['name']),x['url']) for x in not_yet_retrieved.find({},{'_id':0})])-set([((x['model'],x['submodel']),x['url']) for x in retrieved_elements.find({},{'_id':0,'image':0})]))
res = set([((x['model'],x['submodel']),x['url']) for x in retrieved_elements.find({},{'_id':0,'image':0})])
res = list(res)

#[(x['model'],x['submodel']) for x in retrieved_elements.find()]
#res = retrieved_elements.find({'model':'JMC'})
example = retrieved_elements.find_one()
Image.open(BytesIO(example['plate_pic']))
Image.open(BytesIO(example['plate_pic']))

plt.figure(figsize=(6,6))
plt.imshow(np.array(Image.open(BytesIO(example['image']))))
plt.title('Car: {} of type {}'.format(example['model'],example['submodel']))
plt.xticks([])
plt.yticks([])
plt.show()



# for x in not_yet_retrieved.find({},{'_id':0}):
#     print(x)
