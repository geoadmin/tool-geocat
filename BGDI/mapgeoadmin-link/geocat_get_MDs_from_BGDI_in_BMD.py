# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    check whether "BGDI" exists as keyword in the MDs from the list from BMD.
            This list from BMD should contain all BGDI-Datasets.
            Then get all the necessairy information from geocat to these MDs, as uuid, keywords,...
            This was made for the Ticket METADATA_SB-151. No MDs are modified here.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            file_bmd4mum - Excelfile from search-request on BMD4MUM
            Path_File_out - where to save the csvs, that will be generated in this script
            file_groupowners - path to the file called groupowners.csv. This is a file with informations about the
                               different groups that use geocat (cantons, bundesämter,...). In this script, it is
                               a special csv, where just the infos from groups with BGDI are present.
            geocat_environment - "INT" or "PROD"
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
import getpass

# TODO: adapt the following variables
geocat_user = "egs"
file_bmd4mum = r"\\v0t0020a.adr.admin.ch\iprod\gdwh-vector\test\TESTING\egs\geocat\BGDI\Report_20210603.xlsx"
Path_File_out = r"\\v0t0020a.adr.admin.ch\iprod\gdwh-vector\test\TESTING\egs\geocat\BGDI\test.csv"
file_groupowners = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\BGDI\groups_BGDI.csv"
geocat_environment = "INT"  # "INT" or "PROD"
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


