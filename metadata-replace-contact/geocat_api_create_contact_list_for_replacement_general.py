# -*- coding: utf-8 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This script makes the list which will be used in geocat_api_replace_contacts_with_list.py. It looks for all
            MDs, which use a certain mail address and also gets its place (there are three different places
            ("MDContact", "ResourceContact", "DistributorContact")) and its role. In the next script
            (geocat_api_replace_contacts_with_list_general.py), all these appearances of the  contact will be replaced
            with another contact. The script creates 2 csvs. One csv has all contacts that are used in these MDs 
            (all_...). This csv is for an overview and control at the end. The other csv just has the contact you want 
            to replace. This is the one you use in the next script: geocat_api_replace_contacts_with_list_general.py.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            mail_old - the mail that is used for the search in geocat.ch
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.
            path - path to the folder where to save the files.
            filename - general filename. You can keep it like it is or you can change it to a name you like.

Remarks:    ADAPT THE VARIABLES IN THE LINES BELOW
------------------------------------------------------------------------------------------------------------------------
"""
import os.path
import urllib3
import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
import xml.etree.ElementTree as etree
import getpass


# TODO - define inputs
geocat_user = "egs"
mail_old = "info.au@llv.li"
geocat_environment = "INT"  # "INT" or "PROD"
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}
path = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\contacts"
filename = mail_old + "_" + geocat_environment + ".csv"

# -----------------------------------------------------------------------------

# other definitions and general informations
geocat_password = getpass.getpass("Password: ")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
environment = {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
try:
    url_part1 = environment[geocat_environment]
except Exception as error:
    print("Your geocat-environment is wrong. It has to be \"PROD\" or \"INT\"")
    exit()
url_part2 = "/q?from=1&to=1000&any="
parser = etree.XMLParser(encoding="UTF-8")

# find all uuids
url = url_part1 + "ger" + url_part2 + mail_old
print(url)
r_main = requests.get(url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
tree1 = etree.fromstring(r_main.content)
number = tree1.find("./summary").attrib["count"]
print(number)
all_uuids = tree1.findall(".//uuid")
a_list = []

# XML-Categories from geocat.ch
x_char = "{http://www.isotc211.org/2005/gco}CharacterString"
x_org = "{http://www.isotc211.org/2005/gmd}organisationName"
x_mail = "{http://www.isotc211.org/2005/gmd}electronicMailAddress"
x_role = "{http://www.isotc211.org/2005/gmd}CI_RoleCode"
x_con = "{http://www.isotc211.org/2005/gmd}contact"
x_poc = "{http://www.isotc211.org/2005/gmd}pointOfContact"
x_dis = "{http://www.isotc211.org/2005/gmd}distributorContact"

columns = ["uuid", "place", "organisation_old", "mail_old", "role"]
df_first = pd.DataFrame([columns], columns=columns)
df_all = df_first.copy()

# go through each MD seperately and find its contacts
for j in range(len(all_uuids)):
    uuid = all_uuids[j].text
    df1 = df_first.copy()
    print(uuid)
    new_url = url_part1 + "ger/xml.metadata.get?uuid=" + uuid
    r = requests.get(new_url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
    tree = etree.fromstring(r.content)

    try:
        test = tree.findall(".//" + x_con)
        if len(test) == 1:
            org1 = tree.findtext(".//" + x_con + "//" + x_org + "/" + x_char)
            mail1 = tree.findtext(".//" + x_con + "//" + x_mail + "/" + x_char)
            role1 = tree.find(".//" + x_con + "//" + x_role).attrib["codeListValue"]
            df = pd.DataFrame([[uuid, "MDContact", org1, mail1, role1]], columns=columns)
            df1 = df1.append(df, ignore_index=True)

        elif len(test) > 1:
            for key2 in test:
                for key3 in key2.iter():
                    if key3.tag == x_org:
                        for key4 in key3.iter():
                            if key4.tag == x_char:
                                org1 = key4.text
                    if key3.tag == x_mail:
                        for key4 in key3.iter():
                            if key4.tag == x_char:
                                mail1 = key4.text
                    if key3.tag == x_role:
                        role1 = key3.attrib["codeListValue"]
                df = pd.DataFrame([[uuid, "MDContact", org1, mail1, role1]], columns=columns)
                df1 = df1.append(df, ignore_index=True)

        test = tree.findall(".//" + x_poc)
        if len(test) == 1:
            org2 = tree.findtext(".//" + x_poc + "//" + x_org + "/" + x_char)
            mail2 = tree.findtext(".//" + x_poc + "//" + x_mail + "/" + x_char)
            role2 = tree.find(".//" + x_poc + "//" + x_role).attrib["codeListValue"]
            df = pd.DataFrame([[uuid, "ResourceContact", org2, mail2, role2]], columns=columns)
            df1 = df1.append(df, ignore_index=True)
        elif len(test) > 1:
            for key2 in test:
                for key3 in key2.iter():
                    if key3.tag == x_org:
                        for key4 in key3.iter():
                            if key4.tag == x_char:
                                org2 = key4.text
                    if key3.tag == x_mail:
                        for key4 in key3.iter():
                            if key4.tag == x_char:
                                mail2 = key4.text
                    if key3.tag == x_role:
                        role2 = key3.attrib["codeListValue"]
                df = pd.DataFrame([[uuid, "ResourceContact", org2, mail2, role2]], columns=columns)
                df1 = df1.append(df, ignore_index=True)

        test = tree.findall(".//" + x_dis)
        if len(test) == 1:
            org3 = tree.findtext(".//" + x_dis + "//" + x_org + "/" + x_char)
            mail3 = tree.findtext(".//" + x_dis + "//" + x_mail + "/" + x_char)
            role3 = tree.find(".//" + x_dis + "//" + x_role).attrib["codeListValue"]
            df = pd.DataFrame([[uuid, "DistributorContact", org3, mail3, role3]], columns=columns)
            df1 = df1.append(df, ignore_index=True)
        elif len(test) > 1:
            for key2 in test:
                for key3 in key2.iter():
                    if key3.tag == x_org:
                        for key4 in key3.iter():
                            if key4.tag == x_char:
                                org3 = key4.text
                    if key3.tag == x_mail:
                        for key4 in key3.iter():
                            if key4.tag == x_char:
                                mail3 = key4.text
                    if key3.tag == x_role:
                        role3 = key3.attrib["codeListValue"]
                df = pd.DataFrame([[uuid, "DistributorContact", org3, mail3, role3]], columns=columns)
                df1 = df1.append(df, ignore_index=True)
    except:
        pass
        print("---ERROR--- at " + uuid)
    df_all = df_all.append(df1, ignore_index=True)

# save the contacts of each MD to two different CSVs.
df_all = df_all.loc[(df_all["uuid"] != "uuid")]
filename1 = "all_" + filename
print(df_all.shape)
df_all["multiple"] = "no"
test1 = df_all.groupby(["uuid", "place"]).count()
test1 = test1.loc[test1["role"] > 1]
test1.reset_index(inplace=True)
for x in range(len(test1)):
    df_all["multiple"].loc[(df_all["uuid"] == test1["uuid"][x]) & (df_all["place"] == test1["place"][x])] = "yes"
filename1 = r"all_" + filename
df_all.to_csv(os.path.join(path, filename1), sep=';', encoding='utf-8-sig')
df_new = df_all.loc[(df_all["mail_old"] == mail_old)]
print(df_new.shape)
df_new.to_csv(os.path.join(path, filename), sep=';', encoding='utf-8-sig')
