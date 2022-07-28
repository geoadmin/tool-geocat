from datetime import datetime
import requests
from lxml import etree as ET
from geocat.geocat import GeocatAPI
from geocat import constants, utils

XML = "<gmd:descriptiveKeywords xmlns:gmd='http://www.isotc211.org/2005/gmd' "\
    "xmlns:xlink='http://www.w3.org/1999/xlink' " \
    "xlink:href='local://srv/api/registries/vocabularies/keyword?" \
    "skipdescriptivekeywords=true&amp;thesaurus=thesaurus_id&amp;" \
    "id=keyword_id&amp;lang=fre,ita,eng,ger'></gmd:descriptiveKeywords>"


class ManageKeyword:
    """
    Manage keywords

    Attributes :
        env : indicating the geocat's environment to work with, 'int' or 'prod', default = 'int'.

    Methods :
        add_keyword : add a new keyword
        delete_keyword : delete keyword
    """

    def __init__(self, env: str = "int") -> None:

        self.api = GeocatAPI(env=env)

    def __keyword_xlink_check(self, metadata: bytes) -> bool:
        """Check if metadata has non shared object keyword (no xlink)"""

        xml_root = ET.fromstring(metadata)
        tags = xml_root.findall(".//gmd:descriptiveKeywords", namespaces=constants.NS)

        for tag in tags:

            if "{http://www.w3.org/1999/xlink}href" not in tag.attrib:
                return False
        return True

    def __keyword_check(self, metadata: bytes, keyword_id: str) -> bool:
        """
        Check if keyword already exists in metadata

        Return the xpath of the <gmd:descriptiveKeywords> tag containing the
        keyword when exists. Returns False when not existing.
        """

        xml_root = ET.fromstring(metadata)
        tree = tree = ET.ElementTree(xml_root)

        tags = tree.findall(".//gmd:descriptiveKeywords", namespaces=constants.NS)

        for tag in tags:

            if "{http://www.w3.org/1999/xlink}href" not in tag.attrib:
                continue

            attributes = requests.utils.unquote(tag.attrib["{http://www.w3.org/1999/xlink}href"])
            for parameter in attributes.split("?")[-1].split("&"):

                if parameter.split("=")[0] == "id":
                    for existing_keyword_id in parameter.split("=")[-1].split(","):
                        if existing_keyword_id == keyword_id:

                            return tree.getpath(tag)
        return False

    def __get_thesaurus_from_keyword(self, metadata: bytes, keyword_id: str) -> str:
        """Get thesaurus ID containing the given keyword"""

        xml_root = ET.fromstring(metadata)

        tags = xml_root.findall(".//gmd:descriptiveKeywords", namespaces=constants.NS)

        for tag in tags:

            if "{http://www.w3.org/1999/xlink}href" not in tag.attrib:
                continue

            attributes = requests.utils.unquote(tag.attrib["{http://www.w3.org/1999/xlink}href"])
            for parameter in attributes.split("?")[-1].split("&"):

                if parameter.split("=")[0] == "id":
                    for existing_keyword_id in parameter.split("=")[-1].split(","):
                        if existing_keyword_id == keyword_id:

                            for parameter in attributes.split("?")[-1].split("&"):
                                if parameter.split("=")[0] == "thesaurus":
                                    return parameter.split("=")[1]

        return False

    def __thesaurus_check(self, metadata: bytes, thesaurus_id: str):
        """
        Check if thesaurus already exists in metadata.

        Return the xpath of the <gmd:descriptiveKeywords> tag containing the
        thesaurus when exists. Returns False when not existing.
        """

        xml_root = ET.fromstring(metadata)
        tree = tree = ET.ElementTree(xml_root)

        tags = tree.findall(".//gmd:descriptiveKeywords", namespaces=constants.NS)

        for tag in tags:

            if "{http://www.w3.org/1999/xlink}href" not in tag.attrib:
                continue

            attributes = requests.utils.unquote(tag.attrib["{http://www.w3.org/1999/xlink}href"])

            if f"thesaurus={thesaurus_id}" in attributes.split("?")[-1].split("&"):
                return tree.getpath(tag)

        return False

    def __get_existing_keyword(self, metadata: bytes, tag_xpath: str) -> list:
        """
        Get keywords from <gmd:descriptiveKeywords> tag.

        Return a list of keywords id.
        """

        xml_root = ET.fromstring(metadata)
        tag = xml_root.xpath(tag_xpath, namespaces=constants.NS)[0]

        keyword_id = list()

        if "{http://www.w3.org/1999/xlink}href" not in tag.attrib:
            return keyword_id

        attributes = requests.utils.unquote(tag.attrib["{http://www.w3.org/1999/xlink}href"])

        for parameter in attributes.split("?")[-1].split("&"):
            if parameter.split("=")[0] == "id":
                keyword_id = parameter.split("=")[-1]
                keyword_id = keyword_id.split(",")

        return keyword_id

    def add_keyword(self, uuids: list, keyword_id: str, thesaurus_id: str,
                    backup: bool = True) -> None:
        """
        Add a keyword to a list of metadata.

        Args:
            uuids : a list of metadata uuid
            keyword_id : the ID of the keyword to add
            thesaurus_id : the thesaurus ID where the keyword comes from
            backup : True or False. If True, backup all metadata before changes are made
        """

        if backup is True:
            self.api.backup_metadata(uuids)

        logger = utils.setup_logger(f"AddKeyword_{datetime.now().strftime('%Y%m%d-%H%M%S')}")

        print("Add Keyword : ", end="\r")

        successful = 0
        unsuccessful = 0
        already_existing = 0

        count = 0
        for uuid in uuids:

            print(f"Add Keyword : {round((count / len(uuids)) * 100, 1)}%", end="\r")
            count += 1

            metadata = self.api.get_metadata_from_mef(uuid)

            if metadata is None:
                logger.error(f"{count}/{len(uuids)} - {uuid} - Couldn't fetch metadata")
                unsuccessful += 1
                continue

            if not self.__keyword_xlink_check(metadata):
                logger.warning(f"{count}/{len(uuids)} - {uuid} - At least 1 keyword has missing xlink")

            if self.__keyword_check(metadata=metadata, keyword_id=keyword_id):
                logger.info(f"{count}/{len(uuids)} - {uuid} - Keyword already exists")
                already_existing += 1
                continue

            if self.__thesaurus_check(metadata=metadata, thesaurus_id=thesaurus_id):
                xpath = self.__thesaurus_check(metadata=metadata, thesaurus_id=thesaurus_id)
                existing_keywords = self.__get_existing_keyword(metadata=metadata, tag_xpath=xpath)

                xml_to_add = XML.replace("thesaurus_id", thesaurus_id)

                if len(existing_keywords) == 0:
                    xml_to_add = xml_to_add.replace("keyword_id", keyword_id)
                else:
                    xml_to_add = xml_to_add.replace("keyword_id",
                                                    f"{','.join(existing_keywords)},{keyword_id}")

                body = [{
                    "xpath": xpath,
                    "value": "<gn_delete></gn_delete>",
                }]

                # If there are many <gmd:descriptiveKeywords> tags, add it at first position
                if xpath.endswith("]"):
                    body.append({
                    "xpath": ".//gmd:identificationInfo//gmd:descriptiveKeywords[1]",
                    "value": f"<gn_add>{xml_to_add}</gn_add>",
                    })

                # If only one <gmd:descriptiveKeywords> tags, add it at parent level
                else:
                    body.append({
                    "xpath": ".//gmd:identificationInfo[1]/*",
                    "value": f"<gn_add>{xml_to_add}</gn_add>",
                    })

            else:
                xml_to_add = XML.replace("thesaurus_id", thesaurus_id)
                xml_to_add = xml_to_add.replace("keyword_id", keyword_id)

                body = [{
                "value": f"<gn_add>{xml_to_add}</gn_add>",
                }]

                xml_root = ET.fromstring(metadata)
                # If there are many <gmd:descriptiveKeywords> tags, add it at first position
                if len(xml_root.findall(".//gmd:descriptiveKeywords", namespaces=constants.NS)) > 0:
                    body[0]["xpath"] = ".//gmd:identificationInfo//gmd:descriptiveKeywords[1]"

                # If only one <gmd:descriptiveKeywords> tags, add it at parent level
                else:
                    body[0]["xpath"] = ".//gmd:identificationInfo[1]/*"

            response = self.api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)

            if utils.process_ok(response):
                logger.info(f"{count}/{len(uuids)} - {uuid} - Keyword successfuly added")
                successful += 1
            else:
                logger.error(f"{count}/{len(uuids)} - {uuid} - Keyword unsuccessfuly added")
                unsuccessful += 1

        print(f"Add Keyword : {utils.okgreen('Done')}")
        print(f"Keyword successfuly added: {utils.okgreen(successful)}")
        print(f"Keyword already existing: {utils.okgreen(already_existing)}")
        print(f"Keyword unsuccessfuly added: {utils.warningred(unsuccessful)}")

    def delete_keyword(self, uuids: list, keyword_id: str, backup: bool = True) -> None:
        """
        Delete a keyword from a list of metadata.

        Args:
            uuids : a list of metadata uuid
            keyword_id : the ID of the keyword to delete
            backup : True or False. If True, backup all metadata before changes are made
        """

        if backup is True:
            self.api.backup_metadata(uuids)

        logger = utils.setup_logger(f"DeleteKeyword_{datetime.now().strftime('%Y%m%d-%H%M%S')}")

        print("Delete Keyword : ", end="\r")

        successful = 0
        unsuccessful = 0
        not_existing = 0

        count = 0
        for uuid in uuids:

            print(f"Delete Keyword : {round((count / len(uuids)) * 100, 1)}%", end="\r")
            count += 1

            metadata = self.api.get_metadata_from_mef(uuid)

            if metadata is None:
                logger.error(f"{count}/{len(uuids)} - {uuid} - Couldn't fetch metadata")
                unsuccessful += 1
                continue

            if not self.__keyword_xlink_check(metadata):
                logger.warning(f"{count}/{len(uuids)} - {uuid} - At least 1 keyword has missing xlink")

            if not self.__keyword_check(metadata=metadata, keyword_id=keyword_id):
                logger.info(f"{count}/{len(uuids)} - {uuid} - Keyword doesn't exist")
                not_existing += 1
                continue

            xpath = self.__keyword_check(metadata, keyword_id)
            existing_keywords = self.__get_existing_keyword(metadata, xpath)
            thesaurus_id = self.__get_thesaurus_from_keyword(metadata, keyword_id)

            body = [{
                "xpath": xpath,
                "value": "<gn_delete></gn_delete>",
            }]

            if len(existing_keywords) > 1:
                existing_keywords.remove(keyword_id)

                xml_to_add = XML.replace("thesaurus_id", thesaurus_id)
                xml_to_add = xml_to_add.replace("keyword_id", ",".join(existing_keywords))

                body.append({
                    "xpath": ".//gmd:identificationInfo[1]/*",
                    "value": f"<gn_add>{xml_to_add}</gn_add>",
                })

            response = self.api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)

            if utils.process_ok(response):
                logger.info(f"{count}/{len(uuids)} - {uuid} - Keyword successfuly deleted")
                successful += 1
            else:
                logger.error(f"{count}/{len(uuids)} - {uuid} - Keyword unsuccessfuly deleted")
                unsuccessful += 1

        print(f"Delete Keyword : {utils.okgreen('Done')}")
        print(f"Keyword successfuly deleted: {utils.okgreen(successful)}")
        print(f"Keyword not existing: {utils.okgreen(not_existing)}")
        print(f"Keyword unsuccessfuly deleted: {utils.warningred(unsuccessful)}")
