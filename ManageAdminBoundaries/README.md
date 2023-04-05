# Manage Admin Boundaries
**Inspect**, **update** and **delete** admin boundaries in geocat by comparing them with a geojon reference file.

Admin boundaries are saved as extent subtemplates in geocat. Any user with write access can create an extent subtemplate but cannot validate them.  

The admin bounadries are managed by the geocat team and have a special **UUID structure** :
* **Municipalities** : `geocatch-subtpl-extent-hoheitsgebiet-{gmdnr}` where `gmdnr` corresponds to the BFS municipality number
* **Districts** : `geocatch-subtpl-extent-bezirk-{bznr}` where `bznr` corresponds to the BFS district number
* **Cantons** : `geocatch-subtpl-extent-kantonsgebiet-{ktnr}` where `ktnr` corresponds to the BFS canton number
* **Countries** : `geocatch-subtpl-extent-landesgebiet-{code_iso}` where `code_iso` corresponds to the country ISO code (CH, FL)

---
### Requirements
This script runs on python 3. Following packages are needed :
* requests
* urllib3
* pandas
* colorama
* geopycat
---

### Data preparation - geojson reference file
The tool uses a geojson reference file to compare it with the data in geocat and to update or create admin boundaries as extent subtemplates.
The geojson file must be as follows :
* One feature per admin unit. If the admin unit has several polygons, the feature type must be Multipolygon
* The SRS must be in WGS84 (EPSG:4326)
* The encoding must be in UTF-8 to correctly describe accents
* The vertices must be as follows (this does not correspond to the up-to-date standard of geojson format) :
    * Exterior Polygons : clockwise order
    * Interior Polygons : counter clockwise order

More information about the geojson reference file structure can be found [here](ExtentStructureInfo/Geojson_structure_for_geocat.md).

If you have a shapefile in WGS84 (if in LV95 or LV03, transform it with the georef app from swisstopo from maximum accuracy),
you can use [this FME WorkBench](shp2geojson.fmw) to transform it into a geojson ready for the tool.

---
### Usage - Inspect

You can compare the admin boundaries in geocat with the geojson reference file. This creates 5 csv lists :
* `correct_{municipalities}{districts}{cantons}{countries}.csv` : ID and Name correct in geocat and reference
* `name_incorrect_{municipalities}{districts}{cantons}{countries}.csv` : ID is found but Name is different in geocat
* `id_incorrect_municipalities{municipalities}{districts}{cantons}{countries}.csv` : Name is found but ID is different in geocat
* `new_{municipalities}{districts}{cantons}{countries}.csv` : ID and Name not found in geocat
* `old_{municipalities}{districts}{cantons}{countries}.csv` : ID and Name not found in reference. 

**Municipalities**
```python
import ManageAdminBoundaries as ab

"""
Args: 
  output_dir: The directory where to save the csv lists. Optional. Default=root folder. Must exist
  ref_geojson: The geojson reference file
  gmdnr: The attribute name of the municipalities ID in the geojson reference file
  gmdname: The attribute name of the municipalities Name in the geojson reference file
  env: The environment of geocat. Optional. 'int' or 'prod'. Default = 'int'
"""

ab.CheckMunicipalityBoundaries(ref_geojson, gmdnr, gmdname, output_dir, env)
```

**Districts**
```python
import ManageAdminBoundaries as ab

"""
Args: 
  output_dir: The directory where to save the csv lists. Optional. Default=root folder. Must exist
  ref_geojson: The geojson reference file
  bznr: The attribute name of the districts ID in the geojson reference file
  bzname: The attribute name of the districts Name in the geojson reference file
  env: The environment of geocat. Optional. 'int' or 'prod'. Default = 'int'
"""

ab.CheckMunicipalityBoundaries(ref_geojson, bznr, bzname, output_dir, env)
```

**Cantons**
```python
import ManageAdminBoundaries as ab

"""
Args: 
  output_dir: The directory where to save the csv lists. Optional. Default=root folder. Must exist
  ref_geojson: The geojson reference file
  ktnr: The attribute name of the cantons ID in the geojson reference file
  ktname: The attribute name of the cantons Name in the geojson reference file
  env: The environment of geocat. Optional. 'int' or 'prod'. Default = 'int'
"""

ab.CheckCantonBoundaries(ref_geojson, ktdnr, ktname, output_dir, env)
```

**Countries**
```python
import ManageAdminBoundaries as ab

"""
Args: 
  output_dir: The directory where to save the csv lists. Optional. Default=root folder. Must exist
  ref_geojson: The geojson reference file
  landnr: The attribute name of the countries ID in the geojson reference file
  landname: The attribute name of the countries Name in the geojson reference file
  env: The environment of geocat. Optional. 'int' or 'prod'. Default = 'int'
"""

ab.CheckCountryBoundaries(ref_geojson, landdnr, landname, output_dir, env)
```
---
### Usage - Update
* Creates new admin boundaries if they don't exist
* Update the geometry and name (if option is selected) of exisiting admin boundaries
```python
import ManageAdminBoundaries as ab

"""
Args:
  output_dir: The directory where to save the csv lists. Optional. Default=root folder. Must exist
  ref_geojson: The geojson reference file
  number: The attribute name of the admin boundaries ID in the geojson reference file
  name: The attribute name of the admin boundaries Name in the geojson reference file
  type: The type of admin units. "g" for municipality, "b" for districts "k" for canton, "l" for country
  update_name: Optional. Default=True. If set to False, the name of admin boundaries are not updated. 
                With False, impossible to create a new non-exisiting admin units.
  env: The environment of geocat, optional, 'int' or 'prod', default = 'int'
"""

manage = ab.UpdateSubtemplatesExtent(ref_geojson, number, name, type, output_dir, update_name, env)
manage.update_all_subtemplates(with_backup=True)  # If with_backup=False, no backup of current extent subtemplates from geocat is made.
```
---
### Usage - Delete
Delete old admin boundaries if they are not linked to any metadata. Works only for municipalities.

This method uses a csv list created by the Inspect functionalty. It must be run before this one.
```python
import ManageAdminBoundaries as ab
import pandas as pd
import os

"""
Args:
  output_dir: The directory where to save the csv lists. Optional. Default=root folder. Must exist
  ref_geojson: The geojson reference file
  number: The attribute name of the admin boundaries ID in the geojson reference file
  name: The attribute name of the admin boundaries Name in the geojson reference file
  type: Must be "g".
  update_name: Optional. Default=True. If set to False, the name of admin boundaries are not updated. 
                With False, impossible to create a new non-exisiting admin units.
  env: The environment of geocat, optional, 'int' or 'prod', default = 'int'
"""

manage = ab.UpdateSubtemplatesExtent(ref_geojson, number, name, type, output_dir, update_name, env)

# Create a list of old extent subtemplates municipalities UUID that are not linked to any metadata
uuids = []
df = pd.read_csv(os.path.join(output_dir, "old_municipalities.csv"))
for index, row in df.iterrows():
if row["MD_Linked"] == 0:
      uuids.append(f'geocatch-subtpl-extent-hoheitsgebiet-{row["GMDNR"]}')

# Delete these list of subtemplates
manage.delete_subtemplates(uuids=uuids, with_backup=True)  # If with_backup=False, no backup of current extent subtemplates from geocat is made.
```

