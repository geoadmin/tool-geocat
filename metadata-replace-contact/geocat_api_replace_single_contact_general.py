# -*- coding: utf-8 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This script replaces a designated contact in a specific MD (uuid) with another contact. It first deletes the
            designated contact if you want to, then puts a new contact in there and relinks it with the reusable object,
            that represents the contact.
            You have to give it some information.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            uuid - the uuid of the MD you want to modify
            place - there are three possible places for a contact: "MDContact", "ResourceContact", "DistributorContact"
            role - the role the new contact should have. ex. resourceProvider,...
            orgname - The name of the organisation of the new contact
            mail - the email of the new contact
            posname - the positionname of the new contact
            first_name - the first name of the new contact
            last_name - the last name of the new contact
            delete - "yes" or "no - it deletes (all) the contacts that are present at the designated place (above)
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.

Remarks:    ADAPT THE VARIABLES IN THE LINES BELOW
------------------------------------------------------------------------------------------------------------------------
"""
import urllib3
import requests
from requests.auth import HTTPBasicAuth
import json
import xml.etree.ElementTree as etree
import getpass


# TODO - define inputs
geocat_user = ""
uuid = ""
place = ""  # "MDContact", "ResourceContact", "DistributorContact"
role = ""  # "resourceProvider", "pointOfContact", "distributor", ...
orgname = ""
mail = ""
posname = ""
first_name = ""
last_name = ""
delete = "yes"
geocat_environment = "INT"  # "INT" or "PROD"
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}

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
parser = etree.XMLParser(encoding="UTF-8")


# Get cookies and token
print("get cookies")
a_session = requests.Session()
a_session.post(url_part1 + "eng/info?type=me", proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
session_cookies = a_session.cookies.get_dict()
token = session_cookies["XSRF-TOKEN"]
print("TOKEN: ", token)

# define the inputs (body) for the API
part_firstname, part_lastname, part_posname = "", "", ""
if first_name != "":
    part_firstname = '<che:individualFirstName><gco:CharacterString>' + first_name + '</gco:CharacterString></che:individualFirstName>'
if last_name != "":
    part_lastname = '<che:individualLastName><gco:CharacterString>' + last_name + '</gco:CharacterString></che:individualLastName>'
if posname != "":
    part_posname = '<gmd:positionName><gco:CharacterString>' + posname + '</gco:CharacterString></gmd:positionName>'

part_orgname = '<gmd:organisationName><gco:CharacterString>' + orgname + '</gco:CharacterString></gmd:organisationName>'
part_mail = '<gmd:contactInfo><gmd:CI_Contact><gmd:address><che:CHE_CI_Address gco:isoType=\"gmd:CI_Address\"><gmd:electronicMailAddress><gco:CharacterString>' + mail + '</gco:CharacterString></gmd:electronicMailAddress></che:CHE_CI_Address></gmd:address></gmd:CI_Contact></gmd:contactInfo>'
part_role = '<gmd:role><gmd:CI_RoleCode codeList=\"http://www.isotc211.org/2005/resources/codeList.xml#CI_RoleCode\" codeListValue=\"' + role + '\"/></gmd:role>'
main_part = '<che:CHE_CI_ResponsibleParty gco:isoType=\"gmd:CI_ResponsibleParty\">' + part_orgname + part_posname + part_mail + part_role + part_firstname + part_lastname + '</che:CHE_CI_ResponsibleParty>'
namespaces = 'xmlns:che=\"http://www.geocat.ch/2008/che\" xmlns:gco=\"http://www.isotc211.org/2005/gco\" xmlns:gmd=\"http://www.isotc211.org/2005/gmd\" xmlns:srv=\"http://www.isotc211.org/2005/srv\" xmlns:gmx=\"http://www.isotc211.org/2005/gmx\" xmlns:gts=\"http://www.isotc211.org/2005/gts\" xmlns:gsr=\"http://www.isotc211.org/2005/gsr\" xmlns:gmi=\"http://www.isotc211.org/2005/gmi\" xmlns:gml=\"http://www.opengis.net/gml/3.2\"'

if place == "ResourceContact":
    json_del = {"value": "<gn_delete></gn_delete>", "xpath": "gmd:identificationInfo/che:CHE_MD_DataIdentification/gmd:pointOfContact"}
    value_add = '<gn_add><gmd:pointOfContact ' + namespaces + '>' + main_part + '</gmd:pointOfContact></gn_add>'
    xpath_add = "/che:CHE_MD_Metadata/gmd:identificationInfo/che:CHE_MD_DataIdentification[1]"

elif place == "DistributorContact":
    json_del = {"value": "<gn_delete></gn_delete>", "xpath": "gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor"}
    value_add = '<gn_add><gmd:distributor ' + namespaces + '><gmd:MD_Distributor xmlns:gmd=\"http://www.isotc211.org/2005/gmd\"><gmd:distributorContact xmlns:gmd=\"http://www.isotc211.org/2005/gmd\">' + main_part + '</gmd:distributorContact></gmd:MD_Distributor></gmd:distributor></gn_add>'
    xpath_add = "/che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution[1]"

elif place == "MDContact":
    json_del = {"value": "<gn_delete></gn_delete>", "xpath": "gmd:contact"}
    value_add = '<gn_add><gmd:contact ' + namespaces + '>' + main_part + '</gmd:contact></gn_add>'
    xpath_add = "/"
    

# Batch delete
if delete == "yes":
    print("batchediting - delete")
    headers_del = {"accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": token}
    payload_del = r"[" + json.dumps(json_del) + "]"
    url_del = url_part1 + "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=false"
    print(payload_del)
    r_del = a_session.put(url_del, data=payload_del, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers_del, cookies=session_cookies)
    print(r_del.status_code)
    if r_del.status_code > 205:
        print("--- ERROR ---")
        print(r_del.content)
 

# Batch add contact
print("batchediting - add")
headers_add = {"accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": token}
json_add = {"value": value_add, "xpath": xpath_add}
payload_add = r"[" + json.dumps(json_add) + "]"
url_add = url_part1 + "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=false"
r_add = a_session.put(url_add, data=payload_add, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers_add, cookies=session_cookies)
print(r_add.status_code)
r_add_answer = r_add.content
print(r_add.content)


# processRecordSubtemplates - needed for RO
print("processRecordSubtemplates")
headers_sub = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": token}
url_sub = url_part1 + "api/0.1/records/" + uuid + "/processRecordSubtemplates"
r_sub = a_session.post(url_sub, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers_sub, cookies=session_cookies)
print(r_sub.status_code)
print(r_sub.content)


# processes/empty - needed for RO
print("processes/empty")
headers_pro = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": token}
url_pro = url_part1 + "api/0.1/records/" + uuid + "/processes/empty"
r_pro = a_session.post(url_pro, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password), headers=headers_pro, cookies=session_cookies)
print(r_pro.status_code)
print(r_pro.content)
