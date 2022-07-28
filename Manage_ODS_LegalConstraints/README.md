# Manage opendata.swiss legal constraints
**Add** and **delete** legal constraints for the opendata.swiss plateform.

These legal constraints are placed here in the metadata XML

`/che:CHE_MD_Metadata/gmd:identificationInfo/*/gmd:resourceConstraints/che:CHE_MD_LegalConstraints/gmd:otherConstraints`

They take the 4 classical values for open data
* `OPEN` Open use
* `OPEN BY` Open use. Must provide the source.
* `OPEN ASK` Open use. Use for commercial purposes requires permission of the data owner.
* `OPEN BY ASK` Open use. Must provide the source. Use for commercial purposes requires permission of the data owner.

These legal constraints, when correctly set, are mapped to Opendata.swiss plateforme to give the correct terms of use with the corresponding icons.

More Info : https://opendata.swiss/en/terms-of-use

---
### Requirements
This script runs on python 3. Following packages are needed :
* requests
* urllib3
* lxml
---

### Usage
```python
import ods_constraint
from ods_constraint import ODS_OPEN, ODS_OPENBY, ODS_OPENASK, ODS_OPENBYASK

ods = ods_constraint.ODSConstraint(env="int")
```
```
env -> str (default = 'int'), can be set to 'prod' to work on the production environment of geocat
```
#### Add a new ODS legal constraint
```python
ods.add_constraint(uuids=uuids, constraint=ODS_OPENBY, backup=False)
```
#### Delete an existing ODS legal constraint
```python
ods.delete_constraint(uuids=uuids, constraint=ODS_OPENBY, backup=False)
```
**Parameters**
```
  uuids : a list of metadata uuid ["uuid1", "uuid2", etc.]
  constraint : [ODS_OPEN, ODS_OPENBY, ODS_OPENASK, ODS_OPENBYASK]
  backup : True or False. If True, backup all metadata before changes are made
```
