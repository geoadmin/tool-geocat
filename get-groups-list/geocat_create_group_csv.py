# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This script can update automatically the csv-file called "groups.csv", which is used for many other scripts.
            Recommendation to first save the new file with an other name than the current (old) one and to check it.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                        don't need that. It is necessary when you run the script with VPN or directly in Wabern.
            Path_File_out - where to save the information about. Recommendation to first save the new file with an other 
                            name than the current (old) one and to check it. Then you can overwrite it.
            
Remarks:    ADAPT THE VARIABLES IN LINES THE LINES BELOW
            Path of the current groups-CSV:
            r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\groups.csv"

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
pd.options.mode.chained_assignment = None

# TODO: adapt the following variables
geocat_user = ""
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}
Path_File_out = r""

########################################################################################################################

# other definitions and general informations
geocat_password = getpass.getpass("Password: ")
url_int = "https://geocat-int.dev.bgdi.ch/geonetwork/srv/api/0.1/groups"
url_prod = "https://www.geocat.ch/geonetwork/srv/api/0.1/groups"
headers = {"accept": "application/json"}
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# get all the groups of INT
response_int = requests.get(url_int, headers=headers, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
data_int = json.loads(response_int.text)
print("getting information on INT...")
df_int = pd.json_normalize(data_int)
df_int = df_int[["name", "id", "label.ger"]]
df_int.columns = [str(col) + '_int' for col in df_int.columns]
df_int.set_index("name_int", inplace=True)
df_int["harvested_int"] = ""
# check if the group is harvested or not harvested
for i in range(len(df_int)):
    groupnumber = df_int.iloc[i]["id_int"]
    url_h = "https://geocat-int.dev.bgdi.ch/geonetwork/srv/ger/q?from=1&to=2000&facet.q=isHarvested%2Fy&_groupOwner=" + str(groupnumber)
    r_main_h = requests.get(url_h, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
    tree_h = etree.fromstring(r_main_h.content)
    number_h = tree_h.find("./summary").attrib["count"]
    url_nh = "https://geocat-int.dev.bgdi.ch/geonetwork/srv/ger/q?from=1&to=2000&facet.q=isHarvested%2Fn&_groupOwner=" + str(groupnumber)
    r_main_nh = requests.get(url_nh, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
    tree_nh = etree.fromstring(r_main_nh.content)
    number_nh = tree_nh.find("./summary").attrib["count"]
    if (int(number_h) == 0) & (int(number_nh) != 0):
        df_int["harvested_int"].iloc[i] = "no"
    elif (int(number_h) != 0) & (int(number_nh) == 0):
        df_int["harvested_int"].iloc[i] = "yes"
    elif (int(number_h) != 0) & (int(number_nh) != 0):
        df_int["harvested_int"].iloc[i] = "both - treated as harvested in the scripts"
    elif (int(number_h) == 0) & (int(number_nh) == 0):
        df_int["harvested_int"].iloc[i] = "none"        
    
    
# get all the groups of PROD
response_prod = requests.get(url_prod, headers=headers, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
data_prod = json.loads(response_prod.text)
print("getting information on PROD...")
df_prod = pd.json_normalize(data_prod)
df_prod = df_prod[["name", "id", "label.ger"]]
df_prod.columns = [str(col) + '_prod' for col in df_prod.columns]
df_prod.set_index("name_prod", inplace=True)
df_prod["harvested_prod"] = ""
# check if the group is harvested or not harvested
for i in range(len(df_prod)):
    groupnumber = df_prod.iloc[i]["id_prod"]
    url_h = "https://geocat-int.dev.bgdi.ch/geonetwork/srv/ger/q?from=1&to=2000&facet.q=isHarvested%2Fy&_groupOwner=" + str(groupnumber)
    r_main_h = requests.get(url_h, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
    tree_h = etree.fromstring(r_main_h.content)
    number_h = tree_h.find("./summary").attrib["count"]
    url_nh = "https://geocat-int.dev.bgdi.ch/geonetwork/srv/ger/q?from=1&to=2000&facet.q=isHarvested%2Fn&_groupOwner=" + str(groupnumber)
    r_main_nh = requests.get(url_nh, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
    tree_nh = etree.fromstring(r_main_nh.content)
    number_nh = tree_nh.find("./summary").attrib["count"]
    if (int(number_h) == 0) & (int(number_nh) != 0):
        df_prod["harvested_prod"].iloc[i] = "no"
    elif (int(number_h) != 0) & (int(number_nh) == 0):
        df_prod["harvested_prod"].iloc[i] = "yes"
    elif (int(number_h) != 0) & (int(number_nh) != 0):
        df_prod["harvested_prod"].iloc[i] = "both - treated as harvested in the scripts"
    elif (int(number_h) == 0) & (int(number_nh) == 0):
        df_prod["harvested_prod"].iloc[i] = "none"    
        
# save all the infos as csv.         
df_all = pd.concat([df_int, df_prod], axis=1, join='outer')
df_all.sort_index(ascending=True, inplace=True)
df_all.to_csv(Path_File_out, sep=';', encoding="utf-8-sig")
print("File is saved: " + Path_File_out)

