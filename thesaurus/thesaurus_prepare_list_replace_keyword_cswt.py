# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This script looks for all MDs, that use a certain keyword. It creates a list at the end, which is used
            as input for the FME-workbench "CSWT_replace_keywords_series.fmw". In fact, the script looks at the uuids 
            having a keyword and lists them with additional attributes, like the info if the new keyword we want to add 
            is already there.
            This script was created during the cleanup of the geocat.ch-Thesarus in order to replace similar keywords
            that are used often

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            old_keyword_de / _fr - the keyword in german and french, that should be replaced
            new_keyword - the new keyword in all four languages
            new_keyword_type - "geocat" or "gemet", depending on where the new keyword is located
            folder - where to save the csvs, that will be generated in this script
            file_groupowners - path to the file called groupowners.csv. This is a file with informations about the
                               different groups that use geocat (cantons, bundesämter,...). It has fo example the
                               information which group is harvesting and which is editing directly.
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
from requests.auth import HTTPBasicAuth
import os
import getpass


# TODO: adapt the following variables
geocat_user = "egs"
old_keyword_de = "Entwässerungsplan"
old_keyword_fr = "plan de drainage"
new_keyword_de = "Entwässerung"
new_keyword_fr = "drainage"
new_keyword_it = "drenaggio"
new_keyword_en = "drainage"
new_keyword_type = "gemet"
folder = r"\\v0t0020a.adr.admin.ch\iprod\gdwh-vector\test\TESTING\egs\geocat\Thesaurus\CSW_replace_keywords_often_used\csvs"
file_groupowners = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\groups.csv"
geocat_environment = "PROD"  # "INT" or "PROD"
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}

########################################################################################################################

# loads the file with the different groups in order to get the groupnumbers, which are not harvested
groupowners = pd.read_csv(file_groupowners, sep=';', encoding="ISO-8859-1")
group = groupowners[groupowners["harvested_" + geocat_environment.lower()] == "no"]["id_" + geocat_environment.lower()].tolist()
group = [str(int(number)) for number in group]
verbindung = "%20or%20"
groupnumbers = verbindung.join(str(e) for e in group)


# definitions from the geocat-XML
x_key = "{http://www.isotc211.org/2005/gmd}keyword"
x_loc = "{http://www.isotc211.org/2005/gmd}LocalisedCharacterString"
x_char = "{http://www.isotc211.org/2005/gco}CharacterString"
x_ptloc = "{http://www.isotc211.org/2005/gmd}PT_Locale"
x_lan = "{http://www.isotc211.org/2005/gmd}language"
x_lanc = "{http://www.isotc211.org/2005/gmd}LanguageCode"


# other definitions and general informations
geocat_password = getpass.getpass("Password: ")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
environment = {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
try:
    url_part1 = environment[geocat_environment]
except Exception as error:
    print("Your geocat-environment is wrong. It has to be \"PROD\" or \"INT\"")
    exit()
url_part2 = "/q?from=1&to=1000&keyword="


# gets all uuids, which use the selected keyword
url = url_part1 + "ger" + url_part2 + old_keyword_de + "%20or%20" + old_keyword_fr + "&_groupOwner=" + groupnumbers
print(url)
r1 = requests.get(url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
tree = etree.fromstring(r1.content)
all_uuids = tree.findall(".//uuid")
dict_uuid, dict_keywords, dict_new_keyword, dict_languages, dict_languages_count = {}, {}, {}, {}, {}

# does the loop for every single uuid, where it is collecting the information of the MD
for j in range(len(all_uuids)):
    # gets the xml of the uuid
    uuid = all_uuids[j].text
    dict_uuid[j] = uuid
    print(uuid)
    new_url = url_part1 + "ger/xml.metadata.get?uuid=" + uuid
    r2 = requests.get(new_url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
    tree = etree.fromstring(r2.content)

    try:
        # get the language information
        lang1 = tree.findall(".//" + x_ptloc)
        languages = []
        if lang1:
            for lang2 in lang1:
                languages.append(lang2.attrib["id"])
        else:
            lang3 = tree.findall(x_lan + "/" + x_lanc)[0].attrib["codeListValue"]
            languages = [lang3]
        languages = [x for x in languages if x is not None]
        dict_languages[j] = str(languages)
        if len(languages) >= 2:
            dict_languages_count[j] = "multiple"
        elif len(languages) == 1:
            dict_languages_count[j] = languages[0]
        else:
            dict_languages_count[j] = "special_case"

        # get the keyword information
        key1 = tree.findall(".//" + x_key)
        keywords = []
        for key2 in key1:
            for key3 in key2.iter():
                if key3.tag == x_loc:
                    keywords.append(key3.text)
        if not keywords:
            for key2 in key1:
                for key3 in key2.iter():
                    if key3.tag == x_char:
                        keywords.append(key3.text)
        keywords = [x for x in keywords if x is not None]
        if new_keyword_de in keywords:
            dict_new_keyword[j] = "yes"
        elif new_keyword_fr in keywords:
            dict_new_keyword[j] = "yes"
        else:
            dict_new_keyword[j] = "no"
        dict_keywords[j] = str(keywords)
    except Exception as error:
        pass
        print("ERROR at ", uuid)
        print(error)

# creates a nice table and saves it in the folder
da = pd.DataFrame.from_dict(dict_uuid, orient='index', columns=['uuid'])
db = pd.DataFrame.from_dict(dict_keywords, orient='index', columns=['keywords'])
dc = pd.DataFrame.from_dict(dict_new_keyword, orient='index', columns=['new_kw_present'])
dd = pd.DataFrame.from_dict(dict_languages, orient='index', columns=['languages'])
de = pd.DataFrame.from_dict(dict_languages_count, orient='index', columns=['multiple_languages'])
df_all = pd.concat([da, db, dc, dd, de], axis=1, join='outer')
df_all["type"] = new_keyword_type
df_all["new_kw_de"] = new_keyword_de
df_all["new_kw_fr"] = new_keyword_fr
df_all["new_kw_en"] = new_keyword_en
df_all["new_kw_it"] = new_keyword_it
df_all.to_csv(os.path.join(folder, old_keyword_de + "_" + new_keyword_de + "_" + new_keyword_type + "_" + geocat_environment + ".csv"), sep=';', encoding="utf-8-sig")
