# Get users list
Get a csv list with all users information.
### Requirements
This script runs on python 3. Following packages are needed :
* pandas
* requests
* urllib3
* numpy
### Usage
1. Clone the repository anywhere you like.
2. Open the file ``get-users-list/geocat_user_list.py`` either with an IDE or a text editor.
3. Adapt the variables directly into the python file. More information are available in comments in the python file.
```
Variables:  geocat_user - your username (The password will be asked automatically by the script)
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            Path_File - path where the CSV will be saved. The name of the csv is generated automatically.
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                        don't need that. It is necessary when you run the script with VPN or directly in Wabern.
```
4. Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)

