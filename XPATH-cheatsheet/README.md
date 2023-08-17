# Geocat XPATH cheat sheet
**Valid for the schema : iso19139.che**

All XPATH start from the root node `che:CHE_MD_Metadata`. 

For example, the following given XPATH `gmd:fileIdentifier/gco:CharacterString` corresponds to that node :
```xml
<che:CHE_MD_Metadata>
  <gmd:fileIdentifier>
    <gco:CharacterString>4030f510-1b29-467c-a777-4f0ed3888f46</gco:CharacterString>
  </gmd:fileIdentifier>
  <gmd:language>
</che:CHE_MD_Metadata>
```

#### Attributes
* [Title](#title)
* [Alternate Title](#alternate-title)
* [Collective Title](#collective-title)
* [Contact for Metadata](#contact-for-metadata)
* [Contact for Resources](#contact-for-resources)
* [Contact for Distribution](#contact-for-distribution)
* [Status](#status)
* [Topic Category](#topic-category)
* [Dates](#dates)
* [Maintenance & Update Frequency](#maintenance-and-update-frequency)
* [AAP](#aap)
* [Keywords](#keywords)
* [Other Constraints](#other-constraints)
* [Basic Geodata](#basic-geodata)
* [Coordinates Reference System](#coordinates-reference-system)
* [Spatial Resolution](#spatial-resolution)
* [Localized Languages](#localized-languages)

# 
### Title
**In all localized languages**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:title//gmd:LocalisedCharacterString
```
**In the default language**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:title/gco:CharacterString
```
**In a specific language (e.g. english)**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:title//gmd:LocalisedCharacterString[locale = "#EN"]
```

# 
### Alternate Title
**In all localized languages**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:alternateTitle//gmd:LocalisedCharacterString
```
**In the default language**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:alternateTitle/gco:CharacterString
```
**In a specific language (e.g. english)**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:alternateTitle//gmd:LocalisedCharacterString[locale = "#EN"]
```

# 
### Collective Title
**In all localized languages**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:collectiveTitle//gmd:LocalisedCharacterString
```
**In the default language**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:collectiveTitle/gco:CharacterString
```
**In a specific language (e.g. english)**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:collectiveTitle//gmd:LocalisedCharacterString[locale = "#EN"]
```

# 
### Contact for Metadata
**Name in default language**
```
gmd:contact/*/gmd:organisationName/gco:CharacterString
```
**E-mail address**
```
gmd:contact/*/gmd:contactInfo//gmd:electronicMailAddress/gco:CharacterString
```
**Role**
```
gmd:contact/*/gmd:role/gmd:CI_RoleCode/@codeListValue
```

# 
### Contact for Resources
**Name in default language**
```
gmd:identificationInfo/*/gmd:pointOfContact/*/gmd:organisationName/gco:CharacterString
```
**E-mail address**
```
gmd:identificationInfo/*/gmd:pointOfContact/*/gmd:contactInfo//gmd:electronicMailAddress/gco:CharacterString
```
**Role**
```
gmd:identificationInfo/*/gmd:pointOfContact/*/gmd:role/gmd:CI_RoleCode/@codeListValue
```

# 
### Contact for Distribution
**Name in default language**
```
gmd:distributionInfo/*/gmd:distributor/*/gmd:distributorContact/*/gmd:organisationName/gco:CharacterString
```
**E-mail address**
```
gmd:distributionInfo/*/gmd:distributor/*/gmd:distributorContact/*/gmd:contactInfo//gmd:electronicMailAddress/gco:CharacterString
```
**Role**
```
gmd:distributionInfo/*/gmd:distributor/*/gmd:distributorContact/*/gmd:role/gmd:CI_RoleCode/@codeListValue
```

# 
### Status
**Code value**
```
gmd:identificationInfo/*/gmd:status/gmd:MD_ProgressCode/@codeListValue
```

# 
### Topic Category
```
gmd:identificationInfo/*/gmd:topicCategory/gmd:MD_TopicCategoryCode
```

# 
### Dates
**Creation Date**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:date/*/gmd:dateType/gmd:CI_DateTypeCode[@codeListValue = "creation"]/../../gmd:date/gco:Date
```
**Revision Date**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:date/*/gmd:dateType/gmd:CI_DateTypeCode[@codeListValue = "revision"]/../../gmd:date/gco:Date
```
**Publication Date**
```
gmd:identificationInfo/*/gmd:citation/*/gmd:date/*/gmd:dateType/gmd:CI_DateTypeCode[@codeListValue = "publication"]/../../gmd:date/gco:Date
```

# 
### Maintenance and Update Frequency
```
gmd:identificationInfo/*/gmd:resourceMaintenance/*/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode/@codeListValue
```

# 
### AAP
**Archival Value**
```
gmd:identificationInfo/*/gmd:resourceMaintenance/*/che:appraisal/*/che:appraisalOfArchivalValue/che:CHE_AppraisalOfArchivalValueCode/@codeListValue
```
**Duration of Conservation**
```
gmd:identificationInfo/*/gmd:resourceMaintenance/*/che:appraisal/*/che:durationOfConservation/gco:Integer
```

# 
### Keywords
**Only in default language**
```
gmd:identificationInfo/*/gmd:descriptiveKeywords/*/gmd:keyword/gco:CharacterString
```

# 
### Other Constraints
**Only in default language**
```
gmd:identificationInfo/*/gmd:resourceConstraints/*/gmd:otherConstraints/*[1]
```

# 
### Basic Geodata
**ID**
```
gmd:identificationInfo/*/che:basicGeodataID/gco:CharacterString
```
**Type**
```
gmd:identificationInfo/*/che:basicGeodataIDType/che:basicGeodataIDTypeCode/@codeListValue
```

# 
### Coordinates Reference System
**If entered from the proposed list**
```
gmd:referenceSystemInfo/*/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor/@xlink:title
```
**If entered manually**
```
gmd:referenceSystemInfo/*/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString
```

# 
### Localized languages
```
gmd:locale/gmd:PT_Locale/@id
```

# 
### Spatial Resolution
**Value**
```
gmd:identificationInfo/*/gmd:spatialResolution/*/gmd:distance/gco:Distance
```
**Unit**
```
gmd:identificationInfo/*/gmd:spatialResolution/*/gmd:distance/gco:Distance/@uom
```

# 
### Graphic Overview
```
gmd:identificationInfo/*/gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString
```
