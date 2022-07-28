 lines (41 sloc) 1.65 KB
# Manage Keywords
**Add** and **delete** Keyword

Keywords are available in several thesauri and can be retrieved by giving their ID and the thesaurus ID they belong to. 
Keywords live at this node in the metadata's XML.
```
/che:CHE_MD_Metadata/gmd:identificationInfo/*/gmd:descriptiveKeywords
```
Keywords are set up in the metadata's XML in a tag where the Keyword and Thesaurus ID are given in a xlink:href attribute. The content of the keywords is
then retrieved from the thesaurus and populate inside the tag.
```
<gmd:descriptiveKeywords xlink:href="local://srv/api/registries/vocabularies/keyword?skipdescriptivekeywords=true&thesaurus=local.theme.geocat.ch&id=http://geocat.ch/concept#e6485c01-fe69-485e-b194-035f682463db&lang=fre,ita,eng,ger">
```

---
### Requirements
This script runs on python 3. Following packages are needed :
* requests
* urllib3
* lxml
---
### Installation
Clone the repo anywhere you like. At the root folder, import the `manage_keyword.py` python module.

---
### Usage
#### Import and setup the keyword and thesaurus ID
```python
import manage_keyword

KEYWORD_ID = "http://geocat.ch/concept#e6485c01-fe69-485e-b194-035f682463db"
THESAURUS_ID = "local.theme.geocat.ch"

keyword = manage_keyword.ManageKeyword(env="int")  # env -> str (default = 'int'), can be set to 'prod' to work on the production environment of geocat
```
#### Add a new keyword
```python
keyword.add_keyword(uuids=uuids, keyword_id=KEYWORD_ID, thesaurus_id=THESAURUS_ID, backup=True)
```
#### Delete an existing ODS legal constraint
```python
keyword.delete_keyword(uuids=uuids, keyword_id=KEYWORD_ID, backup=True)
```
**Parameters**
```
  uuids : a list of metadata uuid ["uuid1", "uuid2", etc.]
  keyword_id : the ID of the keyword to add
  thesaurus_id : the thesaurus ID where the keyword comes from
  backup : True or False. If True, backup all metadata before changes are made
```
