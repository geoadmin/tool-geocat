## Mapping BGDI - geocat.ch
Consistency between the BGDI and geocat.ch (for records belonging to the BGDI)
### Get the BMD records
The firste source is the google sheet : https://docs.google.com/spreadsheets/d/1to10g8bIhVv0GxMQZk00Yc-kIk9FpMzQJp6veFXgN6s/edit#gid=1731531890<br>
But we rely also on the BMD to add missing records and to fix missing geocat UUID from the latter.
Therefore, the script need a `report.csv` file with the BMD records :
* From https://ltbmd.adr.admin.ch/BmdPortal/Reporting extract the following table
```sql
select PUB.techpublayername, PUB.geocatuuid, ZS.ingeststate as "Status (ZS)", PUB.ingeststate as "INGESTSTATE", ZS.TimestandDate
from bmd.publayer PUB, bmd.timestand ZS
where PUB.reftimestand = ZS.timestandid AND PUB.gdstechname = ZS.gdstechname;  
```
* Process the table to have only unique Layer ID and geocat UUID. Keep the most recent according to TimestandDate and for duplicated with same timestand, apply the following priority "Productive" -> "NotProductive" -> "Decommissioned" -> "Deleted".
* Export a csv file with the following columns :

  |TECHPUBLAYERNAME| GEOCATUUID|STATUS (ZS)|INGESTSTATE|TIMESTANDDATE|
  |---|---|---|---|---|
  |ch.blw.erosion|02210bb3-1c51-4c2c-a665-a696286b945c|InProgress|Productive|2022-05-03 00:00:00|
