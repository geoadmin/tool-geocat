from lxml import etree as ET
from geocat.geocat import GeocatAPI
from geocat import constants, utils

class ManageContact:
    """
    Manage contacts

    Attributes :
        env : indicating the geocat's environment to work with, 'int' or 'prod', default = 'int'.
    """

    def __init__(self, env: str = "int") -> None:

        self.api = GeocatAPI(env)

    def get_md_contact_xlink(self, uuid: str) -> str:
        """Get the first contact xlink for the metadata"""

        metadata = self.api.get_metadata_from_mef(uuid=uuid)
        if metadata is None:
            return None

        root = ET.fromstring(metadata)

        tag = root.find("./gmd:contact", namespaces=constants.NS)

        try:
            contact = tag.attrib["{http://www.w3.org/1999/xlink}href"]

        except KeyError:
            print(utils.warningred("Metadata contact is not a shared object"))
            return None

        return contact

    def replace_ressource_contact(self, uuid: str, contact_xlink: str) -> object:
        """
        Replace ressource contact by given contact.

        If there are many ressource contacts, they are all erased and replaced by the only one given
        """
        if "&amp;" not in contact_xlink:
            contact_xlink = contact_xlink.replace("&", "&amp;")

        value_to_add = f"<gmd:pointOfContact xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:xlink='http://www.w3.org/1999/xlink' xlink:href='{contact_xlink}'></gmd:pointOfContact>"

        body = [
            {
                "xpath": ".//gmd:identificationInfo//gmd:pointOfContact",
                "value" : "<gn_delete></gn_delete>",
            },
            {
                "xpath": ".//gmd:identificationInfo[1]/*",
                "value" : f"<gn_add>{value_to_add}</gn_add>",
            },
        ]

        response = self.api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)

        if utils.process_ok(response):
            print(utils.okgreen("Ressource Contact successfuly replaced"))
            return response
        else:
            print(utils.warningred("Ressource Contact unsuccessfuly replaced"))
            return response

    def replace_md_contact(self, uuid: str, contact_xlink: str) -> object:
        """
        Replace metadata contact by given contact.

        If there are many metadata contacts, they are all erased and replaced by the only one given
        """

        if "&amp;" not in contact_xlink:
            contact_xlink = contact_xlink.replace("&", "&amp;")

        value_to_add = f"<gmd:contact xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:xlink='http://www.w3.org/1999/xlink' xlink:href='{contact_xlink}'></gmd:contact>"

        body = [
            {
                "xpath": "./gmd:contact",
                "value" : "<gn_delete></gn_delete>",
            },
            {
                "xpath": "/che:CHE_MD_Metadata/",
                "value" : f"<gn_add>{value_to_add}</gn_add>",
            },
            # case if metadata is iso19139 and not iso19139che
            {
                "xpath": "/gmd:MD_Metadata/",
                "value" : f"<gn_add>{value_to_add}</gn_add>",
            },
        ]

        response = self.api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)

        if utils.process_ok(response):
            print(utils.okgreen("Metadata Contact successfuly replaced"))
            return response
        else:
            print(utils.warningred("Metadata Contact unsuccessfuly replaced"))
            return response
