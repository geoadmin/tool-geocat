# Metadata batch edit
With this script, you can make simple batch edits on a list of uuids. gn_replace, gn_add & gn_delete are
simple batch edits, when they are executed on non reusable objects like titles, protocols, dates, links,...
All the uuids that went through are stored in a csv with the information on the statuscode of the batch edit. 
This file is stored in the same folder as the input_file with the uuids.
### Requirements
This script runs on python 3. Following packages are needed :
* pandas
* requests
* urllib3
* numpy
### Usage
1. Clone the repository anywhere you like.
2. Open the file ``get-groups-list/geocat_create_group_csv.py `` either with an IDE or a text editor.
3. Adapt the variables directly into the python file. More information are available in comments in the python file.
```
Variables:  geocat_user - your username (The password will be asked automatically by the script)
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            input_file - csv-file with at least a column named "UUID". There can be other columns present
            xpath - xpath (batchedit) to the attribute you want to change
            value - value (batchedit) that you want to change
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                        don't need that. It is necessary when you run the script with VPN or directly in Wabern.
```
4. Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)

