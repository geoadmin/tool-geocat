# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    get a list of MDs from geocat which correspond to certain criterias, which you can define in the variables.
            You can also define, which attributes you want to have in the list. Check the variables.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            file_out - name and path of the csv, you want to generate
            searching_keywords - keywords you are looking for in a list. Leave list empty if keywords are not important
                                 in your request. ex. ["opedata.swiss", "BGDI"]
            searching_any - words you are looking for in a list (same as you would type in the geocat.ch-search). Leave
                            list empty if keywords are not important in your request
            searching_group - list of groups (numbers in quotationmarks: ["24", "6"]) you are looking for. Leave list
                              empty if keywords are not important in your request
            harvested - "" or "no" or "yes"
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            number_of_MDs - "all" or a number between quotationmarks (ex. "10" or "50"). So it takes either the
                            information of all found MDs or just of the first 10, 50, ...
            attributes - you can define what you want to get in the list. The possibilities are: title, languages, 
                         extents, formats, keywords and contacts. UUIDs are always saved, even if there are no more 
                         parameters. Ex: ["title", "contacts"]
                         Possible are: ["title", "languages", "extents", "formats", "keywords", "contacts"]
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.
                         
Remarks:    ADAPT THE VARIABLES IN THE LINES BELOW
------------------------------------------------------------------------------------------------------------------------
"""
import xml.etree.ElementTree as etree
import pandas as pd
import requests
import urllib3
from requests.auth import HTTPBasicAuth
import getpass


# TODO: adapt the following variables
geocat_user = ""
file_out = r""
searching_keywords = ["BGDI Bundesgeodaten-Infrastruktur"]
searching_any = []
searching_group = []
harvested = "no"
geocat_environment = "PROD"
number_of_MDs = "1000"
attributes = ["title", "contacts"]
proxydict = {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}

########################################################################################################################
# definition of functions, which are used several times in the script
########################################################################################################################

def find_contacts(org, mail, role, fname, lname):
    con_list, mail_list = [], []
    if len(org) == len(mail):
        for xy in range(len(org)):
            if mail[xy].text == None:
                a_mail = "None"
            else:
                a_mail = mail[xy].text
            if role[xy].attrib["codeListValue"] == None:
                a_role = "None"
            else:
                a_role = role[xy].attrib["codeListValue"]
            con_list.append(org[xy].text + " (" + a_mail + ", " + a_role + ")")
        return str(con_list)[1:-1]
    elif (len(org) == 1) & (len(mail) > 1):
        for xy in range(len(mail)):
            if mail[xy].text == None:
                a_mail = "None"
            else:
                a_mail = mail[xy].text
            mail_list.append(a_mail)
        if role[0].attrib["codeListValue"] == None:
            a_role = "None"
        else:
            a_role = role[0].attrib["codeListValue"]  
        con_list.append(org[0].text + " (" + str(mail_list) + ", " + a_role + ")")
        return str(con_list)[1:-1]
    elif (len(org) == 0) & (len(mail) != 0):
        for xy in range(len(mail)):
            if mail[xy].text == None:
                a_mail = "None"
            else:
                a_mail = mail[xy].text
            if role[xy].attrib["codeListValue"] == None:
                a_role = "None"
            else:
                a_role = role[xy].attrib["codeListValue"]
            if fname[xy].text == None:
                a_fname = "None"
            else:
                a_fname = fname[xy].text
            if lname[xy].text == None:
                a_lname = "None"
            else:
                a_lname = lname[xy].text
            con_list.append(a_fname + " " + a_lname + " (" + a_mail + ", " + a_role + ")")
        return str(con_list)[1:-1]
    elif (len(org) == 1) & (len(mail) == 0):
        if role[0].attrib["codeListValue"] == None:
            a_role = "None"
        else:
            a_role = role[0].attrib["codeListValue"]
        con_list.append(org[0].text + " ( - , " + a_role + ")")
        return str(con_list)[1:-1]
    else:
        return "Not the same number of OrganisationNames and MailAdresses. " \
               "There are either contacts without MailAdresses or contacts without OrganisationNames"


def get_titles(findall_xpath):
    tit_get, tit_fre = "", ""
    for k in range(len(findall_xpath)):
        if [*findall_xpath[k].attrib.values()][0] == "#DE":
            tit_ger = findall_xpath[k].text
        if [*findall_xpath[k].attrib.values()][0] == "#FR":
            tit_fre = findall_xpath[k].text
    return tit_ger, tit_fre
    
########################################################################################################################

# check your input
all_possible_attributes = ["title", "languages", "extents", "formats", "keywords", "contacts"]
result =  all(elem in all_possible_attributes for elem in attributes)
if result:
    print("all selected attributes are valid")    
else:
    print("check you attributes. Possible are: " + str(all_possible_attributes))
    exit()

# create the search query (which will be a part of the url)
geocat_password = getpass.getpass("Password: ")
groupnumbers, keywords, anys, url_part1, url_harv = "", "", "", "", ""
if searching_group:
    verbindung = "%20or%20"
    groupnumbers = "&_groupOwner=" + verbindung.join(str(e) for e in searching_group)
if searching_keywords:
    verbindung = "%20or%20"
    keywords = "&keyword=" + verbindung.join(str(e) for e in searching_keywords)
if searching_any:
    verbindung = "%20or%20"
    anys = "&any=" + verbindung.join(str(e) for e in searching_any)
if harvested == "yes":
    url_harv = "&facet.q=isHarvested%2Fy"
elif harvested == "no":
    url_harv = "&facet.q=isHarvested%2Fn"


# define the url
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
environment = {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
try:
    url_part1 = environment[geocat_environment]
except Exception as error:
    print("Your geocat-environment is wrong. It has to be \"PROD\" or \"INT\"")
    exit()
parser = etree.XMLParser(encoding='UTF-8')
url = url_part1 + "ger/q?from=1&to=2000" + keywords + anys + groupnumbers + url_harv
print(url)


# XML-Categories from geocat.ch
x_start = "{http://www.geocat.ch/2008/che}CHE_MD_Metadata"
x_char = "{http://www.isotc211.org/2005/gco}CharacterString"
x_form = "{http://www.isotc211.org/2005/gmd}MD_Format"
x_name = "{http://www.isotc211.org/2005/gmd}name"
x_vers = "{http://www.isotc211.org/2005/gmd}version"
x_org = "{http://www.isotc211.org/2005/gmd}organisationName"
x_fname = "{http://www.geocat.ch/2008/che}individualFirstName"
x_lname = "{http://www.geocat.ch/2008/che}individualLastName"
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
x_srv1 = "{http://www.geocat.ch/2008/che}CHE_SV_ServiceIdentification"
x_srv2 = "{http://www.isotc211.org/2005/srv}SV_ServiceIdentification"
x_kws = "{http://www.isotc211.org/2005/gmd}MD_Keywords"
x_kwd = "{http://www.isotc211.org/2005/gmd}keyword"
x_ext = "{http://www.isotc211.org/2005/gmd}EX_Extent"
x_ptloc = "{http://www.isotc211.org/2005/gmd}PT_Locale"
x_mail = "{http://www.isotc211.org/2005/gmd}electronicMailAddress"
x_role = "{http://www.isotc211.org/2005/gmd}CI_RoleCode"
x_mdcon = "{http://www.isotc211.org/2005/gmd}contact"
x_rescon = "{http://www.isotc211.org/2005/gmd}pointOfContact"
x_discon = "{http://www.isotc211.org/2005/gmd}distributorContact"
x_desc = "{http://www.isotc211.org/2005/gmd}description"

# access the url and count the number of MDs corresponding to your search
r_main = requests.get(url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
tree = etree.fromstring(r_main.content)
number = tree.find("./summary").attrib["count"]
print("Number of MDs corresponding to your search: " + number)
t_d, t_f, k_d, k_f, u, c1, c2, c3, e, f, g = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}
lang_dict = {"ger": "DE", "fre": "FR", "eng": "EN", "ita": "IT"}

if number_of_MDs == "all":
    number_info = int(number)
elif int(number_of_MDs) > int(number):
    number_info = int(number)
else:
    number_info = int(number_of_MDs)


# check if there are any results
if int(number) != 0:
    # get all uuids corresponding to your search
    all_uuids = tree.findall(".//uuid")
    
    # get all the information for every single uuid
    for i in range(number_info):
        a1, a2 = "", ""
        contacts, languages, extents, formats1, formats2, all_keywords, all_keywords_fr = [], [], [], [], [], [], []
        print(i)
        uuid = all_uuids[i].text
        u[i] = uuid
        if attributes != []:
            new_url = url_part1 + "ger/xml.metadata.get?uuid=" + uuid
            r = requests.get(new_url, proxies=proxydict, verify=False, auth=HTTPBasicAuth(geocat_user, geocat_password))
            tree = etree.fromstring(r.content)
            try:
                if "title" in attributes:
                    titles = tree.findall(x_idinf + '/' + x_data_id + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_pttxt + '/' + x_txt + "/" + x_loc)
                    titles2 = tree.findall(x_idinf + '/' + x_srv1 + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_pttxt + '/' + x_txt + "/" + x_loc)
                    titles3 = tree.findall(x_idinf + '/' + x_srv2 + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_pttxt + '/' + x_txt + "/" + x_loc)
                    if len(titles) != 0:
                        a1, a2 = get_titles(titles)
                    elif len(titles2) != 0:
                        a1, a2 = get_titles(titles2)
                    elif len(titles3) != 0:
                        a1, a2 = get_titles(titles3)
                    else:
                        title = tree.findtext(x_idinf + '/' + x_data_id + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_char)
                        if title == None:
                            title = tree.findtext(x_idinf + '/' + x_srv1 + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_char)
                            if title == None:
                                title = tree.findtext(x_idinf + '/' + x_srv2 + '/' + x_cit + '/' + x_cicit + '/' + x_tit + '/' + x_char)
                        language = tree.findall(x_lan + '/' + x_lanc)
                        if [*language[0].attrib.values()][1] == "ger":
                            a1 = title
                        if [*language[0].attrib.values()][1] == "fre":
                            a2 = title                      
                    t_d[i] = a1
                    t_f[i] = a2
                    
                if "languages" in attributes:
                    lang1 = tree.findall(".//" + x_ptloc)
                    if lang1:
                        for lang2 in lang1:
                            languages.append(lang2.attrib["id"])
                    else:
                        lang3 = tree.findall(x_lan + "/" + x_lanc)[0].attrib["codeListValue"]
                        languages = [lang_dict[lang3]]
                    languages = [x for x in languages if x is not None]
                    g[i] = str(languages)[1:-1]
                    
                if "extents" in attributes:
                    ext1 = tree.findall(".//" + x_ext + "/" + x_desc + "/" + x_char)
                    for xyz in range(len(ext1)):
                        extents.append(ext1[xyz].text)
                    e[i] = str(extents)[1:-1]
                    
                if "formats" in attributes:
                    form1 = tree.findall(".//" + x_form + "//" + x_char)
                    for xy in range(len(form1)):
                        formats1.append(form1[xy].text)
                    formats1 = [k for k in formats1 if k is not None]
                    for x, y in zip(formats1[0::2], formats1[1::2]):
                        formats2.append(x + ' (' + y + ')')
                    f[i] = str(formats2)[1:-1]
                    
                if "keywords" in attributes:
                    keywords = tree.findall(".//" + x_kws + "/" + x_kwd + "//" + x_loc)
                    keywords2 = tree.findall(".//" + x_kws + "/" + x_kwd + "/" + x_char)
                    for j in range(len(keywords)):
                        if [*keywords[j].attrib.values()][0] == "#DE":
                            all_keywords.append(keywords[j].text)
                        if [*keywords[j].attrib.values()][0] == "#FR":
                            all_keywords_fr.append(keywords[j].text)
                    if not all_keywords:
                        for j in range(len(keywords2)):
                            all_keywords.append(keywords2[j].text)
                    if not all_keywords_fr:
                        for j in range(len(keywords2)):
                            all_keywords_fr.append(keywords2[j].text)
                    all_keywords = [k for k in all_keywords if k is not None]
                    all_keywords_fr = [k for k in all_keywords_fr if k is not None]
                    k_d[i] = ', '.join(all_keywords)
                    k_f[i] = ', '.join(all_keywords_fr)

                if "contacts" in attributes:
                    x_datacon = "{http://www.isotc211.org/2005/gmd}pointOfContact"
                    x_discon = "{http://www.isotc211.org/2005/gmd}distributorContact"
                    mdorg = tree.findall("./" + x_mdcon + "//" + x_org + "/" + x_char)
                    mdfname = tree.findall("./" + x_mdcon + "//" + x_fname + "/" + x_char)
                    mdlname = tree.findall("./" + x_mdcon + "//" + x_lname + "/" + x_char)
                    mdmail = tree.findall("./" + x_mdcon + "//" + x_mail + "/" + x_char)
                    mdrole = tree.findall("./" + x_mdcon + "//" + x_role)
                    resorg = tree.findall(".//" + x_rescon + "//" + x_org + "/" + x_char)
                    resfname = tree.findall(".//" + x_rescon + "//" + x_fname + "/" + x_char)
                    reslname = tree.findall(".//" + x_rescon + "//" + x_lname + "/" + x_char)
                    resmail = tree.findall(".//" + x_rescon + "//" + x_mail + "/" + x_char)
                    resrole = tree.findall(".//" + x_rescon + "//" + x_role)
                    disorg = tree.findall(".//" + x_discon + "//" + x_org + "/" + x_char)
                    disfname = tree.findall(".//" + x_discon + "//" + x_fname + "/" + x_char)
                    dislname = tree.findall(".//" + x_discon + "//" + x_lname + "/" + x_char)
                    dismail = tree.findall(".//" + x_discon + "//" + x_mail + "/" + x_char)
                    disrole = tree.findall(".//" + x_discon + "//" + x_role)
                    
                    c1[i] = find_contacts(mdorg, mdmail, mdrole, mdfname, mdlname)
                    c2[i] = find_contacts(resorg, resmail, resrole, resfname, reslname)
                    c3[i] = find_contacts(disorg, dismail, disrole, disfname, dislname)
                    

            except Exception as error:
                print("ERROR: " + uuid)
                pass

    # save to csv
    du = pd.DataFrame.from_dict(u, orient='index', columns=['UUID'])
    df_all = du.copy()    
    if "title" in attributes:
        dt_d = pd.DataFrame.from_dict(t_d, orient='index', columns=['Title (DE)'])
        dt_f = pd.DataFrame.from_dict(t_f, orient='index', columns=['Title (FR)'])
        df_all = pd.concat([df_all, dt_d, dt_f], axis=1, join='outer')
    if "languages" in attributes:    
        dg = pd.DataFrame.from_dict(g, orient='index', columns=['languages'])
        df_all = pd.concat([df_all, dg], axis=1, join='outer')
    if "extents" in attributes:
        de = pd.DataFrame.from_dict(e, orient='index', columns=['extent'])   
        df_all = pd.concat([df_all, de], axis=1, join='outer')
    if "formats" in attributes:
        df = pd.DataFrame.from_dict(f, orient='index', columns=['formats'])
        df_all = pd.concat([df_all, df], axis=1, join='outer')
    if "keywords" in attributes:
        dk_d = pd.DataFrame.from_dict(k_d, orient='index', columns=['Keywords (DE)'])
        dk_f = pd.DataFrame.from_dict(k_f, orient='index', columns=['Keywords (FR)'])
        df_all = pd.concat([df_all, dk_d, dk_f], axis=1, join='outer')
    if "contacts" in attributes:
        dc1 = pd.DataFrame.from_dict(c1, orient='index', columns=['Metadata contacts (mail, role)'])    
        dc2 = pd.DataFrame.from_dict(c2, orient='index', columns=['Resource contacts (mail, role)'])    
        dc3 = pd.DataFrame.from_dict(c3, orient='index', columns=['Distribution contacts (mail, role)'])    
        df_all = pd.concat([df_all, dc1, dc2, dc3], axis=1, join='outer')    
    df_all.to_csv(file_out, sep=';', encoding="utf-8-sig")
    print("File saved: " + file_out)

else:
    print("There are no MDs corresponding to your search. No file was written.")
