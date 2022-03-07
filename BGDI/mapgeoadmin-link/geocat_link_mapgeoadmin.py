# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This was made for the Ticket METADATA_SB-152. The script goes through a list of uuids (created from BMD4MUM 
            and separated by bmd_group_by_amt.py). It searches for existing links. Then it adds a link of MAP:Preview to
            all those of the list, that don't have one yet. the ending of the link is taken from the bmd-excel.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            protokoll - protocol of the link you add
            title - title of the link you add, in all languages
            description - description of the link you add, in all languages (can be equal to the title)
            map_url_base - base of the map_url. the ending of the link is taken from the bmd-excel.
            folder - folder of where the bmd-excel is lying
            file - name of the bmd-excel
            geocat_environment - "INT" or "PROD"
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.

Remarks:    ADAPT THE VARIABLES IN LINES THE LINES BELOW
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
geocat_user = "egs"
protokoll = "MAP:Preview"
title = {"de": "Vorschau map.geo.admin.ch", "fr": "Aperçu map.geo.admin.ch", "en": "Preview map.geo.admin.ch", "it": "Previsione map.geo.admin.ch"}
description = title
map_url_base = "https://map.geo.admin.ch/?layers="
folder = r"\\v0t0020a.adr.admin.ch\iprod\gdwh-vector\test\TESTING\egs\geocat\BGDI\Bundesamt"
file = "vbs.xlsx"
geocat_environment = "PROD"  # "INT" or "PROD"
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}

########################################################################################################################

# define important paths of geocat-XML
x_resp = "{http://www.isotc211.org/2005/gmd}contact/{http://www.geocat.ch/2008/che}CHE_CI_ResponsibleParty"
x_org = "{http://www.isotc211.org/2005/gmd}organisationName"
x_char = "{http://www.isotc211.org/2005/gco}CharacterString"
x_idinf = "{http://www.isotc211.org/2005/gmd}identificationInfo"
x_data_id = "{http://www.geocat.ch/2008/che}CHE_MD_DataIdentification"
x_cit = "{http://www.isotc211.org/2005/gmd}citation"
x_cicit = "{http://www.isotc211.org/2005/gmd}CI_Citation"
x_tit = "{http://www.isotc211.org/2005/gmd}title"
x_pttxt = "{http://www.isotc211.org/2005/gmd}PT_FreeText"
x_txt = "{http://www.isotc211.org/2005/gmd}textGroup"
x_loc = "{http://www.isotc211.org/2005/gmd}LocalisedCharacterString"
x_lan = "{http://www.isotc211.org/2005/gmd}language"
x_lanc = "{http://www.isotc211.org/2005/gmd}LanguageCode"
x_srv = "{http://www.isotc211.org/2005/srv}SV_ServiceIdentification"
x_kws = "{http://www.isotc211.org/2005/gmd}MD_Keywords"
x_tran = "{http://www.isotc211.org/2005/gmd}transferOptions"
x_onl = "{http://www.isotc211.org/2005/gmd}CI_OnlineResource"
x_url = "{http://www.isotc211.org/2005/gmd}URL"
x_prot = "{http://www.isotc211.org/2005/gmd}protocol"
x_lurl = "{http://www.geocat.ch/2008/che}LocalisedURL"
x_link = "{http://www.isotc211.org/2005/gmd}linkage"

