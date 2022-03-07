# Manage BGDI metadata
Scripts to manage the metadata from BGDI datasets.
### Requirements
The scripts run on python 3. Following packages are needed :
* pandas
* requests
* urllib3
* numpy
### Usage
1. Clone the repository anywhere you like.
2. Open the python files either with an IDE or a text editor.
3. Adapt the variables directly into the python file.
4. Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)

#### mapgeoadmin-link/bmd_group_by_amt.py
```
Purpose:    This script divides the output of a BMD4MUM search into Bundesämter. So you have a csv pro Bundesamt.

Variables:  path_file - path and filename of the excel of you BMD4MUM-request
            path - path to a folder, where you want to store the csvs of each Amt
```

#### mapgeoadmin-link/geocat_get_MDs_from_BGDI_in_BMD.py
```
Purpose:    check whether "BGDI" exists as keyword in the MDs from the list from BMD.
            This list from BMD should contain all BGDI-Datasets.
            Then get all the necessairy information from geocat to these MDs, as uuid, keywords,...
            This was made for the Ticket METADATA_SB-151. No MDs are modified here.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            file_bmd4mum - Excelfile from search-request on BMD4MUM
            Path_File_out - where to save the csvs, that will be generated in this script
            file_groupowners - path to the file called groupowners.csv. This is a file with informations about the
                               different groups that use geocat (cantons, bundesämter,...). In this script, it is
                               a special csv, where just the infos from groups with BGDI are present.
            geocat_environment - "INT" or "PROD"
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.
```


#### mapgeoadmin-link/geocat_link_mapgeoadmin.py
```
Purpose:    This was made for the Ticket METADATA_SB-152. The script goes through a list of uuids (created from BMD4MUM 
            and separated by bmd_group_by_amt.py). It searches for existing links. Then it adds a link of MAP:Preview to
            all those of the list, that don't have one yet. the ending of the link is taken from the bmd-excel.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            protokoll - protocol of the link you add
            title - title of the link you add, in all languages
            description - description of the link you add, in all languages (can be equal to the title)
            map_url_base - base of the map_url. the ending of the link is taken from the bmd-excel.
            folder - folder of where the bmd-excel is lying
            file - name of the bmd-excel
            geocat_environment - "INT" or "PROD"
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.
```


#### restapi-link/get_apis_by_amt.py
```
Purpose:    This script takes the list of layers from http://api3.geo.admin.ch/api/faq/index.html#which-layers-are-available
            and searches for its uuids (from bmd4mum). It then makes a list of uuids per Bundesamt. This list will be 
            used as input for the addition of the Rest-API-Link (METADATA_SB-143)

Variables:  report_bmd - path and filename of the excel of you BMD4MUM-request
            list_api - path and filename of a excel list, which is copied from 
                       http://api3.geo.admin.ch/api/faq/index.html#which-layers-are-available
            path - path to a folder, where you want to store the csvs of each Bundesamt
```



#### restapi-link/link_restapi.py
```
Purpose:    This was made for the Ticket METADATA_SB-143. The script goes through a list of uuids (get_apis_by_amt.py). 
            It searches for existing links and checks if they are correctly. If not, it adapts the existing link and
            description/title of the protocol ESRI:REST. For those with the correct link, the description/title is not
            adapted.

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            protokoll - protocol of the link you add
            title - title of the link you add, in all languages
            description - description of the link you add, in all languages (can be equal to the title)
            link_base - base of the link. the ending of the link is taken from the bmd-excel.
            folder - folder of where the bmd-excel is lying
            file - name of the bmd-excel
            geocat_environment - "INT" or "PROD"
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.
```
     