# other definitions and general informations
geocat_password = getpass.getpass("Password: ")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
environment = {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
try:
    url_part1 = environment[geocat_environment]
except Exception as error:
    print("Your geocat-environment is wrong. It has to be \"PROD\" or \"INT\"")
    exit()


# read excel from BMD
bmd_list = pd.read_excel(file_bmd4mum)
print(bmd_list.shape)
bmd_list = bmd_list.drop_duplicates(subset=['TECHPUBLAYERNAME', 'GDSKEY', 'GEOCATUUID'], keep='last')
print(bmd_list.shape)
t_d, k_d, o, u, pp, tech, gds, rem, a, b, c, d, e, f = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

# go through every line in the BMD-Excel and collect its corresponding information
print("BMD-Liste durchgehen")
for i in range(len(bmd_list)):
    print(i)
    uuid = bmd_list.iloc[i]["GEOCATUUID"]
    if isinstance(uuid, str):
        # get the XML of the uuid
        new_url = url_part1 + "ger/xml.metadata.get?uuid=" + uuid
        r = requests.get(new_url, proxies=proxydict, verify=False)
        if r.status_code == 200:
            pub = "yes"
        else:
            r = requests.get(new_url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
            pub = 'no'
            if r.status_code != 200:
                pub = "No vaild uuid"

        try:
            # read the XML and save the info
            tree = etree.fromstring(r.content)
            all_keywords = []
            organisation = tree.findtext(x_resp + '/' + x_org + '/' + x_char)
            titles = tree.findall(x_idinf + '/' + x_data_id + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_pttxt + '/' + x_txt + "/" + x_loc)
            titles2 = tree.findall(x_idinf + '/' + x_srv + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_pttxt + '/' + x_txt + "/" + x_loc)
            keywords = tree.findall(".//" + x_kws + "//" + x_loc)
            for j in range(len(keywords)):
                if [*keywords[j].attrib.values()][0] == "#DE":
                    all_keywords.append(keywords[j].text)
            if len(titles) != 0:
                for k in range(len(titles)):
                    if [*titles[k].attrib.values()][0] == "#DE":
                        t_d[i] = titles[k].text
            elif len(titles2) != 0:
                for k in range(len(titles2)):
                    if [*titles2[k].attrib.values()][0] == "#DE":
                        t_d[i] = titles2[k].text
            else:
                title = tree.findtext(x_idinf + '/' + x_data_id + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_char)
                language = tree.findall(x_lan + '/' + x_lanc)
                if [*language[0].attrib.values()][1] == "ger":
                    t_d[i] = title
            k_d[i] = ', '.join(all_keywords)
            o[i] = organisation
            u[i] = uuid
            pp[i] = pub
            tech[i] = bmd_list.iloc[i]["TECHPUBLAYERNAME"]
            gds[i] = bmd_list.iloc[i]["GDSKEY"]
            rem[i] = bmd_list.iloc[i]["REMARKS"]
            a[i] = bmd_list.iloc[i]["HASWMTSSERVICE"]
            b[i] = bmd_list.iloc[i]["HASWMSSERVICE"]
            c[i] = bmd_list.iloc[i]["HASFREEWMSSERVICE"]
            d[i] = bmd_list.iloc[i]["HASRAWPACKAGESERVICE"]
            e[i] = bmd_list.iloc[i]["ISPUBLISHEDINAPI"]
            f[i] = bmd_list.iloc[i]["ISPUBLISHEDINONLINEVIEWER"]
        except:
            print("--- mistake at " + str(i))
            print("--- uuid = " + uuid)
            print("--- " + bmd_list.iloc[i]["TECHPUBLAYERNAME"])
            pass
    else:
        uuid = "No UUID in BMD4MUM"
        u[i] = uuid
        tech[i] = bmd_list.iloc[i]["TECHPUBLAYERNAME"]
        gds[i] = bmd_list.iloc[i]["GDSKEY"]
        rem[i] = bmd_list.iloc[i]["REMARKS"]
        a[i] = bmd_list.iloc[i]["HASWMTSSERVICE"]
        b[i] = bmd_list.iloc[i]["HASWMSSERVICE"]
        c[i] = bmd_list.iloc[i]["HASFREEWMSSERVICE"]
        d[i] = bmd_list.iloc[i]["HASRAWPACKAGESERVICE"]
        e[i] = bmd_list.iloc[i]["ISPUBLISHEDINAPI"]
        f[i] = bmd_list.iloc[i]["ISPUBLISHEDINONLINEVIEWER"]

# put all collected information in a nice table
dk_d = pd.DataFrame.from_dict(k_d, orient='index', columns=['Keywords'])
do = pd.DataFrame.from_dict(o, orient='index', columns=['Organisation Geocat'])
dt_d = pd.DataFrame.from_dict(t_d, orient='index', columns=['Title Geocat'])
du = pd.DataFrame.from_dict(u, orient='index', columns=['UUID'])
dpub = pd.DataFrame.from_dict(pp, orient='index', columns=['Published Geocat'])
dtech = pd.DataFrame.from_dict(tech, orient='index', columns=['TECHPUBLAYER'])
dgds = pd.DataFrame.from_dict(gds, orient='index', columns=['GDSKEY'])
drem = pd.DataFrame.from_dict(rem, orient='index', columns=['REMARKS'])
da = pd.DataFrame.from_dict(a, orient='index', columns=['HASWMTSSERVICE'])
db = pd.DataFrame.from_dict(b, orient='index', columns=['HASWMSSERVICE'])
dc = pd.DataFrame.from_dict(c, orient='index', columns=['HASFREEWMSSERVICE'])
dd = pd.DataFrame.from_dict(d, orient='index', columns=['HASRAWPACKAGESERVICE'])
de = pd.DataFrame.from_dict(e, orient='index', columns=['ISPUBLISHEDINAPI'])
df = pd.DataFrame.from_dict(f, orient='index', columns=['ISPUBLISHEDINONLINEVIEWER'])
df_all = pd.concat([du, dt_d, dk_d, do, dpub, dtech, dgds, drem, da, db, dc, dd, de, df], axis=1, join='outer')
df_all["Keyword BGDI"] = "test"
df_all['Keyword BGDI'] = np.where(df_all.Keywords.str.contains('BGDI', regex=False), "yes", "no")


# define which uuids correspond to which Bundesamt
print("Bundesämter definieren")
groupowners = pd.read_csv(file_groupowners, sep=';', encoding="ISO-8859-1")
groupowners.dropna(subset=["id_" + geocat_environment.lower()], inplace=True)
df_all["Bundesamt Geocat"] = "not known"
for groupnumber in groupowners["id_" + geocat_environment.lower()]:
    name = groupowners["name"][groupowners.index[groupowners["id_" + geocat_environment.lower()] == groupnumber][0]]
    print(name)
    url = "https://www.geocat.ch/geonetwork/srv/ger/q?from=1&to=1500&_groupOwner=" + str(int(groupnumber))
    r = requests.get(url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
    tree = etree.fromstring(r.content)
    all_uuids = tree.findall(".//uuid")
    
    for j in range(len(all_uuids)):
        #print(all_uuids[j].text)
        if df_all["UUID"].str.contains(all_uuids[j].text).any():
            df_all.loc[df_all['UUID'] == all_uuids[j].text, 'Bundesamt Geocat'] = name
    
# rename the columns and save the table as a csv
df_all = df_all[['UUID', 'Title Geocat', 'Keywords', 'Keyword BGDI', 'Bundesamt Geocat', 'Organisation Geocat', 'Published Geocat', 'TECHPUBLAYER', 'GDSKEY', 'REMARKS', 'HASWMTSSERVICE', 'HASWMSSERVICE', 'HASFREEWMSSERVICE', 'HASRAWPACKAGESERVICE', 'ISPUBLISHEDINAPI', 'ISPUBLISHEDINONLINEVIEWER']]
df_all = df_all.rename({'Keywords': 'All Keywords Geocat'}, axis=1)
df_all.to_csv(Path_File_out, sep=';', encoding="utf-8-sig")
print(df_all.shape)
