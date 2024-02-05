# Admin Boundaries Update of 05.02.2024
Following the new admin units data from swisstopo and BFS for 2024, the geocat team launched a new update of all admin units in geocat.  

### Geojson reference file source
* The shapefiles from BFS have been taken (generalization 1)
* `g1g23.shp` (municipalities), `g1g23_encl.shp` (enclaves DE & IT), `g1g23_li.shp` (municipalities from FL) and `g1s23.shp` (Lakes) 
have been merged together to create a single file for municipalities.
* `g1b23.shp` for districts
* `g1k23.shp` for cantons
* `g1l23.shp` for CH. Does not contain FL
* FL taken from swissBOUNDARIES3D data (no generalization) with selection of FL.

### LV95 -> WGS84
Since the data from BFS and swisstopo are in LV95. The shapefile have been transformed with the georef app from swisstopo. The exit SRS must be in WGS84 in degrees. 
* The georef app doesn't save the `.cpg` file when exporting in shapefile. It must be manually copied and renamed to match the other files. This file contains the encoding info for the attributes table. It is used to read correctly the accents.
* The georef app export the wrong `.prj` file when exporting in shapefile. It must be deleted and the projection must be explicitly given when importing the shapefile in GIS software.

### SHP -> Geojson
Used the [FME WorkBench](./shp2geojson.fmw) to transform the different shapefiles into a geojson ready for the tool.

### Results

* For municipalities, only the ones with changes (source : Applikation der Schweizer Gemeinden, BFS) have been processed. For the Rest, every boundaries have been overridden (only the geometry !) by the new `.json` files.

> * 4 **municipalities** have been updated
> * 1 new **municipality** have been created
> * 6 old **municipalities** have been deleted (not used in any metadata)
> * 134 **districts** have been updated (only geometry !)
> * 26 **cantons** updated (only geometry)
> * CH updated (only geometry)
> * FL updated (only geometry)