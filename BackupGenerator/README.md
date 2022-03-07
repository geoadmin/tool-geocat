# Backup Generator
Backup the entire geocat.ch catalogue, including :
* metadata (as MEF archive)
* users (as json files and csv list)
* groups (as json files and csv list)
* subtemplates (i.e. reusable objects as XML)
* thesaurus (as rdf files)
* unpublished reports (as csv file)
### Requirements
This script runs on python 3. Following packages are needed :
* colorama
* requests
* urllib3
* pandas
### Usage
Clone the repository anywhere you like.
#### In a python IDE
Inside the tool folder ``.\BackupGenerator\``

```Python
import geocat_backup

BACKUP_DIR = "the-directory-to-save-the-backup" # created if not exists

geocat_backup.GeocatBackup(backup_dir=BACKUP_DIR, env='int', catalogue=True, users=True, groups=True,
                           reusable_objects=True, thesaurus=True)
```

Attributes:
```
    backup_dir (required):  a string containing the path to the folder where to save the backup. Created if not exists
    env (required):   'int' or 'prod', default='int'. The environment to backup.
    catalogue (optional):   boolean, default=True. If False, the metadata (MEF archive) are not exported.
    users (optional):   boolean, default=True. If False, the users are not exported.
    groups (optional):  boolean, default=True. If False, the groups are not exported.
    reusable_objects (optional):  boolean, default=True. If False, the reusable objects (i.e. subtemplates) are not exported.
    thesaurus (optional):   boolean, default=True. If False, the thesaurus are not exported.
```

#### In a command line interface (swisstopo)
```
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" \BackupGenerator\geocat_backup.py backup_dir=directory-to-save-the-backup env=int [catalogue=True] [users=True] [groups=True] [reusable_objects=True] [thesaurus=True]
```

