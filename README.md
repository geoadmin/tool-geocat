# Geocat scripts and tools
Scripts and tools for the (meta)data management of geocat.ch. This does not contain the geocat.ch application !
### Tools

* **AddCoupledResource**

  **This is a test.** Automatically add the coupled ressources of a geoservice's metadata (one ressource per service's layer). 
  Read the getCapabilities to get all layers and another service to get the Geocat ID for each layer. Works  for the BGDI WMS.

* **add-opendataSwissPermalinkOnLineResource-to-geocatMDs**

  Add the opendataSwiss-Permalink as OnLineResource to geocat.ch MDs.

* **add-RESTfulAPIonLineResource-to-BGDI-MDs**

  Add the RESTfulAPI-Service as onLineResource to geocat.ch BGDI-MDs.
  
* **add-techLayerId-to-geocatIdentifier**

  Add techLayer-Id (-Name) as geocatIdentifier to geocat.ch MDs.
  
* **BGDI**

  Manage metadata from BGDI datasets. 

* **ClassLibrary**

  With this scripts, you have a helpfull library, which you can use in other projects.
  
* **BackupGenerator**

  Export all metadata, groups, users, thesaurus, subtemplates (reusable objects) and the unpublish report 
  and save them into a directory with a comprehensive structure.

* **export-xml-from-mef**

  Export a given list of metadata (UUID) from a MEF (metadata exchange format) archive (.zip) and save them in XML.

* **export-xml**

  Export a given list of metadata (UUID) from geocat and save them in XML.

* **get-groups-list**

  Get a csv list with all groups information.

* **get-list-from-search-request**

  Get a csv list of metadata found by given search criteria

* **get-users-list**

  Get a csv list with all users information.

* **get-wrong-thesauriUrl-in-PROD**

  Get all thesauriUrl from PROD, which has a link to INT
  
* **metadata-bacth-edit**

  Perform simple batch edits on a list of metadata (UUID).

* **metadata-replace-contact**

  Replace a given contact (subtemplate) in every metadata or in a defined single one.

* **metadata-subtemplate-xlink**

  Link all subtemplates (add the xlink in the XML) of a given list of metadata (UUID).

* **migration-the-legends-in-geocat**

  You can add png and pdf Legendfiles to MD-records as attachment
  This is a one time use Script! But it give an example, how to add files as attachment

* **replace-Http2Https-in-BGDI-MDs**

  Replace Http to Https in geocat.ch BGDI-MDs
  
* **thesaurus**

  Manage thesaurus and keywords in the metadata.
