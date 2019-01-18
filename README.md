# image scrapper for platesmania.com

---
This respository contains a scrapping script to find and download car images from https://platesmania.com and to store them in a __MongoDB__ database. Scrapping speeds are adjusted to ensure both not getting your IP blocked and not accidentally DDOSing the site.
For longer runs, the scripts offers the option to set flags which firstly, check for internet connectivity periodically and if not available, hold until available again, and secondly, which time every function call to avoid getting stuck at scraps with very low bandwidth.

__NOTE:__ This script was created BEFORE finding the provided API https://platesmania.com/api. In larger quantities, this is the preferred way to extract images. Additionally, with the newly added cloudfare and captcha protection, this scrapper is no longer viable to use and serves only as a guide.

_Some parts in this repository are adapted from_ https://github.com/asanakoy/artprice_scrapper.

---

## PREREQUISITES
To get everything run, following prerequisites need to be fulfilled:


### 1. Install MongoDB (_optionally running on external drive_)
* To install and get MongoDB running, follow the instructions under https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/
* This install a configuration file under `/etc/mongod.conf`. Everything passed to a database will then be saved at the database path `dbPath`
   given in the conf-file, e.g. `/var/lib/mongodb`.
* If one wishes to save the data to a different location/disk (e.g. due to issues of space), using a symbolic link is prefered (and easy):

    1. First, ensure `mongodb` is not running: `sudo service mongod stop`.

    2. Denoting the current database save-path as `path/mongodb`, one runs
      `sudo mv /path/mongodb /path_new_save_folder`, where `/path_new_save_folder` points to the desired storing location, e.g. on a external drive.

    3. Now, after moving the database save folder to the new save space, we create a symbolic link to it: `sudo ln -s /path_new_save_folder/mongodb /path/mongodb`

    4. Ensure that mongodb has rights to access the new folder. Check this e.g. via `sudo -u mongodb -s cd /new_save_folder/mongodb`, where to test if `mongodb` has the rights to access the folder.  

    5. If this throws a `permission denied`-error, change folder access rights e.g. to all via `sudo chmod 777 /path_new_save_folder/mongodb`.

* Now, run `sudo service mongod start` and check `sudo service mongod status` if everything is working correctly (or by simply running `mongo`)

* Removing everything:
  * `sudo apt-get purge mongodb mongodb-clients mongodb-server mongodb-dev` and `sudo apt-get purge mongodb-org*`

* If a `mongod.servive not found`-error is thrown, run `sudo systemctl unmask mongodb` before restarting the service.

* If the whole service setup fails, one can run `mongodb` as a frontprocess as well, by setting a folder in `/data/db` (empty) or pointing it towards a folder on the external disk. Then
(1) `sudo rm /var/lib/mongodb/mongod.lock
(2) `mongod --repair
(3) `sudo mongod

### 2. Install required python packages
All python packages required are listed in `requirements.txt`. Simply run `bash installer.sh` to install them, ideally in a desired conda environment.

### 3. Chromedriver & Selenium
For educational purposes only: To extract proxies from cloudfare-protected sites such as https://hidemyna.net, `selenium` requires a chromedriver to run the website on a controlled chrome instance, allowing the scripts to bypass the cloudfare protection and extract the desired proxies. A tested `chromedriver` version comes within this repo, as well as a set of extracted proxies, that can be used (although some might now be obsolete), see `proxies.npy`.

---

## RUNNING THE SCRAPPER
To run the scrapper, simply run
```
python image_scrapper.py --max_images 10000 --car_classes BMW Audi
```
with flags `--max_images` to set the maximum number of images to download, and `--car_classes` to limit the scrapping to a set of car classes. Not providing these flags results in the scripts scrapping all available images. Add `--use_proxy` to use proxies that were previously extracted via `get_proxies.py`. Note that this is only required if one wishes to heavily parallelize scrapping. However, this puts a heavy strain on the servers and is not suggested.

__NOTE [1]__: By _all_ I refer to the downloadable number of images, at the time of creation of this repo, the pagination for car images stops after 100, e.g. allowing only 1000 images at most per car subclass.  

__NOTE [2]__: If one wishes to adjust the scrapper to extract different elements, take a look at `exploration.py`, which uses the key elements in an easy-to-understand and straightforward way to extract and download one picture.
