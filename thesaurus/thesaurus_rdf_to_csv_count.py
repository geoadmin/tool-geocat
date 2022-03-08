# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    It takes the rdf from the geocat-website and writes all the keywords with its translations into a table.
            Additionally you can chose whether you also want it to calculate how much each keyword is used (for all 
            languages together or also for each language seperately).
            This script was created during the cleanup of the geocat-ch-Thesarus

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            FileIn - path & filename of the RDF-file of the thesaurus
            FileOut - path & filename of the newly counted CSV
            catalog - "geocat" or "gemet" (in small letters)
            count - "yes" or "no". If yes, it counts how many times each keyword is used for each language separately
            count_all - "yes" or "no". If yes, it counts how many times each keyword is used for all languages together
            geocat_environment - "INT" or "PROD"
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                        don't need that. It is necessary when you run the script with VPN or directly in Wabern

Remarks:    ADAPT THE VARIABLES IN LINES THE LINES BELOW
            The script might take a while when it is counting the apparitions in all languages
            (Geocat ca. 20min; Gemet ca. 1h30min)
            If it just counts it for all languages at once, it takes about 8min for Geocat.
------------------------------------------------------------------------------------------------------------------------
"""
import xml.etree.ElementTree as etree
import os
import pandas as pd
import requests
import urllib3
import numpy as np
import datetime as dt
from requests.auth import HTTPBasicAuth
import getpass


# TODO: adapt the following variables
geocat_user = ""
FileIn = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\thesaurus\geocat_new.rdf"
FileOut = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\thesaurus\geocat_20210908_count.csv"
catalog = "geocat"
count = "no"
count_all = "yes"
geocat_environment = "PROD"
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}

########################################################################################################################

# other definitions and general informations
geocat_password = getpass.getpass("Password: ")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
environment = {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
try:
    url_part1 = environment[geocat_environment]
except Exception as error:
    print("Your geocat-environment is wrong. It has to be \"PROD\" or \"INT\"")
    exit()
url_part2 = "/q?from=1&to=20&keyword="
parser = etree.XMLParser(encoding='UTF-8')
de, fr, it, en, code, de_nr, fr_nr, it_nr, en_nr = {}, {}, {}, {}, {}, {}, {}, {}, {}

# open rdf-file
if os.path.isfile(FileIn):
    tree = etree.parse(FileIn, parser)
    root = tree.getroot()
    descriptions = list(root)
    i = 0
    for desc in descriptions:
        # prepare keyword-id
        if list(desc.attrib.keys())[0] == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about":
            cat_id = list(desc.attrib.values())[0]
            if catalog == "geocat":
                try:
                    code[cat_id] = cat_id.split("#")[1]
                except:
                    pass
            elif catalog == "gemet":
                try:
                    code[cat_id] = cat_id.split("/")[-1]
                except:
                    pass
            labels = list(desc)
            for jj in labels:
                # Find the labels of the various languages in prefLabel and count them (if count is set on "yes")
                if jj.tag == '{http://www.w3.org/2004/02/skos/core#}prefLabel':
                    if list(jj.attrib.values())[0] == "de":
                        de[cat_id] = jj.text
                        i += 1
                        print(i)
                        if count == "yes" and jj.text is not None:
                            url_de = url_part1 + "ger" + url_part2 + jj.text
                            r1 = requests.get(url_de, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
                            tree = etree.fromstring(r1.content)
                            de_nr[cat_id] = tree.find("./summary").attrib["count"]
                    elif list(jj.attrib.values())[0] == "fr":
                        fr[cat_id] = jj.text
                        if count == "yes" and jj.text is not None:
                            url_fr = url_part1 + "fre" + url_part2 + jj.text
                            r2 = requests.get(url_fr, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
                            tree = etree.fromstring(r2.content)
                            fr_nr[cat_id] = tree.find("./summary").attrib["count"]
                    elif list(jj.attrib.values())[0] == "it":
                        it[cat_id] = jj.text
                        if count == "yes" and jj.text is not None:
                            url_it = url_part1 + "ita" + url_part2 + jj.text
                            r3 = requests.get(url_it, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
                            tree3 = etree.fromstring(r3.content)
                            it_nr[cat_id] = tree3.find("./summary").attrib["count"]
                    elif list(jj.attrib.values())[0] == "en":
                        en[cat_id] = jj.text
                        if count == "yes" and jj.text is not None:
                            url_en = url_part1 + "eng" + url_part2 + jj.text
                            r4 = requests.get(url_en, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
                            tree = etree.fromstring(r4.content)
                            en_nr[cat_id] = tree.find("./summary").attrib["count"]

    # make a nice table
    data_code = pd.DataFrame.from_dict(code, orient='index', columns=['concept-cat_id'])
    data_de = pd.DataFrame.from_dict(de, orient='index', columns=['de'])
    data_fr = pd.DataFrame.from_dict(fr, orient='index', columns=['fr'])
    data_it = pd.DataFrame.from_dict(it, orient='index', columns=['it'])
    data_en = pd.DataFrame.from_dict(en, orient='index', columns=['en'])
    if count == 'yes':
        data_de_nr = pd.DataFrame.from_dict(de_nr, orient='index', columns=['de_nr'])
        data_fr_nr = pd.DataFrame.from_dict(fr_nr, orient='index', columns=['fr_nr'])
        data_en_nr = pd.DataFrame.from_dict(en_nr, orient='index', columns=['en_nr'])
        data_it_nr = pd.DataFrame.from_dict(it_nr, orient='index', columns=['it_nr'])
        df_all = pd.concat([data_code, data_de, data_fr, data_it, data_en, data_de_nr, data_fr_nr, data_it_nr, 
                            data_en_nr], axis=1, join='outer')
    else:
        df_all = pd.concat([data_code, data_de, data_fr, data_it, data_en], axis=1, join='outer')
        df_all.fillna("", inplace=True)

    # count the appearances for all languages
    if count_all == "yes":
        print("Count all...")
        df_all["all_nr"] = ""
        df_all.fillna("", inplace=True)
        for k in df_all.index:
            a = "%20or%20"
            url_1 = url_part1 + "ger" + url_part2
            url_all = url_1 + df_all.loc[k, 'de'] + a + df_all.loc[k, 'fr'] + a + df_all.loc[k, 'it'] + a + \
                      df_all.loc[k, 'en']
            if df_all.loc[k, 'de'] == "":
                url_all = url_1 + df_all.loc[k, 'fr'] + a + df_all.loc[k, 'it'] + a + df_all.loc[k, 'en']
                if df_all.loc[k, 'fr'] == "":
                    url_all = url_1 + df_all.loc[k, 'it'] + a + df_all.loc[k, 'en']
                    if df_all.loc[k, 'it'] == "":
                        url_all = url_1 + df_all.loc[k, 'en']
                        if df_all.loc[k, 'en'] == "":
                            print('All languages are empty', k)
            r5 = requests.get(url_all, proxies=proxydict, verify=False)
            tree = etree.fromstring(r5.content)
            df_all.loc[k, 'all_nr'] = tree.find("./summary").attrib["count"]
            r_user = requests.get(url_all, proxies=proxydict, verify=False,
                                  auth=HTTPBasicAuth(geocat_user, geocat_password))
            tree = etree.fromstring(r_user.content)
            df_all.loc[k, 'all_pub_unpub'] = tree.find("./summary").attrib["count"]
            url_all_harvest = url_all + "&_valid=-1"
            r_harvest = requests.get(url_all_harvest, proxies=proxydict, verify=False,
                                     auth=HTTPBasicAuth(geocat_user, geocat_password))
            tree = etree.fromstring(r_harvest.content)
            df_all.loc[k, 'harvested_nr (valid=-1)'] = tree.find("./summary").attrib["count"]

    # save the table
    df_all.to_csv(FileOut, sep=';', encoding='utf-8-sig')
    print("Finished")
    print(FileOut)

else:
    print("ERROR: path of file or not existant - check your input values")
