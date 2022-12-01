# Admin Boundaries Update of november 2022
Following the need of a partner, we decided to add the districts geometries as subtemplate in geocat.ch 

### Geojson reference file source
* The `g1b22.shp` shapefile from BFS have been taken (generalization 1). The cantons considered as
district because there are no districts within their perimeter have been manually removed

### LV95 -> WGS84
Since the data from BFS and swisstopo are in LV95. The shapefile have been transformed with the georef app from swisstopo. The exit SRS must be in WGS84 in degrees. 
* The georef app doesn't save the `.cpg` file when exporting in shapefile. It must be manually copied and renamed to match the other files. This file contains the encoding info for the attributes table. It is used to read correctly the accents.
* The georef app export the wrong `.prj` file when exporting in shapefile. It must be deleted and the projection must be explicitly given when importing the shapefile in GIS software.

### SHP -> Geojson
Used the [FME WorkBench](./shp2geojson.fmw) to transform the different shapefiles into a geojson ready for the tool.

### Results
**ONLY ON PROD**
> * 134 **districts** have been added 
> * 6 **old districts** that have been created without a dedicated UUID have been deleted. 3 of them
where linked to metadata. The link has been updated to the newly created districts subtemplates.
