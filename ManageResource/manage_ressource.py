import sys
import requests
from lxml import etree as ET
from geocat.geocat import GeocatAPI
from geocat import constants, utils

OGC_FORMAT = {
    "WMS": {
        "int": "local://srv/api/registries/entries/e3f7c60f-b40a-44b5-8221-7c66ff5d3787?lang=fre,ita,eng,ger,roh&amp;schema=iso19139.che",
        "prod": "local://srv/api/registries/entries/6c284fc7-fb99-4bb6-8e14-35466d8096d6?lang=fre,ita,eng,ger,roh&amp;schema=iso19139.che"
    },
    "WFS": {
        "int": "local://srv/api/registries/entries/80779add-0cf2-4c66-913b-0cf5ca7f645e?lang=fre,ita,eng,ger,roh&amp;schema=iso19139.che",
        "prod": "local://srv/api/registries/entries/80779add-0cf2-4c66-913b-0cf5ca7f645e?lang=fre,ita,eng,ger,roh&amp;schema=iso19139.che"
    },
    "WMTS": {
        "int": "local://srv/api/registries/entries/90b40abc-003d-4a1d-b9ca-1839a8c61a31?lang=fre,ita,eng,ger,roh&amp;schema=iso19139.che",
        "prod": "local://srv/api/registries/entries/84c21b8c-d491-47e9-a866-87b4767b206a?lang=fre,ita,eng,ger,roh&amp;schema=iso19139.che"
    }
}


