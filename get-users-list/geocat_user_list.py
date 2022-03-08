# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This script gets the profile every user of geocat, including the group he belongs to.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            Path_File - path where the CSV will be saved. The name of the csv is generated automatically.
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
pd.options.mode.chained_assignment = None

# TODO: adapt the following variables
geocat_user = ""
geocat_environment = "INT"
Path_File_out = r""
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}

########################################################################################################################

# other definitions and general informations
geocat_password = getpass.getpass("Password: ")
headers = {"accept": "application/json"}
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# define the url
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
environment = {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
try:
    url_part1 = environment[geocat_environment]
except Exception as error:
    print("Your geocat-environment is wrong. It has to be \"PROD\" or \"INT\"")
    exit()
parser = etree.XMLParser(encoding='UTF-8')
url = url_part1 + "api/0.1/users"
url2 = url_part1 + "api/0.1/users/groups"


# get all the groups of INT - mail, adress,...
response = requests.get(url, headers=headers, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
data = json.loads(response.text)
df_info = pd.json_normalize(data)


# get all the groups of INT - groupinfo,
response = requests.get(url2, headers=headers, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
data = json.loads(response.text)
df_all = pd.json_normalize(data)


categories = {'Administrator':1, 'UserAdmin': 2, "Reviewer": 3, "Editor": 4, "RegisteredUser": 5}
df_all["categorie"] = df_all["userProfile"].map(categories)
df_all.sort_values("categorie", inplace=True)
df_all.drop_duplicates(subset=['userId', 'groupId'], keep='first', inplace=True)


df_info.set_index("id", inplace=True)
df_all["mail"] = ""
df_all["last_login"] = ""
df_all["enabled"] = ""
for i in range(len(df_all)):
    id = df_all["userId"].iloc[i]
    mail = df_info["emailAddresses"][id]
    if mail != []:
        df_all["mail"].iloc[i] = mail[0]
    else:
        df_all["mail"].iloc[i] = ""
    df_all["last_login"].iloc[i] = df_info["lastLoginDate"][id]
    df_all["enabled"].iloc[i] = df_info["enabled"][id]
df_all[["name", "bla"]] = df_all["userName"].str.split("(", 1, expand=True)
df_all["username"] = df_all["bla"].str.split(")", 1, expand=True)[0]
df_all["categorie"] = df_all["categorie"].astype(str)
df_all.sort_values(["groupName", "categorie", "username"], inplace=True, key=lambda x: x.str.lower())
df_all.reset_index(inplace=True)
df_all = df_all[['userId', 'username', 'name', 'mail', 'userProfile', 'groupId', 'groupName', 'enabled', 'last_login']]
df_all.to_csv(os.path.join(Path_File_out, "all_users_" + geocat_environment + ".csv"), sep=";", encoding="utf-8-sig", index=False)
