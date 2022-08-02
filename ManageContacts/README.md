# Manage Contacts

Contacts are shared object (fragment of XML) that can be used and re-used in several metadata.
In the metadata, contacts can be placed at various location and are given by their UUID and the role for the contact in an xlink:href attribute of the parent tag. 


E.g. within the tag `<gmd:contact>`, the contact UUID and the role are given like this:
```
<gmd:contact xlink:href="local://srv/api/registries/entries/{contact_UUID}?lang=fre,ita,eng,ger&amp;process=*//gmd:CI_RoleCode/@codeListValue~{role}">
```
When saving the metadata, geocat.ch fetches the content of the contact and populates it inside the tag.

---
### Requirements
This script runs on python 3. Following packages are needed :
* requests
* urllib3
* lxml
---
### Installation
Clone the repo anywhere you like. At the root folder, import the `manage_contact.py` python module.

---
### Usage
#### Import
```python
import manage_contact

contacts = manage_contact.ManageContact(env="int")  # env -> str (default = 'int'), can be set to 'prod' to work on the production environment of geocat
```
#### Get the first metadata contact xlink
```python
contacts.get_md_contact_xlink(uuid=uuid)  # uuid : the metadata's uuid
```
#### Replace all ressource contacts by a single new contact
```python
NEW_CONTACT = "local://srv/api/registries/entries/{contact_uuid}?lang=ger,fre,ita,eng,roh&amp;process=*//gmd:CI_RoleCode/@codeListValue~{role}"

contacts.replace_ressource_contact(uuid=uuid, contact_xlink=NEW_CONTACT)  # uuid : the metadata's uuid
```
#### Replace all metadata contacts by a single new contact
```python
NEW_CONTACT = "local://srv/api/registries/entries/{contact_uuid}?lang=ger,fre,ita,eng,roh&amp;process=*//gmd:CI_RoleCode/@codeListValue~{role}"

contacts.replace_md_contact(uuid=uuid, contact_xlink=NEW_CONTACT)  # uuid : the metadata's uuid
```
