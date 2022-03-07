# -*- coding: utf-8 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This script creates the links from all the reusable objects in a MD. All the uuids that went through are
            stored in a csv with the information whtether the linkage was successful or not. This file is stored in the 
            same folder as the input_file with the uuids. If some of the ROs have changed and the script can't relink 
            them, they will be marked in the csv (output). If everything is okay, you will find the numbers 200 & 204 as 
            well as an empty error_Part1 in the list. Else you will have a number above 400 and an error_Part1 with the 
            errormessage. The errormessage tells you, which element caused the error in the linkage process. These uuids 
            have to be treated manually. Most of the time, it is enough to make just the link to the contact manually 
            and for the extents, keywords & formats you can make it automatically again...

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            proxy_dict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.
            input_file - path to the CSV-file (just one column with the uuids, first line is called "uuid") with the 
                         uuids you want to treat.
                         
Remarks:    ADAPT THE VARIABLES IN THE LINES BELOW
------------------------------------------------------------------------------------------------------------------------
"""
import openpyxl.descriptors
import urllib3
import requests
from requests.auth import HTTPBasicAuth
import json
import xml.etree.ElementTree as etree
import numpy as np
import pandas as pd
import os
import getpass
pd.options.mode.chained_assignment = None


# TODO: adapt the following variables
geocat_user = "egs"
geocat_environment = "INT"  # "INT" or "PROD"
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}
input_file = r"\\v0t0020a.adr.admin.ch\iprod\gdwh-vector\test\TESTING\egs\geocat\uuids_to_relink.csv"


# other definitions and general informations
geocat_password = getpass.getpass("Password: ")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
environment = {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
try:
    url_part1 = environment[geocat_environment]
except Exception as error:
    print("Your geocat-environment is wrong. It has to be \"PROD\" or \"INT\"")
    exit()
parser = etree.XMLParser(encoding="UTF-8")

# read the input file (just a CSV-list of uuids)
df_all = pd.read_csv(input_file, sep=';')

# Get cookies and token
print("get cookies")
a_session = requests.Session()
a_session.post(url_part1 + "eng/info?type=me", proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
session_cookies = a_session.cookies.get_dict()
token = session_cookies["XSRF-TOKEN"]
print("TOKEN: ", token)
df_all["Part1"] = None
df_all["Part2"] = None
df_all["error_Part1"] = None

for i in range(len(df_all)):
    uuid = df_all["uuid"][i]
    print(uuid)

    # processRecordSubtemplates - needed for RO
    headers_sub = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": token}
    url_sub = url_part1 + "api/0.1/records/" + uuid + "/processRecordSubtemplates"
    r_sub = a_session.post(url_sub, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers_sub, cookies=session_cookies)
    df_all["Part1"][i] = r_sub.status_code

    # processes/empty - needed for RO
    headers_pro = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": token}
    url_pro = url_part1 + "api/0.1/records/" + uuid + "/processes/empty"
    r_pro = a_session.post(url_pro, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers_pro, cookies=session_cookies)
    df_all["Part2"][i] = r_pro.status_code
    df_all["error_Part1"][i] = r_sub.content

# save the output-csv
path, extension = os.path.splitext(input_file)
output_file = path + "_out.csv"
df_all.to_csv(output_file, sep=';', encoding="utf-8-sig")
