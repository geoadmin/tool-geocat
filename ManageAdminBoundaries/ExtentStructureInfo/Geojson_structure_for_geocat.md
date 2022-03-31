# Geojson Structure for geocat
This tool uses a reference file in geojson. The structure of the latter must follow the rules below.
### General considerations
* The SRS of the coordinates must be given in WGS84 (EPSG:4326).
* The encoding of the file must be UTF-8 to correctly describe the accents.
* The vertices order is as follows (this does not correspond to the up-to-date standard of geojson format) :
    * Exterior Polygons : clockwise order
    * Interior Polygons : counter clockwise order
---
### Single Polygon
```json
[
    {
        "type": "FeatureCollection",
        "name": "swissBoundaries3D_WGS84",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [
                                    "lng",
                                    "lat"
                                ],
                                [
                                    "lng",
                                    "lat"
                                ]
                            ]
                        ]
                    ]
                },
                "properties": {
                  "attribute_1": "value",
                  "attribute_2": "value"
                }
            }
        ]
    }
]
```
---
### Multi Polygons with hole inside them (donut)
```json
[
    {
        "type": "FeatureCollection",
        "name": "swissBoundaries3D_WGS84",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [
                                    "poly1 - lng",
                                    "poly1 - lat"
                                ],
                                [
                                    "poly1 - lng",
                                    "poly1 - lat"
                                ]
                            ],
                            [
                                [
                                    "donut of poly1 - lng",
                                    "donut of poly1 - lat"
                                ],
                                [
                                    "donut of poly1 - lng",
                                    "donut of poly1 - lat"
                                ]
                            ]
                        ],
                        [
                            [
                                [
                                    "poly2 - lng",
                                    "poly2 - lat"
                                ],
                                [
                                    "poly2 - lng",
                                    "poly2 - lat"
                                ]
                            ]
                        ]
                    ]
                },
                "properties": {
                  "attribute_1": "value",
                  "attribute_2": "value"
                }
            }
        ]
    }
]
```
