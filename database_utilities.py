###LIBRARIES
import urllib, bs4, requests, pymongo, time, numpy as np
from tqdm import tqdm
import pandas as pd
import itertools as it, os
import time, random
from tqdm import tqdm
from joblib import Parallel, delayed




"""========================================="""
### Start Database
def start_database():
    # MONGODB config
    MONGODB_SERVER, MONGODB_PORT = "localhost", 27017
    MONGODB_DB_NAME              = "platemania_cars_retrieval"
    MONGODB_RETRIEVED_ELEMENTS = "retrieved_elements"
    MONGODB_NOT_YET_RETRIEVED  = "not_yet_retrieved"
    MONGODB_NOT_RETRIEVABLE    = "not_retrievable"


    ### Connect via PyMongo-Client
    try:
        client           = pymongo.MongoClient(MONGODB_SERVER, MONGODB_PORT)
        database         = client[MONGODB_DB_NAME]
        retrieved_elements = database[MONGODB_RETRIEVED_ELEMENTS]
        not_yet_retrieved  = database[MONGODB_NOT_YET_RETRIEVED]
        not_retrievable    = database[MONGODB_NOT_RETRIEVABLE]

    except error:
        raise Exception('There was an error connecting to mongodb at localhost: {}'.format(error))

    return database, retrieved_elements, not_yet_retrieved, not_retrievable

def delete_collection_elements(coll):
    for item in coll.find(): coll.delete_one(item)

def n_elem_coll(coll):
    return len([x['model'] for x in coll.find()])
