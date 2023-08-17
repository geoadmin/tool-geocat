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