class ManageOGCResource:

    def __init__(self, api: object = None, env: str = "int"):

        if api is None:
            self.__api = GeocatAPI(env=env)
        else:
            self.__api = api
        self.env = env
        self.service = None
        self.endpoint = None
        self.layers = None

    def __get_ogc_xpath(self, metadata: bytes, layer_id: str = None) -> list:
        """
        Get the xpath of the given geoservice layer. If no layers id are given, 
        get the geoservice xpath. Returns a list of xpath (in case of duplicated resources)
        """

        root = ET.fromstring(metadata)
        tree = ET.ElementTree(root)

        xpath = list()

        for tag in tree.findall("./gmd:distributionInfo//gmd:transferOptions//gmd:onLine",
                                    namespaces=constants.NS):

            if tag.find(".//gmd:linkage/gmd:URL", namespaces=constants.NS) is None:
                continue
            url = tag.find(".//gmd:linkage/gmd:URL", namespaces=constants.NS).text

            if tag.find(".//gmd:protocol/gco:CharacterString", namespaces=constants.NS) is None:
                continue
            protocol = tag.find(".//gmd:protocol/gco:CharacterString", namespaces=constants.NS).text

            if url is None or protocol is None:
                continue

            name = tag.find(".//gmd:name/gco:CharacterString", namespaces=constants.NS)
            if name is not None:
                name = tag.find(".//gmd:name/gco:CharacterString", namespaces=constants.NS).text

            if layer_id is None:
                if url.split("?")[0] == self.endpoint and \
                protocol.split(":")[-1].upper() == self.service and name is None:

                    xpath.append(tree.getpath(tag))

            else:
                if url.split("?")[0] == self.endpoint and \
                protocol.split(":")[-1].upper() == self.service and name == layer_id.split(":")[-1]:

                    xpath.append(tree.getpath(tag))

        return xpath

    def __create_resource_container(self, metadata: bytes) -> list:
        """
        Creates all necessary tags and distribution format for the given metadata
        to add new OGC online resource.

        Returns a list for the batch editing API's body
        """

        body = list()

        root = ET.fromstring(metadata)

        # Add distribution element if doesn't exist
        if root.find("./gmd:distributionInfo", namespaces=constants.NS) is None:

            body += [
                {
                    "xpath": "/che:CHE_MD_Metadata/",
                    "value": f"<gn_add>{constants.XML_TAG['distributionInfo']}</gn_add>"
                },
                # case if metadata is iso19139 and not iso19139che
                {
                    "xpath": "/gmd:MD_Metadata/",
                    "value": f"<gn_add>{constants.XML_TAG['distributionInfo']}</gn_add>"
                }
            ]

        # Add corresponding OGC format if doesn't exist
        ogc_format = False
        for tag in root.findall("./gmd:distributionInfo[1]//gmd:distributionFormat",
                                    namespaces=constants.NS):

            if tag.attrib["{http://www.w3.org/1999/xlink}href"].split("?")[0] == \
                            OGC_FORMAT[self.service][self.env].split("?")[0]:
                ogc_format = True
                break

        if not ogc_format:

            body.append(
                {
                    "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution",
                    "value": "<gn_add><gmd:distributionFormat" \
                    " xmlns:gmd='http://www.isotc211.org/2005/gmd'" \
                    " xmlns:xlink='http://www.w3.org/1999/xlink'" \
                    f" xlink:href='{OGC_FORMAT[self.service][self.env]}'>" \
                    "</gmd:distributionFormat></gn_add>"
                }
            )

        # Add digital transfer options element if doesn't exist
        if root.find("./gmd:distributionInfo[1]//gmd:transferOptions/gmd:MD_DigitalTransferOptions",
                        namespaces=constants.NS) is None:

            body.append(
                {
                    "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution",
                    "value": f"<gn_add>{constants.XML_TAG['transferOptions']}</gn_add>"
                }
            )

        return body

    def __create_resource_layer(self, metadata: bytes, layer_id: str) -> dict:
        """
        Creates an xpath-value pair for the batch editing API.
        The value contains an online resource XML element for an OGC geoservice layer.

        The layer name will have all the languages set up in the given metadata.
        """

        if layer_id not in self.layers:
            print(utils.warningred(f"The Layer ID : {layer_id} hasn't been found in the OGC service"))
            return None

        languages = self.__api.get_metadata_languages(metadata=metadata)

        root = ET.fromstring(constants.XML_TAG['onLine_layer'])

        # Add the URL endpoint only for the main language
        tag = root.find(".//gmd:linkage/che:PT_FreeURL", namespaces=constants.NS)

        ET.SubElement(tag, "{http://www.geocat.ch/2008/che}URLGroup")
        ET.SubElement(tag[0], "{http://www.geocat.ch/2008/che}LocalisedURL",
                        attrib={"locale": f'#{languages[0]}'})

        if self.service == "WMS" or self.service == "WFS":
            tag[0][0].text = f"{self.endpoint}?SERVICE={self.service}&REQUEST=GetCapabilities"
        else:
            tag[0][0].text = self.endpoint

        # add protocol
        root.find(".//gmd:protocol/gco:CharacterString",
                    namespaces=constants.NS).text = f"OGC:{self.service}"

        # add layer id only for the main language
        tag = root.find(".//gmd:name/gmd:PT_FreeText", namespaces=constants.NS)

        ET.SubElement(tag, "{http://www.isotc211.org/2005/gmd}textGroup")
        ET.SubElement(tag[0], "{http://www.isotc211.org/2005/gmd}LocalisedCharacterString",
                        attrib={"locale": f'#{languages[0]}'})

        tag[0][0].text = layer_id.split(":")[-1]

        # add layer description
        tag = root.find(".//gmd:description/gmd:PT_FreeText", namespaces=constants.NS)

        for lang in languages:
            ET.SubElement(tag, "{http://www.isotc211.org/2005/gmd}textGroup")
            ET.SubElement(tag[-1], "{http://www.isotc211.org/2005/gmd}LocalisedCharacterString",
                attrib={"locale": f'#{lang}'})

            tag[-1][0].text = self.layers[layer_id][lang.lower()]

        return {
            "xpath": "./gmd:distributionInfo[1]//gmd:transferOptions[1]/gmd:MD_DigitalTransferOptions",
            "value": f"<gn_add>{ET.tostring(root, encoding='utf-8').decode()}</gn_add>".replace('"', "'")
            }

    def __create_resource_service(self, metadata: bytes) -> dict:
        """
        Creates an xpath-value pair for the batch editing API.
        The value contains an online resource XML element for an OGC geoservice.
        """

        languages = self.__api.get_metadata_languages(metadata=metadata)

        root = ET.fromstring(constants.XML_TAG['onLine_service'])

        # Add the URL endpoint only for the main language
        tag = root.find(".//gmd:linkage/che:PT_FreeURL", namespaces=constants.NS)

        ET.SubElement(tag, "{http://www.geocat.ch/2008/che}URLGroup")
        ET.SubElement(tag[0], "{http://www.geocat.ch/2008/che}LocalisedURL",
                        attrib={"locale": f'#{languages[0]}'})

        if self.service == "WMS" or self.service == "WFS":
            tag[0][0].text = f"{self.endpoint}?SERVICE={self.service}&REQUEST=GetCapabilities"
        else:
            tag[0][0].text = self.endpoint

        # add protocol
        root.find(".//gmd:protocol/gco:CharacterString",
                    namespaces=constants.NS).text = f"OGC:{self.service}"

        return {
            "xpath": "./gmd:distributionInfo[1]//gmd:transferOptions[1]/gmd:MD_DigitalTransferOptions",
            "value": f"<gn_add>{ET.tostring(root, encoding='utf-8').decode()}</gn_add>".replace('"', "'")
            }

    def __cleanup_format(self, uuid: str):
        """
        Clean up the OGC format in the given metadata.

        If the OGC format according to to given service is not used by any resource but it is set up
        as distribution format, the latter is deleted.
        """
        metadata = self.__api.get_metadata_from_mef(uuid=uuid)

        if metadata is None:
            raise Exception("No metadata found")

        root = ET.fromstring(metadata)
        tree = ET.ElementTree(root)

        tags_to_delete = list()
        body = list()

        for tag in tree.findall("./gmd:distributionInfo[1]//gmd:transferOptions//gmd:onLine//gmd:protocol/gco:CharacterString",
                        namespaces=constants.NS):

            if tag.text.split(":")[-1] == self.service:
                return

        for tag in tree.findall("./gmd:distributionInfo[1]//gmd:distributionFormat",
                                    namespaces=constants.NS):

            if tag.attrib["{http://www.w3.org/1999/xlink}href"].split("?")[0] == \
                            OGC_FORMAT[self.service][self.env].split("?")[0]:

                tags_to_delete.append(tree.getpath(tag))

        if len(tags_to_delete) > 0:
            for tag in reversed(tags_to_delete):

                body.append(
                    {
                        "xpath": tag,
                        "value": "<gn_delete></gn_delete>"
                    }
                )

            response = self.__api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)
            if not utils.process_ok(response):
                raise Exception("Cleanup format unsuccessfull")

    def __cleanup_distribution(self, uuid: str):
        """If distribution is empty, delete the entire tag"""

        metadata = self.__api.get_metadata_from_mef(uuid=uuid)

        if metadata is None:
            raise Exception("No metadata found")

        root = ET.fromstring(metadata)

        if len(root.find("./gmd:distributionInfo[1]/gmd:MD_Distribution",
                        namespaces=constants.NS).getchildren()) == 0:

            body = [
                {
                    "xpath": "./gmd:distributionInfo[1]",
                    "value": "<gn_delete></gn_delete>"
                }
            ]

            response = self.__api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)
            if not utils.process_ok(response):
                raise Exception("Cleanup distribution unsuccessfull")

    def get_ogc_layers(self, service: str, endpoint: str):
        """Connects to OGC web service and fetch all available layers"""      
        
        self.service = service.upper()
        self.endpoint = endpoint.split('?')[0]
        self.layers = dict()

        lang = ("de", "fr", "it", "en", "rm")

        if self.service == "WMS" or self.service == "WFS":
            url = f"{self.endpoint}?SERVICE={self.service}&REQUEST=GetCapabilities&"
        elif self.service == "WMTS":
            url = f"{self.endpoint}?"
        else:
            print(utils.warningred("The parameter service is not valid (wms, wfs, wmts)"))
            sys.exit()

        if self.service == "WMS":
            layer_xpath = ".//*[local-name()='Layer']"
            id_xpath = "./*[local-name()='Name']"
            title_xpath = "./*[local-name()='Title']"
        elif self.service == "WFS":
            layer_xpath = ".//*[local-name()='FeatureType']"
            id_xpath = "./*[local-name()='Name']"
            title_xpath = "./*[local-name()='Title']"
        elif self.service == "WMTS":
            layer_xpath = ".//*[local-name()='Layer']"
            id_xpath = "./*[local-name()='Identifier']"
            title_xpath = "./*[local-name()='Title']"

        for l in lang:

            response = requests.get(f"{url}lang={l}", proxies=self.__api.session.proxies)

            if response.status_code != 200:
                continue

            root = ET.fromstring(response.content)
            for layer in root.xpath(layer_xpath):
                id = layer.xpath(id_xpath)[0].text

                if id not in self.layers:
                    self.layers[id] = dict()

                name = layer.xpath(title_xpath)[0].text

                self.layers[id][l] = name

    def add_ogc_layers(self, uuid: str, layers_id: list):
        """
        Add one or more OGC geoservice layers to the given metadata. Layers are given with their
        ID in form of a list.
        """

        if self.service is None:
            raise Exception("No service found ! The method get_ogc_service must be run")

        metadata = self.__api.get_metadata_from_mef(uuid=uuid)

        if metadata is None:
            raise Exception("No metadata found")

        body = self.__create_resource_container(metadata=metadata)

        # Add OGC webservice layers
        has_layer = False
        layer_already_exist = True
        for layer in layers_id:

            if len(self.__get_ogc_xpath(metadata=metadata, layer_id=layer)) == 0:
                layer_already_exist = False
                if self.__create_resource_layer(metadata=metadata, layer_id=layer) is not None:
                    body.append(self.__create_resource_layer(metadata=metadata, layer_id=layer))
                    has_layer = True

        if layer_already_exist:
            raise Exception("Layers ID already exist")

        if not has_layer:
            raise Exception("No layers ID found in the OGC geoservice")

        response = self.__api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)
        if not utils.process_ok(response):
            raise Exception("OGC Layers unsucessfully added")

    def add_ogc_service(self, uuid: str, service: str, endpoint: str):
        """Add an OGC geoservice to the given metadata."""
        self.service = service.upper()
        self.endpoint = endpoint.split('?')[0]

        metadata = self.__api.get_metadata_from_mef(uuid=uuid)

        if metadata is None:
            raise Exception("No metadata found")

        body = self.__create_resource_container(metadata=metadata)

        if len(self.__get_ogc_xpath(metadata=metadata)) == 0:
            body.append(self.__create_resource_service(metadata=metadata))
        else:
            raise Exception("OGC service already exists")     

        response = self.__api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)
        if not utils.process_ok(response):
            raise Exception("OGC service unsucessfully added")

    def delete_ogc_layers(self, uuid: str, layers_id: list):
        """
        Delete one or more OGC geoservice layers from the given metadata. Layers are given
        with their ID in form of a list.
        """

        if self.service is None:
            raise Exception("No service found ! The method get_ogc_service must be run")

        metadata = self.__api.get_metadata_from_mef(uuid=uuid)

        if metadata is None:
            raise Exception("No metadata found")

        root = ET.fromstring(metadata)

        online_tags = list()
        body = list()

        no_layer = True
        for layer in layers_id:
            for xpath in self.__get_ogc_xpath(metadata=metadata, layer_id=layer):
                online_tags.append(xpath)
                no_layer = False

        if no_layer:
            raise Exception("No layers found in the metadata")

        for tag in reversed(online_tags):
            body.append(
                {
                    "xpath": tag,
                    "value": "<gn_delete></gn_delete>"
                }
            )

        transfer_tag = "/".join(online_tags[0].split("/")[:-1])

        if len(root.xpath(transfer_tag,
                            namespaces=constants.NS)[0].getchildren()) == len(online_tags):
            body.append(
                {
                    "xpath": "/".join(transfer_tag.split("/")[:-1]),
                    "value": "<gn_delete></gn_delete>"
                }
            )

        response = self.__api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)
        if not utils.process_ok(response):
            raise Exception("OGC Layers unsucessfully deleted")

        self.__cleanup_format(uuid=uuid)
        self.__cleanup_distribution(uuid=uuid)

    def delete_ogc_service(self, uuid: str, service: str, endpoint: str):
        """Delete OGC geoservice from the given metadata."""

        self.service = service.upper()
        self.endpoint = endpoint.split('?')[0]

        metadata = self.__api.get_metadata_from_mef(uuid=uuid)

        if metadata is None:
            raise Exception("No metadata found")

        root = ET.fromstring(metadata)

        body = list()
        online_tags = self.__get_ogc_xpath(metadata=metadata)

        if len(online_tags) == 0:
            raise Exception("No service found in the metadata")

        for tag in reversed(online_tags):
            body.append(
                {
                    "xpath": tag,
                    "value": "<gn_delete></gn_delete>"
                }
            )

        transfer_tag = "/".join(online_tags[0].split("/")[:-1])

        if len(root.xpath(transfer_tag,
                            namespaces=constants.NS)[0].getchildren()) == len(online_tags):
            body.append(
                {
                    "xpath": "/".join(transfer_tag.split("/")[:-1]),
                    "value": "<gn_delete></gn_delete>"
                }
            )

        response = self.__api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)
        if not utils.process_ok(response):
            raise Exception("OGC service unsucessfully deleted")

        self.__cleanup_format(uuid=uuid)
        self.__cleanup_distribution(uuid=uuid)

    def delete_all_ogc(self, uuid: str):
        """Delete all OGC online resources from the given metadata."""

        metadata = self.__api.get_metadata_from_mef(uuid=uuid)

        if metadata is None:
            raise Exception("No metadata found")

        root = ET.fromstring(metadata)
        tree = ET.ElementTree(root)

        xpath = list()

        for tag in tree.findall("./gmd:distributionInfo//gmd:transferOptions//gmd:onLine",
                                    namespaces=constants.NS):

            if tag.find(".//gmd:protocol/gco:CharacterString", namespaces=constants.NS) is None:
                continue

            protocol = tag.find(".//gmd:protocol/gco:CharacterString", namespaces=constants.NS).text

            if protocol.split(":")[0] == "OGC":
                xpath.append(tree.getpath(tag))

        if len(xpath) == 0:
            raise Exception("No OGC resource found in the metadata")

        body = list()

        for tag in reversed(xpath):
            body.append(
                {
                    "xpath": tag,
                    "value": "<gn_delete></gn_delete>"
                }
            )

        transfer_tag = "/".join(xpath[0].split("/")[:-1])

        if len(root.xpath(transfer_tag,
                            namespaces=constants.NS)[0].getchildren()) == len(xpath):
            body.append(
                {
                    "xpath": "/".join(transfer_tag.split("/")[:-1]),
                    "value": "<gn_delete></gn_delete>"
                }
            )

        response = self.__api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)
        if not utils.process_ok(response):
            raise Exception("OGC resources unsucessfully deleted")

        for service in OGC_FORMAT:
            self.service = service
            self.__cleanup_format(uuid=uuid)
        self.__cleanup_distribution(uuid=uuid)
