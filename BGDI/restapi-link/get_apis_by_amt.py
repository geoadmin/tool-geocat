# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This script takes the list of layers from http://api3.geo.admin.ch/api/faq/index.html#which-layers-are-available
            and searches for its uuids (from bmd4mum). It then makes a list of uuids per Bundesamt. This list will be 
            used as input for the addition of the Rest-API-Link (METADATA_SB-143)

Variables:  report_bmd - path and filename of the excel of you BMD4MUM-request
            list_api - path and filename of a excel list, which is copied from 
                       http://api3.geo.admin.ch/api/faq/index.html#which-layers-are-available
            path - path to a folder, where you want to store the csvs of each Bundesamt

Remarks:    ADAPT THE VARIABLES IN THE LINES BELOW
------------------------------------------------------------------------------------------------------------------------
"""
import pandas as pd
import os

# TODO: adapt the following variables
report_bmd = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\BGDI\restapi-link\Report.xlsx"
list_api = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\BGDI\restapi-link\layers_api.xlsx"
path = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\BGDI\restapi-link\Bundesamt"

# ----------------------------------------------------------------------------------------------------------------------

df_api = pd.read_excel(list_api)
df_api['TECHPUBLAYERNAME'] = df_api['layer'].str.split("\(").str[0]
df_api['TECHPUBLAYERNAME'] = df_api['TECHPUBLAYERNAME'].str[:-1]
# print(df_api.head())

df_bmd = pd.read_excel(report_bmd)
df_api["uuid"] = ""

for i in range(len(df_api)):
    print(i)
    layer = df_api["TECHPUBLAYERNAME"].iloc[i]
    a = df_bmd[df_bmd['TECHPUBLAYERNAME'] == layer]
    try:
        uuid = a["GEOCATUUID"].iloc[0]
        df_api["uuid"].iloc[i] = uuid
    except:
        print("EMPTY")
        df_api["uuid"].iloc[i] = "empty"

df_api.to_csv(r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\BGDI\restapi-link\Bundesamt\all.csv", sep=';', encoding="utf-8-sig")

df_api[["A", "org", "B"]] = df_api["TECHPUBLAYERNAME"].str.split('.', 2, expand=True)
org_names = set(df_api['org'].tolist())

for org_name in org_names:
    print(org_name)
    a = df_api.copy()
    a = a.loc[a["org"] == org_name]
    a = a[["TECHPUBLAYERNAME", "uuid"]]
    a.to_csv(os.path.join(path, org_name + ".csv"), sep=';', encoding="utf-8-sig")
