###LIBRARIES
import urllib, bs4, requests, pymongo, time, numpy as np
from tqdm import tqdm
import pandas as pd
import itertools as it, os
import time, random
from tqdm import tqdm
from joblib import Parallel, delayed




""" ====================================================== """
### GET PROXIES
class ProxyHandler():
    def __init__():
        self.proxies = np.load('proxies.py')
        self.proxy_dict = None

    def update_proxy(self):
        # proxies = get_proxies_FreeProxyListNet()
        if len(self.proxies)==0:
            raise Exception('Ran out of availble proxies!')

        new_proxy = self.proxies.pop()
        self.proxy_dict    = {'http': new_proxy, 'https': new_proxy}
        urllib_data = urllib.request.ProxyHandler(self.proxy_dict)
        urllib_data = urllib.request.build_opener(urllib_data)
        urllib.request.install_opener(urllib_data)
