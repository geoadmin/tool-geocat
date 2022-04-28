# S3 Consistency Checker
Do the following checks with metadata inside an AWS S3 Bucket from the harvesting partners of geocat.ch :
* Check if XML are well formed
* Check if the schema is correct. At least can found a UUID
* Check if UUID is used in more than one XML
* Check the numer of correct XML (the ones that satisfy the 3 first checks) with the numer of metadata effectively in geocat 
in the corresponding group (1 group = 1 AWS S3 Bucket)
### Requirements
This script runs on python 3. Following packages are needed :
* colorama
* requests
* urllib3
* pysftp : this package is not installed by default at swisstopo (Python from ArcGIS)
### Usage
Clone the repository anywhere you like.
#### In a command line interface (swisstopo)
Inside the tool folder ``.\S3-consistency-checker\``

```
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" S3-consistency-checker.py groupID={group_id} S3path={s3_path} pk={private_key} [env={env}] 
```

Attributes:
```
group_id: str, the group ID corresponding to the S3 Bucket to check
s3_path: str, the path of the Bucket from the root of the SFTP Server
private_key: str, path to the SSH private Key (.rem, OpenSSH format)
env: str, default="prod". If set to "int", check the content of the Integration instance of geocat.ch
```
