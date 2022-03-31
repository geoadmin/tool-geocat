# GML Structure of Extent Subtemplates in geocat
Extents are saved in geocat.ch as subtemplates (reusable objects) in XML. 
The geometry part of these XML looks like a GML, here can you find the exact structure.
### General considerations
* The SRS of the coordinates must be given in WGS84 (EPSG:4326).
* It's possible to give coordinates in another SRS by specifying it in the `<gmd:surfaceMember srsName="EPSG:2056">` tag. If the SRS is not supported by the editing in geocat, it will generate a bug in geocat editing mode but still works for the MD and the validation. 
  The transformation applied is still to be controlled, may be very bad quality).
* Coordinates order between X and Y can be lat-lng or lng-lat. See below.
* The vertices order is as follows :
    * Exterior Polygons : clockwise order
    * Interior Polygons : counter clockwise order
---
### Structure
The structure below starts at the tag `<gmd:polygon>`. Here is the Xpath from the root the this tag :
```
\gmd:EX_Extent\gmd:geographicElement\gmd:EX_BoundingPolygon\gmd:polygon
```
### Single Polygon
> * If the tag `<gml:posList>` has the attribute `srsDimension=2`, the coordinates order is inverted : lat-lng.
> * If the tag `<gml:posList>` does not have the attribute `srsDimension=2`, the coordinates order is normal : lng-lat.
```xml
 <gmd:polygon xmlns:gmd='http://www.isotc211.org/2005/gmd'>
     <gml:MultiSurface xmlns='http://www.opengis.net/gml/3.2' xmlns:gml='http://www.opengis.net/gml/3.2' srsDimension='2'>
         <gml:surfaceMember>
             <gml:Polygon>
                 <gml:exterior>
                     <gml:LinearRing>
                         <gml:posList>
                               lng lat lng lat
                         </gml:posList>
                     </gml:LinearRing>
                 </gml:exterior>
             </gml:Polygon>
         </gml:surfaceMember>
     </gml:MultiSurface>
 </gmd:polygon>
```
---
### Multi Polygons
> * If the tag `<gml:posList>` has the attribute `srsDimension=2`, the coordinates order is inverted : lat-lng.
> * If the tag `<gml:posList>` does not have the attribute `srsDimension=2`, the coordinates order is normal : lng-lat.
```xml
 <gmd:polygon xmlns:gmd='http://www.isotc211.org/2005/gmd'>
     <gml:MultiSurface xmlns='http://www.opengis.net/gml/3.2' xmlns:gml='http://www.opengis.net/gml/3.2' srsDimension='2'>
         <gml:surfaceMember>
             <gml:Polygon>
                 <gml:exterior>
                     <gml:LinearRing>
                         <gml:posList>
                               Poly 1 : lng lat lng lat
                         </gml:posList>
                     </gml:LinearRing>
                 </gml:exterior>
             </gml:Polygon>
         </gml:surfaceMember>
         <gml:surfaceMember>
             <gml:Polygon>
                 <gml:exterior>
                     <gml:LinearRing>
                         <gml:posList>
                               Poly 2 : lng lat lng lat
                         </gml:posList>
                     </gml:LinearRing>
                 </gml:exterior>
             </gml:Polygon>
         </gml:surfaceMember>
     </gml:MultiSurface>
 </gmd:polygon>
```
---
### Polygon with holes (Donut)
> * If the tag `<gml:posList>` has the attribute `srsDimension=2`, the coordinates order is inverted : lat-lng.
> * If the tag `<gml:posList>` does not have the attribute `srsDimension=2`, the coordinates order is normal : lng-lat.
```xml
 <gmd:polygon xmlns:gmd='http://www.isotc211.org/2005/gmd'>
     <gml:MultiSurface xmlns='http://www.opengis.net/gml/3.2' xmlns:gml='http://www.opengis.net/gml/3.2' srsDimension='2'>
         <gml:surfaceMember>
             <gml:Polygon>
                 <gml:exterior>
                     <gml:LinearRing>
                         <gml:posList>
                               poly 1
                         </gml:posList>
                     </gml:LinearRing>
                 </gml:exterior>
                 <gml:interior>
                     <gml:LinearRing>
                         <gml:posList>
                               hole 1 inside poly 1
                         </gml:posList>
                     </gml:LinearRing>
                 </gml:interior>
                 <gml:interior>
                     <gml:LinearRing>
                         <gml:posList>
                               hole 2 inside poly 1
                         </gml:posList>
                     </gml:LinearRing>
                 </gml:interior>
             </gml:Polygon>
         </gml:surfaceMember>
         <gml:surfaceMember>
             <gml:Polygon>
                 <gml:exterior>
                     <gml:LinearRing>
                         <gml:posList>
                               poly 2
                         </gml:posList>
                     </gml:LinearRing>
                 </gml:exterior>
                 <gml:interior>
                     <gml:LinearRing>
                         <gml:posList>
                               hole 1 inside poly 2
                         </gml:posList>
                     </gml:LinearRing>
                 </gml:interior>
             </gml:Polygon>
         </gml:surfaceMember>
     </gml:MultiSurface>
 </gmd:polygon>
```
