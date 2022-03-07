# Export metadata
Export a given list of metadata (UUID) from geocat and save them in XML.
### Requirements
This script runs on python 3. Following packages are needed :
* pandas
* requests
* urllib3
### Usage
1. Clone the repository anywhere you like.
2. Open the file ``export-xml/geocat_save_xmls.py`` either with an IDE or a text editor.
3. Adapt the variables directly into the python file. More information are available in comments in the python file.
```
Variables:  geocat_user - your username (The password will be asked automatically by the script)
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            input_file - csv-file with at least a column named "UUID". There can be other columns present
            folder - path to the folder, where the xmls should be saved in. It will be zipped at the end
            xml_types - you can chose which type of xml you want ["GM03", "ISO19139", "ISO19139.che"]. It must be a list
            zip_folder - if "yes", then the folder will additionally be zipped at the end of the script. the
                         unzipped folder remains
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                        don't need that. It is necessary when you run the script with VPN or directly in Wabern.
```
4. Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)
