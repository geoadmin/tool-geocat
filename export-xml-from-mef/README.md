# Export metadata from MEF
Export a given list of metadata (UUID) from a MEF (metadata exchange format) archive (.zip) and save them in XML.
### Requirements
This script runs on python 3.
### Usage
1. Clone the repository anywhere you like.
2. Open the file ``export-xml-from-mef/geocat_get_backup_xml_from_zip.py`` either with an IDE or a text editor.
3. Adapt the variables directly into the python file. More information are available in comments in the python file.
```
Variables:  zip_folder - path to the backup-zip
            new_folder - path, where the xmls should be saved
            all_uuids - list of uuids you want to get (must be in [], ex: ["uuid1", "uuid2"])
```
4. Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)
