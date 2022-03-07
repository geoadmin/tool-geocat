# Replace metadata contact
Replace a given contact (subtemplate) either in every metadata or in a specific one.
### Requirements
The scripts run on python 3. Following packages are needed :
* pandas
* requests
* urllib3
### Usage
Clone the repository anywhere you like.
#### To replace a given contact in all metadata
1. First run the ``geocat_api_create_contact_list_for_replacement_general.py`` script in order to generate a csv list used by the second script.
   * Open the file ``metadata-replace-contact/geocat_api_create_contact_list_for_replacement_general.py`` either with an IDE or a text editor.
   * Adapt the variables directly into the python file. More information are available in comments in the python file.
      ```
      Variables:  geocat_user - your username (The password will be asked automatically by the script)
                  mail_old - the mail that is used for the search in geocat.ch
                  geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
                  proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                               don't need that. It is necessary when you run the script with VPN or directly in Wabern.
                  path - path to the folder where to save the files.
                  filename - general filename. You can keep it like it is or you can change it to a name you like.
      ```
   * Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)

2. Then run the ``geocat_api_replace_contacts_with_list_general.py`` script with the csv list from step 1.
   * Open the file ``metadata-replace-contact/geocat_api_replace_contacts_with_list_general.py`` either with an IDE or a text editor.
   * Adapt the variables directly into the python file. More information are available in comments in the python file.
      ```
      Variables:  geocat_user - your username (The password will be asked automatically by the script)
                  list_file_in - path to where the csv with information is located (uuid, place, role,...)
                  list_file_out - path where to save the output. Important to have the control, where there were problems in
                                  the modification
                  orgname - the organization name of the new contact
                  mail - the mail address of the new contact
                  posname - the position name of the new contact (check in an existing XML, what this is)
                  first_name - the first name of the new contact
                  last_name - the last_name of the new contact
                  geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
                  proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                              don't need that. It is necessary when you run the script with VPN or directly in Wabern.
      ```
   * Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)

#### To replace a given contact in a specific metadata
1. Clone the repository anywhere you like.
2. Open the file ``metadata-replace-contact/geocat_api_replace_single_contact_general.py `` either with an IDE or a text editor.
3. Adapt the variables directly into the python file. More information are available in comments in the python file.
```
Variables:  geocat_user - your username (The password will be asked automatically by the script)
            uuid - the uuid of the MD you want to modify
            place - there are three possible places for a contact: "MDContact", "ResourceContact", "DistributorContact"
            role - the role the new contact should have. ex. resourceProvider,...
            orgname - The name of the organisation of the new contact
            mail - the email of the new contact
            posname - the positionname of the new contact
            first_name - the first name of the new contact
            last_name - the last name of the new contact
            delete - "yes" or "no - it deletes (all) the contacts that are present at the designated place (above)
            geocat_environment - "INT" or "PROD" - depending on where you want to modify your MD
            proxydict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                         don't need that. It is necessary when you run the script with VPN or directly in Wabern.
```
4. Run the file with a python 3 interpreter. (swisstopo : ``C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe``)
