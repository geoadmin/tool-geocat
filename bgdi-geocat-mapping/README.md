# Mapping BGDI - geocat.ch
![Static Badge](https://img.shields.io/badge/Python-3.9%2B-%2334eb77)

Consistency between the BGDI and geocat.ch (for records belonging to the BGDI). For more info, check https://jira.swisstopo.ch/browse/METADATA_SB-167

---
## Installation
Clone the repo and install dependencies in a python virtual environment (recommended)
```
git clone https://github.com/geoadmin/tool-geocat.git

cd tool-geocat/bgdi-geocat-mapping

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### at swisstopo (using powershell)
```
git clone https://github.com/geoadmin/tool-geocat.git

cd tool-geocat/bgdi-geocat-mapping

& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\Scripts\pip3" install --trusted-host github.com --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --proxy=proxy-bvcol.admin.ch:8080 -r requirements.txt
```
---

## Get the BGDI source
The firste source is the google sheet : https://docs.google.com/spreadsheets/d/1to10g8bIhVv0GxMQZk00Yc-kIk9FpMzQJp6veFXgN6s/edit#gid=1731531890<br>

But we rely also on the BMD to add missing records and to fix missing geocat UUID from the latter.
Therefore, the script takes `.csv` file with the BMD records as argument. Hier is how to generate this file :
* From https://ltbmd.adr.admin.ch/BmdPortal/Reporting extract the following table as excel table.
```sql
select PUB.techpublayername, PUB.geocatuuid, ZS.ingeststate as "Status (ZS)", PUB.ingeststate as "INGESTSTATE", ZS.TimestandDate
from bmd.publayer PUB, bmd.timestand ZS
where PUB.reftimestand = ZS.timestandid AND PUB.gdstechname = ZS.gdstechname;  
```
* In excel, Process the table to have only unique Layer ID and geocat UUID : 
  * Delete rows that have emtpy Layer ID or geocat UUID. 
  * Keep the most recent according to `TimestandDate` and for duplicated with same `TimestandDate`, apply the following priority for `Ingestate` "Productive" -> "NotProductive" -> "Decommissioned" -> "Deleted". For that, you can create a new column `order` in excel with the following formula :
    
    ```
    =SI(D2="Productive";1;SI(D2="NotProductive";2;SI(D2="Decommissioned";3;4)))
    ```
    Then sort the table first by `TimestandDate` (from Z to A to have the most actual ones first) and second by `order` (from smallest to largest). Select all rows and delete duplicated in colomn `TECHPUBLAYERNAME` and `GEOCATUUID`. Thanks to the ordering applied, it will delete duplicated ones that are oldest and/or with deprecated `Ingestate`.
    
* Export a `.csv` file with at least the following columns :

  |TECHPUBLAYERNAME|GEOCATUUID|INGESTSTATE|
  |---|---|---|
  |ch.blw.erosion|02210bb3-1c51-4c2c-a665-a696286b945c|Productive|

---
## Initiate Mapping
By initiating the `BGDIMapping` class, it will compute the mapping between the BGDI and geocat.ch.
```python
from bgdi_mapping import BGDIMapping

mapping = BGDIMapping(bmd="report.csv", env="int")
# bmd is the csv file containing the BMD records
# env is the geocat environment to deal with. "int" or "prod"
```
The resulting mapping (dataframe) is stored in the variable `mapping.mapping`. You can either analyse it in a IDE or export it as a csv file `mapping.mapping.to_csv("file.csv")`

Make sure there is no duplicated in the mapping dataframe in the field `Geocat UUID` and `Layer ID`.
With pandas :
```python
mapping.mapping[mapping.mapping["Layer ID"].duplicated()]
mapping.mapping[mapping.mapping["Geocat UUID"].duplicated()]

# Delete a row by index
mapping.mapping = mapping.mapping.drop([719])
```

---
## Get list of metadata to be repaired and backup them
```python
# Get List

uuids = mapping.mapping.loc[
    ((mapping.mapping['Published'] == "To publish") | 
    (mapping.mapping['Geocat Status'].isin(["Add obsolete", "Remove obsolete"])) | 
    (mapping.mapping['Keyword'].isin(["Add BGDI", "Remove BGDI"])) | 
    (mapping.mapping['Identifier'] == "Add identifier") | 
    ((mapping.mapping['WMS Link'].isin(["Add WMS", "Fix WMS"])) & (mapping.mapping['Published'].isin(["To publish", "Published"]))) | 
    ((mapping.mapping['WMTS Link'].isin(["Add WMTS", "Fix WMTS"])) & (mapping.mapping['Published'].isin(["To publish", "Published"])))| 
    ((mapping.mapping['API3 Link'].isin(["Add API3", "Fix API3"])) & (mapping.mapping['Published'].isin(["To publish", "Published"])))| 
    ((mapping.mapping['ODS Permalink'].isin(["Add ODS Permalink", "Fix ODS Permalink"])) & (mapping.mapping['Published'].isin(["To publish", "Published"])))| 
    (mapping.mapping['ODS Permalink'] == "Remove ODS Permalink") |
    (mapping.mapping['WMS Link'] == "Remove WMS") |
    (mapping.mapping['WMTS Link'] == "Remove WMTS") |
    (mapping.mapping['API3 Link'] == "Remove API3") |
    ((mapping.mapping['Map Preview Link'] == "Add map preview") & (mapping.mapping['Published'].isin(["To publish", "Published"]))))
     & 
     (mapping.mapping['Published'] != "To unpublish")
]["Geocat UUID"].tolist()

# Backup Metadata in MEF

mapping.backup_metadata(uuids=uuids, with_related=False)
```

---
## Check Validity before and after reparation
Get a query for geocat.ch to select the metadata from the list above.
```python
" OR ".join(uuids)
```
Copy the printed output and paste it in the search bar of the edit board of `geocat.ch`. Check the number of valid and not valid metadata. 

After reparing all metadata, with the selected metadata from above, run a validation and check that the number of valid and invalid metadata are still the same.

---
## Repair Metadata
Repair a single metadata
```python
mapping.repair_metadata(uuid="metadata-uuid")
```
Repair all metadata in the mapping dataframe
```python
mapping.repair_all(tounpub=False)

# tounpub argument ensures that the metadata "To unpublish" are not processed by default.
# Can be set to True to process these metadata
```
