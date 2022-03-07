# Link subtemplates of metadata
Link all subtemplates (add the xlink in the XML) of a given list of metadata (UUID). Subtemplates are XML snippets that are used in several metadata = reusable objects.
### Requirements
This script runs on python 3. Following packages are needed :
* pandas
* requests
* urllib3
* numpy
* openpyxl
### Usage
1. Clone the repository anywhere you like.
2. Open the file ``metadata-subtemplate-xlink/geocat_api_link_reusable_objects.py`` either with an IDE or a text editor.
3. Adapt the variables directly into the python file. More information are available in comments in the python file.
 ```
 Variables:  geocat_user - your username (The password will be asked automatically by the script)
             geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
             proxy_dict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                          don't need that. It is necessary when you run the script with VPN or directly in Wabern.
             input_file - path to the CSV-file (just one column with the uuids, first line is called "uuid") with the 
                          uuids you want to treat.
 ```
4. Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)