# other definitions and general informations
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
geocat_password = getpass.getpass("Password: ")
environment = {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
try:
    url_part1 = environment[geocat_environment]
except Exception as error:
    print("Your geocat-environment is wrong. It has to be \"PROD\" or \"INT\"")
    exit()

# Get cookies and token - ok
print("get cookies")
a_session = requests.Session()
a_session.post(url_part1 + "eng/info?type=me", proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
session_cookies = a_session.cookies.get_dict()
token = session_cookies["XSRF-TOKEN"]
print("TOKEN: ", token)
headers = {"accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": token}

# read excel from BMD
bmd_list = pd.read_excel(os.path.join(folder, file))
bmd_list = bmd_list.drop_duplicates(subset=['TECHPUBLAYERNAME', 'GDSKEY', 'GEOCATUUID'], keep='last')
bmd_list["procedure"] = ""
df_all = pd.DataFrame([["UUID", "Protokoll", "URL"]], columns=["UUID", "Protokoll", "URL"])

# go through every line in the BMD-Excel and collect its corresponding information
print("BMD-Liste durchgehen")
for i in range(len(bmd_list)):
    uuid = bmd_list.iloc[i]["GEOCATUUID"]
    techpublayer = bmd_list.iloc[i]["TECHPUBLAYERNAME"]
    if isinstance(uuid, str):
        print(str(i) + "   " + uuid)  # , end="   ", flush=True)
        all_links = []
        # get the XML of the uuid
        new_url = url_part1 + "ger/xml.metadata.get?uuid=" + uuid
        r = requests.get(new_url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
        if r.status_code != 200:
            print("No vaild uuid")

        else:
            # read the XML and save the info
            abcd = []
            tree = etree.fromstring(r.content)
            test = tree.findall(".//" + x_tran + "//" + x_onl)
            if len(test) == 1:
                prot1 = tree.findtext(".//" + x_tran + "//" + x_onl + "/" + x_prot + "/" + x_char)
                url1 = tree.findtext(".//" + x_tran + "//" + x_onl + "//" + x_url)
                all_links.append([uuid, prot1, url1])

            elif len(test) > 1:
                for key2 in test:
                    for key3 in key2.iter():
                        if key3.tag == x_prot:
                            for key4 in key3.iter():
                                if key4.tag == x_char:
                                    prot1 = key4.text
                        if key3.tag == x_link:
                            for key4 in key3.iter():
                                if key4.tag == x_lurl:
                                    if key4.attrib["locale"] == "#DE":
                                        url1 = key4.text

                    all_links.append([uuid, prot1, url1])
            df = pd.DataFrame(all_links, columns=["UUID", "Protokoll", "URL"])
            df_short = df.loc[(df['URL'].str.contains('map.geo.admin.ch')) | (df['Protokoll'].str.contains(protokoll))]
            df_all = pd.concat([df_all, df])
            map_url = map_url_base + techpublayer
            """
            for j in range(len(df_short)):
                if ("map.geo.admin.ch" in df_short["URL"].iloc[j]) & (df_short["Protokoll"].iloc[j] == "CHTOPO:specialised-geoportal"):
                    print("delete CHTOPO:specialised-geoportal", end="   ", flush=True)
                    json_del = {"value": "<gn_delete></gn_delete>", "xpath": "che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/che:PT_FreeURL/che:URLGroup/che:LocalisedURL[contains(text(), \"" + df_short["URL"].iloc[j] + "\")]/../../../../../.."}
                    payload_del = r"[" + json.dumps(json_del) + "]"
                    url_del = url_part1 + "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=false"
                    r_del = a_session.put(url_del, data=payload_del, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers, cookies=session_cookies)
                    print(r_del.status_code)
                    abcd.append("delete CHTOPO:specialised-geoportal")
                    if r_del.status_code > 205:
                        print("--- ERROR ---")
                        print(r_del.content)
                elif (df_short["Protokoll"].iloc[j] == "MAP:Preview") & ("map.geo.admin.ch" in df_short["URL"].iloc[j]):
                    print("delete & add MAP:Preview", end="   ", flush=True)
                    json_del = {"value": "<gn_delete></gn_delete>", "xpath": "che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/che:PT_FreeURL/che:URLGroup/che:LocalisedURL[contains(text(), \"" + df_short["URL"].iloc[j] + "\")]/../../../../../.."}
                    payload_del = r"[" + json.dumps(json_del) + "]"
                    url_del = url_part1 + "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=false"
                    r_del = a_session.put(url_del, data=payload_del, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers, cookies=session_cookies)
                    print(r_del.status_code, end="   ", flush=True)
                    if r_del.status_code > 205:
                        print("--- ERROR ---")
                        print(r_del.content)
                    value_add = '<gn_add><gmd:transferOptions xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:MD_DigitalTransferOptions xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:onLine xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:CI_OnlineResource xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:linkage xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:URL xmlns:gmd=\"http://www.isotc211.org/2005/gmd\">' + map_url + '</gmd:URL><che:PT_FreeURL xmlns:che=\"http://www.geocat.ch/2008/che\"><che:URLGroup xmlns:che=\"http://www.geocat.ch/2008/che\"><che:LocalisedURL xmlns:che=\"http://www.geocat.ch/2008/che\" locale=\"#DE\">' + map_url + '</che:LocalisedURL></che:URLGroup><che:URLGroup xmlns:che=\"http://www.geocat.ch/2008/che\"><che:LocalisedURL xmlns:che=\"http://www.geocat.ch/2008/che\" locale=\"#FR\">' + map_url + '</che:LocalisedURL></che:URLGroup><che:URLGroup xmlns:che=\"http://www.geocat.ch/2008/che\"><che:LocalisedURL xmlns:che=\"http://www.geocat.ch/2008/che\" locale=\"#IT\">' + map_url + '</che:LocalisedURL></che:URLGroup><che:URLGroup xmlns:che=\"http://www.geocat.ch/2008/che\"><che:LocalisedURL xmlns:che=\"http://www.geocat.ch/2008/che\" locale=\"#EN\">' + map_url + '</che:LocalisedURL></che:URLGroup><che:URLGroup xmlns:che=\"http://www.geocat.ch/2008/che\"><che:LocalisedURL xmlns:che=\"http://www.geocat.ch/2008/che\" locale=\"#RM\">' + map_url + '</che:LocalisedURL></che:URLGroup></che:PT_FreeURL></gmd:linkage><gmd:protocol xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gco:CharacterString xmlns:gco=\"http://www.isotc211.org/2005/gco\">' + protokoll + '</gco:CharacterString></gmd:protocol><gmd:name xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" xsi:type="gmd:PT_FreeText_PropertyType" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><gco:CharacterString xmlns:gco=\"http://www.isotc211.org/2005/gco\">' + title["de"] + '</gco:CharacterString><gmd:PT_FreeText xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#DE\">' + title["de"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#FR\">' + title["fr"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#IT\">' + title["it"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#EN\">' + title["en"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString locale=\"#RM\"/></gmd:textGroup></gmd:PT_FreeText></gmd:name><gmd:description xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" xsi:type="gmd:PT_FreeText_PropertyType" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><gco:CharacterString xmlns:gco=\"http://www.isotc211.org/2005/gco\">' + description["de"] + '</gco:CharacterString><gmd:PT_FreeText xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#DE\">' + description["de"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#FR\">' + description["fr"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#IT\">' + description["it"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#EN\">' + description["en"] + '</gmd:LocalisedCharacterString></gmd:textGroup>	<gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString locale=\"#RM\"/></gmd:textGroup></gmd:PT_FreeText></gmd:description></gmd:CI_OnlineResource></gmd:onLine></gmd:MD_DigitalTransferOptions></gmd:transferOptions></gn_add>'
                    xpath_add = "che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions[1]"
                    json_add = {"value": value_add, "xpath": xpath_add}
                    payload_add = r"[" + json.dumps(json_add) + "]"
                    url_add = url_part1 + "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=false"
                    r_add = a_session.put(url_add, data=payload_add, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers, cookies=session_cookies)
                    print(r_add.status_code)
                    abcd.append("delete & add MAP:Preview")

                    abcd.append("MAP:Preview is already present with a map.geo.admin.ch-link")
                    """
            if "MAP:Preview" not in df_short.Protokoll.values:
                print("add MAP:Preview", end="   ", flush=True)
                value_add = '<gn_add><gmd:transferOptions xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:MD_DigitalTransferOptions xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:onLine xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:CI_OnlineResource xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:linkage xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:URL xmlns:gmd=\"http://www.isotc211.org/2005/gmd\">' + map_url + '</gmd:URL><che:PT_FreeURL xmlns:che=\"http://www.geocat.ch/2008/che\"><che:URLGroup xmlns:che=\"http://www.geocat.ch/2008/che\"><che:LocalisedURL xmlns:che=\"http://www.geocat.ch/2008/che\" locale=\"#DE\">' + map_url + '</che:LocalisedURL></che:URLGroup><che:URLGroup xmlns:che=\"http://www.geocat.ch/2008/che\"><che:LocalisedURL xmlns:che=\"http://www.geocat.ch/2008/che\" locale=\"#FR\">' + map_url + '</che:LocalisedURL></che:URLGroup><che:URLGroup xmlns:che=\"http://www.geocat.ch/2008/che\"><che:LocalisedURL xmlns:che=\"http://www.geocat.ch/2008/che\" locale=\"#IT\">' + map_url + '</che:LocalisedURL></che:URLGroup><che:URLGroup xmlns:che=\"http://www.geocat.ch/2008/che\"><che:LocalisedURL xmlns:che=\"http://www.geocat.ch/2008/che\" locale=\"#EN\">' + map_url + '</che:LocalisedURL></che:URLGroup><che:URLGroup xmlns:che=\"http://www.geocat.ch/2008/che\"><che:LocalisedURL xmlns:che=\"http://www.geocat.ch/2008/che\" locale=\"#RM\">' + map_url + '</che:LocalisedURL></che:URLGroup></che:PT_FreeURL></gmd:linkage><gmd:protocol xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gco:CharacterString xmlns:gco=\"http://www.isotc211.org/2005/gco\">' + protokoll + '</gco:CharacterString></gmd:protocol><gmd:name xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" xsi:type="gmd:PT_FreeText_PropertyType" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><gco:CharacterString xmlns:gco=\"http://www.isotc211.org/2005/gco\">' + title["de"] + '</gco:CharacterString><gmd:PT_FreeText xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#DE\">' + title["de"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#FR\">' + title["fr"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#IT\">' + title["it"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#EN\">' + title["en"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString locale=\"#RM\"/></gmd:textGroup></gmd:PT_FreeText></gmd:name><gmd:description xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" xsi:type="gmd:PT_FreeText_PropertyType" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><gco:CharacterString xmlns:gco=\"http://www.isotc211.org/2005/gco\">' + description["de"] + '</gco:CharacterString><gmd:PT_FreeText xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#DE\">' + description["de"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#FR\">' + description["fr"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#IT\">' + description["it"] + '</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" locale=\"#EN\">' + description["en"] + '</gmd:LocalisedCharacterString></gmd:textGroup>	<gmd:textGroup xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:LocalisedCharacterString locale=\"#RM\"/></gmd:textGroup></gmd:PT_FreeText></gmd:description></gmd:CI_OnlineResource></gmd:onLine></gmd:MD_DigitalTransferOptions></gmd:transferOptions></gn_add>'
                xpath_add = "che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions[1]"
                json_add = {"value": value_add, "xpath": xpath_add}
                payload_add = r"[" + json.dumps(json_add) + "]"
                url_add = url_part1 + "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=false"
                r_add = a_session.put(url_add, data=payload_add, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers, cookies=session_cookies)
                print(r_add.status_code)
                abcd.append("add MAP:Preview")
                abcd.append(r_add.status_code)
            bmd_list["procedure"].iloc[i] = str(abcd)
name = file.split(".")[0]
df_all.to_csv(os.path.join(folder, "control", name + "_alllinks.csv"), sep=';')
bmd_list.to_csv(os.path.join(folder, "control", name + "_procedures.csv"), sep=';')
