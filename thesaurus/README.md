# Manage thesaurus & keywords
Scripts to manage the thesaurus and the keywords
### Requirements
This script runs on python 3. Following packages are needed :
* pandas
* requests
* urllib3
* numpy
### Usage
1. Clone the repository anywhere you like.
2. Open the python files either with an IDE or a text editor.
3. Adapt the variables directly into the python file.
4. Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)

#### thesaurus_information_from_concerned_metadata.py
```
Purpose:    get the information of a keyword. Who uses the keyword and in which MD is it used?
            The script makes one list per group that is concerned by some of these keywords... It was created during the
            clean-up of the geocat.ch-Thesaurus in order to contact the organisations with the keywords they use, but
            which are very rarely used

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            File_geocat - This is a csv_count (from thesaurus:rdf_to_csv_count.py), where in an additional column called
                          "replace" is marked "yes" for every keyword that should be included in this script..
            Path_File_out - where to save the csvs, that will be generated in this script
            file_groupowners - path to the file called groupowners.csv. This is a file with informations about the
                               different groups that use geocat (cantons, bundesämter,...). It has fo example the
                               information which group is harvesting and which is editing directly.
            geocat_environment - "INT" or "PROD"
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.
```

#### thesaurus_prepare_list_replace_keyword_cswt.py
```
Purpose:    This script looks for all MDs, that use a certain keyword. It creates a list at the end, which is used
            as input for the FME-workbench "CSWT_replace_keywords_series.fmw". In fact, the script looks at the uuids 
            having a keyword and lists them with additional attributes, like the info if the new keyword we want to add 
            is already there.
            This script was created during the cleanup of the geocat.ch-Thesarus in order to replace similar keywords
            that are used often

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            old_keyword_de / _fr - the keyword in german and french, that should be replaced
            new_keyword - the new keyword in all four languages
            new_keyword_type - "geocat" or "gemet", depending on where the new keyword is located
            folder - where to save the csvs, that will be generated in this script
            file_groupowners - path to the file called groupowners.csv. This is a file with informations about the
                               different groups that use geocat (cantons, bundesämter,...). It has fo example the
                               information which group is harvesting and which is editing directly.
            geocat_environment - "INT" or "PROD"
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.
```

#### thesaurus_rdf_to_csv_categories.py
```
Purpose:    It takes the rdf from the geocat-website and writes all the keywords with its translations into a table.
            Currently, this csv-file is part of the documentation on CMS.
            It also includes the categories. This script was created during the cleanup of the geocat-ch-Thesarus and
            it creates the final output

Variables:  RDF_name - filename of the RDF-file of the thesaurus (without the path)
            Path - path to where the RDF-file lies (without RDF_name). The newly created csvs and textfiles will be
                   located in this path with the filename of the RDF
```

#### thesaurus_rdf_to_csv_count.py
```
Purpose:    It takes the rdf from the geocat-website and writes all the keywords with its translations into a table.
            Additionally you can chose whether you also want it to calculate how much each keyword is used (for all 
            languages together or also for each language seperately).
            This script was created during the cleanup of the geocat-ch-Thesarus

Variables:  geocat_user - your username (The password will be asked automatically by the script)
            FileIn - path & filename of the RDF-file of the thesaurus
            FileOut - path & filename of the newly counted CSV
            catalog - "geocat" or "gemet" (in small letters)
            count - "yes" or "no". If yes, it counts how many times each keyword is used for each language separately
            count_all - "yes" or "no". If yes, it counts how many times each keyword is used for all languages together
            geocat_environment - "INT" or "PROD"
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                        don't need that. It is necessary when you run the script with VPN or directly in Wabern
```
