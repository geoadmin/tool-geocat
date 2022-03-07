# Get groups list
Get a csv list with all groups information.
### requirements
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
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                        don't need that. It is necessary when you run the script with VPN or directly in Wabern.
            Path_File_out - where to save the information about. Recommendation to first save the new file with an other 
                            name than the current (old) one and to check it. Then you can overwrite it.
```
4. Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)
