# Manage Resources

In the metadata, resources are information about how to access the data (download link, OGC geoservice,...) 
and other general information (URL to website,...).
Resources are in the section `<gmd:distributionInfo>` inside the tag :
```
che:CHE_MD_Metadata/gmd:distributionInfo/gmd:transferOptions/gmd:MD_DigitalTransferOptions
```
If it's an online resource (can be an offline resource if the data are stored on physical support, e.g. USB stick, external HD,...)
it is packed inside the tags `<gmd:onLine><gmd:CI_OnlineResource>`

---
### Requirements
This script runs on python 3. Following packages are needed :
* requests
* urllib3
* lxml
* psycopg2
* python-dotenv
---
### Installation
Clone the repo anywhere you like. At the root folder, import the `manage_ressource.py` python module.

---
### Usage
#### Import
```python
import manage_ressource
```
#### Add OGC geoservice (WMS/WFS/WMTS) layer as online resources
1) First initiate the service's type and endpoint and reads the service

```python
resource = manage_ressource.ManageOGCResource(env="int")  # env -> str (default = 'int'), can be set to 'prod' to work on the production environment of geocat

# This method reads the getCapabilities of the service and store all layer ID and Title in 5 languages (de, fr, it, en, rm)
resource.get_ogc_layers(service="wms", endpoint="https://wms.example.com")
```

```
Arguments:
  service: can be set to "wms", "wfs" or "wmts"
  endpoint: URL of the service's endpoint
```

2) Then, add the layers to the metadata

```python
resource.add_ogc_layers(uuid=uuid, layers_id=["layer_id_1", "layer_id_2"])
```

```
Arguments:
  uuid: metadata uuid to edit
  layers_id: list of layers id to add, raises an exception if they are not found in the given service
```

#### Delete OGC geoservice (WMS/WFS/WMTS) layer as online resources
1) First initiate the service's type and endpoint and reads the service

```python
resource = manage_ressource.ManageOGCResource(env="int")  # env -> str (default = 'int'), can be set to 'prod' to work on the production environment of geocat

# This method reads the getCapabilities of the service and store all layer ID and Title in 5 languages (de, fr, it, en, rm)
resource.get_ogc_layers(service="wms", endpoint="https://wms.example.com")
```

```
Arguments:
  service: can be set to "wms", "wfs" or "wmts"
  endpoint: URL of the service's endpoint
```

2) Then, delete the layers from the metadata

```python
resource.delete_ogc_layers(uuid=uuid, layers_id=["layer_id_1", "layer_id_2"])
```

```
Arguments:
  uuid: metadata uuid to edit
  layers_id: list of layers id to delete
```
#### Add OGC geoservice (WMS/WFS/WMTS) as online resources without specifying layers

```python
resource = manage_ressource.ManageOGCResource(env="int")  # env -> str (default = 'int'), can be set to 'prod' to work on the production environment of geocat

ogc.add_ogc_service(uuid=uuid, service="wms", endpoint="https://wms.example.com")
```

```
Arguments:
  uuid: metadata uuid to edit
  service: can be set to "wms", "wfs" or "wmts"
  endpoint: URL of the service's endpoint
```
#### Delete OGC geoservice (WMS/WFS/WMTS) as online resources without specifying layers

```python
resource = manage_ressource.ManageOGCResource(env="int")  # env -> str (default = 'int'), can be set to 'prod' to work on the production environment of geocat

ogc.delete_ogc_service(uuid=uuid, service="wms", endpoint="https://wms.example.com")
```

```
Arguments:
  uuid: metadata uuid to edit
  service: can be set to "wms", "wfs" or "wmts"
  endpoint: URL of the service's endpoint
```
