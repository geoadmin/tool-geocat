# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    This script goes into the zip-folder and saves the selected xmls in another folder. So you don't have to
            unzip everything and search manually for the uuid you want.

Variables:  zip_folder - path to the backup-zip
            new_folder - path, where the xmls should be saved
            all_uuids - list of uuids you want to get (must be in [], ex: ["uuid1", "uuid2"])
            
Remarks:    ADAPT THE VARIABLES IN THE LINES BELOW
------------------------------------------------------------------------------------------------------------------------
"""
import zipfile
import os


# TODO: adapt the following variables
zip_folder = r""
new_folder = r""
all_uuids = ["74e0e4a7-165a-414d-b1a5-1921162f04ab"]


# zip file handler
zip = zipfile.ZipFile(zip_folder)

for uuid in all_uuids:
    # extract a specific file from the zip container
    f = zip.open(uuid + "/metadata/metadata.xml")

    # save the extraced file
    content = f.read()
    f = open(os.path.join(new_folder, uuid + '.xml'), 'wb')
    f.write(content)
    f.close()
