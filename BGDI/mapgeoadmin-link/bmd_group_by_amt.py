# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This script divides the output of a BMD4MUM search into Bundesämter. So you have a csv pro Bundesamt.

Variables:  path_file - path and filename of the excel of you BMD4MUM-request
            path - path to a folder, where you want to store the csvs of each Amt

Remarks:    ADAPT THE VARIABLES IN THE LINES BELOW
------------------------------------------------------------------------------------------------------------------------
"""
import pandas as pd
import os

# TODO: adapt the following variables
path_file = r"\\v0t0020a.adr.admin.ch\iprod\gdwh-vector\test\TESTING\egs\geocat\BGDI\Report_20210817.xlsx"
path = r"\\v0t0020a.adr.admin.ch\iprod\gdwh-vector\test\TESTING\egs\geocat\BGDI\Bundesamt"

# ----------------------------------------------------------------------------------------------------------------------

df = pd.read_excel(path_file)
df[["A", "org", "B"]] = df["TECHPUBLAYERNAME"].str.split('.', 2, expand=True)

org_names = set(df['org'].tolist())
print(org_names)

for org_name in org_names:
    a = df.copy()
    a = a.loc[a["org"] == org_name]
    a.to_excel(os.path.join(path, org_name + ".xlsx"), encoding="utf-8-sig")
