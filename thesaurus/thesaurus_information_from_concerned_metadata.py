# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    get the information of a keyword. Who uses the keyword and in which MD is it used?
            The script makes one list per group that is concerned by some of these keywords... It was created during the
            clean-up of the geocat.ch-Thesaurus in order to contact the organisations with the keywords they use, but
            which are very rarely used

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            File_geocat - This is a csv_count (from thesaurus:rdf_to_csv_count.py), where in an additional column called
                          "replace" is marked "yes" for every keyword that should be included in this script..
            Path_File_out - where to save the csvs, that will be generated in this script
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
import getpass
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# TODO: adapt the following variables
geocat_user = "egs"
File_geocat = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Mots-clés_Schlüsselwörter\bereinigung\geocat_20210726_count_extended.xlsx"
Path_File_out = r"\\v0t0020a.adr.admin.ch\iprod\gdwh-vector\test\TESTING\egs\geocat\Thesaurus\contact_updated"
file_groupowners = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\groups.csv"
geocat_environment = "PROD"
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}

########################################################################################################################


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
geocat = pd.read_excel(File_geocat)
print(geocat.shape)
geocat_1 = geocat[geocat["replace"] == "yes"]
print(geocat_1.shape)
geocat_1.fillna("", inplace=True)
groupowners = pd.read_csv(file_groupowners, sep=';', encoding="ISO-8859-1")
groupowners_2 = groupowners[groupowners["harvested_" + geocat_environment.lower()] == "no"]
print(groupowners.shape)
print(groupowners_2.shape)

for groupnumber in groupowners_2["id_" + geocat_environment.lower()]:
    name = groupowners_2["name"][groupowners_2.index[groupowners_2["id_" + geocat_environment.lower()] == groupnumber][0]]
    print(name)
    o, t_d, t_f, k_d, k_f, u, pp, a_d, a_f = {}, {}, {}, {}, {}, {}, {}, {}, {}
    keynumber = 0
    for keyword in geocat_1["de"]:
        keyword_fr = geocat_1["fr"][geocat_1.index[geocat_1["de"] == keyword][0]]
        url = url_part1 + "ger" + url_part2 + keyword + "%20or%20" + keyword_fr + "&_groupOwner=" + str(int(groupnumber))
        print(url)
        r2 = requests.get(url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
        tree = etree.fromstring(r2.content)
        number = tree.find("./summary").attrib["count"]

        if number == 0:
            pass
        else:
            all_uuids = tree.findall(".//uuid")
            for j in range(len(all_uuids)):
                uuid = all_uuids[j].text
                new_url = url_part1 + "ger/xml.metadata.get?uuid=" + uuid
                r = requests.get(new_url, proxies=proxydict, verify=False)
                if r.status_code == 200:
                    pub = "yes"
                else:
                    r = requests.get(new_url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
                    pub = 'no'
                tree = etree.fromstring(r.content)

                organisation = tree.findtext(x_resp + '/' + x_org + '/' + x_char)
                titles = tree.findall(x_idinf + '/' + x_data_id + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_pttxt + '/' + x_txt + "/" + x_loc)
                titles2 = tree.findall(x_idinf + '/' + x_srv + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_pttxt + '/' + x_txt + "/" + x_loc)
                if len(titles) != 0:
                    for i in range(len(titles)):
                        if [*titles[i].attrib.values()][0] == "#DE":
                            t_d[keynumber] = titles[i].text
                        elif [*titles[i].attrib.values()][0] == "#FR":
                            t_f[keynumber] = titles[i].text
                elif len(titles2) != 0:
                    for i in range(len(titles2)):
                        if [*titles2[i].attrib.values()][0] == "#DE":
                            t_d[keynumber] = titles2[i].text
                        elif [*titles2[i].attrib.values()][0] == "#FR":
                            t_f[keynumber] = titles2[i].text
                else:
                    title = tree.findtext(x_idinf + '/' + x_data_id + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_char)
                    language = tree.findall(x_lan + '/' + x_lanc)
                    if [*language[0].attrib.values()][1] == "ger":
                        t_d[keynumber] = title
                    elif [*language[0].attrib.values()][1] == "fre":
                        t_f[keynumber] = title
                k_d[keynumber] = keyword
                k_f[keynumber] = keyword_fr
                o[keynumber] = organisation
                u[keynumber] = uuid
                pp[keynumber] = pub
                keynumber = keynumber + 1

    if keynumber != 0:
        dk_d = pd.DataFrame.from_dict(k_d, orient='index', columns=['Keyword German'])
        dk_f = pd.DataFrame.from_dict(k_f, orient='index', columns=['Keyword French'])
        do = pd.DataFrame.from_dict(o, orient='index', columns=['Organisation'])
        dt_d = pd.DataFrame.from_dict(t_d, orient='index', columns=['Title German'])
        dt_f = pd.DataFrame.from_dict(t_f, orient='index', columns=['Title French'])
        du = pd.DataFrame.from_dict(u, orient='index', columns=['UUID'])
        dpub = pd.DataFrame.from_dict(pp, orient='index', columns=['Published'])

        df_all = pd.concat([du, dt_d, dt_f, dk_d, dk_f, do, dpub], axis=1, join='outer')
        df_all.set_index("UUID", inplace=True)
        df_all.to_csv(Path_File_out + "\liste_" + name + ".csv", sep=';', encoding="utf-8-sig")
        print(df_all.shape)
    else:
        print("No concerned Metadata in " + name)
