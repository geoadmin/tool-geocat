# Get metadata list from search criteria
Get a list of MDs from geocat which correspond to certain criterias, which you can define in the variables.
You can also define, which attributes you want to have in the list. Check the variables.
### Requirements
This script runs on python 3. Following packages are needed :
* pandas
* requests
* urllib3
### Usage
1. Clone the repository anywhere you like.
2. Open the file ``get-list-from-search-request/geocat_generic_table_from_searchrequest.py `` either with an IDE or a text editor.
3. Adapt the variables directly into the python file. More information are available in comments in the python file.
```
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
```
4. Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)
