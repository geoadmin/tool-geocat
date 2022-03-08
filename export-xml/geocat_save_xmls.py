# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This script was created for METADATA_SB-157. It takes a list of uuids, saves them as xml in a folder
            and finally zips that folder (if wanted).

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            input_file - csv-file with at least a column named "UUID". There can be other columns present
            folder - path to the folder, where the xmls should be saved in. It will be zipped at the end
            xml_types - you can chose which type of xml you want ["GM03", "ISO19139", "ISO19139.che"]. It must be a list
            zip_folder - if "yes", then the folder will additionally be zipped at the end of the script. the
                         unzipped folder remains
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                        don't need that. It is necessary when you run the script with VPN or directly in Wabern.

Remarks:    ADAPT THE VARIABLES IN THE LINES BELOW
------------------------------------------------------------------------------------------------------------------------
"""
import pandas as pd
import requests
import urllib3
import shutil
from requests.auth import HTTPBasicAuth
import os
import getpass

# TODO: adapt the following variables
geocat_user = ""
geocat_environment = "PROD"  # "INT" or "PROD"
input_file = r""
folder = r""
xml_types = ["ISO19139.che"]  # ["GM03", "ISO19139", "ISO19139.che"]
zip_folder = "yes"
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}

########################################################################################################################

# other definitions and general informations
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
geocat_password = getpass.getpass("Password: ")
environment = {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
types = {"GM03": [".gm03", "ger/gm03.xml?uuid=", ""],
         "ISO19139": [".iso19139", "ger/xml_iso19139?uuid=", ""],
         "ISO19139.che": ["", "api/records/", "/formatters/xml?approved=true"]}
try:
    url_part1 = environment[geocat_environment]
except Exception as error:
    print("Your geocat-environment is wrong. It has to be \"PROD\" or \"INT\"")
    exit()

# check if your input for xml_types is correctly
if not all(elem in types.keys() for elem in xml_types):
    print("You can just choose one or several of " + str(types.keys()))
    print("you chose " + str(xml_types))
    print("Please change your input!")
    exit()

# check if the folder exists and make a new one if not.
if not os.path.isdir(folder):
    os.makedirs(folder)

# get list of uuids
all_uuids = pd.read_csv(input_file, sep=';', encoding='ISO-8859-1')
all_uuids = all_uuids[["UUID"]]

# write out the xml for each xml-type and each uuid
for i in range(len(all_uuids)):
    uuid = all_uuids.iloc[i]["UUID"]
    print(uuid)
    for xml_type in xml_types:
        url = url_part1 + types[xml_type][1] + uuid + types[xml_type][2]
        resp = requests.get(url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
        with open(os.path.join(folder, uuid + types[xml_type][0] + ".xml"), "wb") as f:
            f.write(resp.content)

if zip_folder == "yes":
    shutil.make_archive(folder, 'zip', folder)

