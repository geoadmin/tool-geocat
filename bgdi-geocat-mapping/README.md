## Mapping BGDI - geocat.ch
Consistency between the BGDI and geocat.ch (for records belonging to the BGDI). For more info, check https://jira.swisstopo.ch/browse/METADATA_SB-167


### Get the BGDI source
The firste source is the google sheet : https://docs.google.com/spreadsheets/d/1to10g8bIhVv0GxMQZk00Yc-kIk9FpMzQJp6veFXgN6s/edit#gid=1731531890<br>

But we rely also on the BMD to add missing records and to fix missing geocat UUID from the latter.
Therefore, the script takes `.csv` file with the BMD records as argument. Hier is how to generate this file :
* From https://ltbmd.adr.admin.ch/BmdPortal/Reporting extract the following table
```sql
select PUB.techpublayername, PUB.geocatuuid, ZS.ingeststate as "Status (ZS)", PUB.ingeststate as "INGESTSTATE", ZS.TimestandDate
from bmd.publayer PUB, bmd.timestand ZS
where PUB.reftimestand = ZS.timestandid AND PUB.gdstechname = ZS.gdstechname;  
```
* Process the table to have only unique Layer ID and geocat UUID. Keep the most recent according to TimestandDate and for duplicated with same timestand, apply the following priority "Productive" -> "NotProductive" -> "Decommissioned" -> "Deleted".
* Export a `.csv` file with at least the following columns :

  |TECHPUBLAYERNAME|GEOCATUUID|INGESTSTATE|
  |---|---|---|
  |ch.blw.erosion|02210bb3-1c51-4c2c-a665-a696286b945c|Productive|


### Initiate Mapping
By initiating the `BGDIMapping` class, it will compute the mapping between the BGDI and geocat.ch.
```python
from bgdi_mapping import BGDIMapping

mapping = BGDIMapping(bmd="report.csv", env="int")
# bmd is the csv file containing the BMD records
# env is the geocat environment to deal with. "int" or "prod"
```
The resulting mapping (dataframe) is stored in the variable `mapping.mapping`. You can either analyse it in a IDE or export it as a csv file `mapping.mapping.to_csv("file.csv")`


### Repair Metadata
Repair a single metadata
```python
mapping.repair_metadata(uuid="metadata-uuid")
```
Repair all metadata in the mapping dataframe
```python
mapping.repair_all(tounpub: bool = False)

# tounpub argument ensures that the metadata "To unpublish" are not processed by default.
# Can be set to True to process these metadata
```
