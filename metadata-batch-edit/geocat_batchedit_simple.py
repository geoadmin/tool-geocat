# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    With this script, you can make simple batch edits on a list of uuids. gn_replace, gn_add & gn_delete are
            simple batch edits, when they are executed on non reusable objects like titles, protocols, dates, links,...
            All the uuids that went through are stored in a csv with the information on the statuscode of the batch edit. 
            This file is stored in the same folder as the input_file with the uuids.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            input_file - csv-file with at least a column named "UUID". There can be other columns present
            xpath - xpath (batchedit) to the attribute you want to change
            value - value (batchedit) that you want to change
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                        don't need that. It is necessary when you run the script with VPN or directly in Wabern.

Remarks:    ADAPT THE VARIABLES IN THE LINES BELOW
------------------------------------------------------------------------------------------------------------------------
"""
import xml.etree.ElementTree as etree
import pandas as pd
import requests
import urllib3
import numpy as np
from requests.auth import HTTPBasicAuth
import json
import os
import getpass

# TODO: adapt the following variables
geocat_user = ""
geocat_environment = "INT"  # "INT" or "PROD"
input_file = r""
xpath = "/che:CHE_MD_Metadata/gmd:identificationInfo/che:CHE_MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString[text() = 'title']"
value = "<gn_replace>new_title</gn_replace>"
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}

########################################################################################################################

# other definitions and general informations
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
geocat_password = getpass.getpass("Password: ")
environment = {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
try:
    url_part1 = environment[geocat_environment]
except Exception as error:
    print("Your geocat-environment is wrong. It has to be \"PROD\" or \"INT\"")
    exit()

# Get cookies and token
print("get cookies")
a_session = requests.Session()
a_session.post(url_part1 + "eng/info?type=me", proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
session_cookies = a_session.cookies.get_dict()
token = session_cookies["XSRF-TOKEN"]
print("TOKEN: ", token)
headers = {"accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": token}

# get list of uuids
all_uuids = pd.read_csv(input_file, sep=';', encoding='ISO-8859-1')
all_uuids = all_uuids[["UUID"]]
print(all_uuids)
all_uuids["api_response"] = ""

# go through every line in the BMD-Excel and collect its corresponding information
print("Batch Edit every UUID")
for i in range(len(all_uuids)):
    uuid = all_uuids.iloc[i]["UUID"]
    json_input = {"value": value, "xpath": xpath}
    payload = r"[" + json.dumps(json_input) + "]"
    url  = url_part1 + "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=false"
    response = a_session.put(url, data=payload, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers, cookies=session_cookies)
    all_uuids["api_response"].iloc[i] = str(response.status_code)

output_file = input_file[:-4] + "_out" + input_file[-4:]
all_uuids.to_csv(output_file, sep=';')
print("MDs should have been modificated. Please check a few of them!")
print("An overview is saved in " + output_file)
print("Reminder: 201 as response is a good sign")
