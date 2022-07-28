from datetime import datetime
from lxml import etree as ET
from geocat.geocat import GeocatAPI
from geocat import constants, utils

ODS_OPEN = "https://opendata.swiss/en/terms-of-use/#terms_open"
ODS_OPENBY = "https://opendata.swiss/en/terms-of-use/#terms_by"
ODS_OPENASK = "https://opendata.swiss/en/terms-of-use/#terms_ask"
ODS_OPENBYASK = "https://opendata.swiss/en/terms-of-use/#terms_by_ask"

ODS_LEGAL_CONSTRAINTS = {
    ODS_OPEN:  "<gmd:otherConstraints xsi:type='gmd:PT_FreeText_PropertyType' xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:gmx='http://www.isotc211.org/2005/gmx' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>" \
                  "<gmx:Anchor xlink:href='https://opendata.swiss/en/terms-of-use/#terms_open'></gmx:Anchor>" \
                  "<gmd:PT_FreeText>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#FR'>Opendata OPEN: Utilisation libre.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#IT'>Opendata OPEN: Libero utilizzo.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#EN'>Opendata OPEN: Open use.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#DE'>Opendata OPEN: Freie Nutzung.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                  "</gmd:PT_FreeText>" \
               "</gmd:otherConstraints>",
    ODS_OPENBY: "<gmd:otherConstraints xsi:type='gmd:PT_FreeText_PropertyType' xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:gmx='http://www.isotc211.org/2005/gmx' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>" \
                  "<gmx:Anchor xlink:href='https://opendata.swiss/en/terms-of-use/#terms_by'></gmx:Anchor>" \
                  "<gmd:PT_FreeText>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#FR'>Opendata BY: Utilisation libre. Obligation d’indiquer la source.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#IT'>Opendata BY: Libero utilizzo. Indicazione della fonte obbligatoria.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#EN'>Opendata BY: Open use. Must provide the source.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#DE'>Opendata BY: Freie Nutzung. Quellenangabe ist Pflicht.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                  "</gmd:PT_FreeText>" \
               "</gmd:otherConstraints>",
    ODS_OPENASK: "<gmd:otherConstraints xsi:type='gmd:PT_FreeText_PropertyType' xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:gmx='http://www.isotc211.org/2005/gmx' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>" \
                  "<gmx:Anchor xlink:href='https://opendata.swiss/en/terms-of-use/#terms_ask'></gmx:Anchor>" \
                  "<gmd:PT_FreeText>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#FR'>Opendata ASK: Utilisation libre. Utilisation à des fins commerciales uniquement avec l’autorisation du fournisseur des données.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#IT'>Opendata ASK: Libero utilizzo. Utilizzo a fini commerciali ammesso soltanto previo consenso del titolare dei dati.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#EN'>Opendata ASK: Open use. Use for commercial purposes requires permission of the data owner.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#DE'>Opendata ASK: Freie Nutzung. Kommerzielle Nutzung nur mit Bewilligung des Datenlieferanten zulässig.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                  "</gmd:PT_FreeText>" \
               "</gmd:otherConstraints>",
    ODS_OPENBYASK: "<gmd:otherConstraints xsi:type='gmd:PT_FreeText_PropertyType' xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:gmx='http://www.isotc211.org/2005/gmx' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>" \
                  "<gmx:Anchor xlink:href='https://opendata.swiss/en/terms-of-use/#terms_by_ask'></gmx:Anchor>" \
                  "<gmd:PT_FreeText>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#FR'>Opendata BY ASK: Utilisation libre. Obligation d’indiquer la source. Utilisation commerciale uniquement avec l’autorisation du fournisseur des données.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#IT'>Opendata BY ASK: Libero utilizzo. Indicazione della fonte obbligatoria. Utilizzo a fini commerciali ammesso soltanto previo consenso del titolare dei dati.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#EN'>Opendata BY ASK: Open use. Must provide the source. Use for commercial purposes requires permission of the data owner.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                     "<gmd:textGroup>" \
                        "<gmd:LocalisedCharacterString locale='#DE'>Opendata BY ASK: Freie Nutzung. Quellenangabe ist Pflicht. Kommerzielle Nutzung nur mit Bewilligung des Datenlieferanten zulässig.</gmd:LocalisedCharacterString>" \
                     "</gmd:textGroup>" \
                  "</gmd:PT_FreeText>" \
               "</gmd:otherConstraints>",
}

LEGAL_CONSTRAINTS_TAG = ("<che:CHE_MD_LegalConstraints xmlns:gmd='http://www.isotc211.org/2005/gmd' gco:isoType='gmd:MD_LegalConstraints' xmlns:che='http://www.geocat.ch/2008/che' xmlns:gco='http://www.isotc211.org/2005/gco'>", "</che:CHE_MD_LegalConstraints>")
RESOURCE_CONSTRAINTS_TAG = ("<gmd:resourceConstraints xmlns:gmd='http://www.isotc211.org/2005/gmd'><che:CHE_MD_LegalConstraints gco:isoType='gmd:MD_LegalConstraints' xmlns:che='http://www.geocat.ch/2008/che' xmlns:gco='http://www.isotc211.org/2005/gco'>", "</che:CHE_MD_LegalConstraints></gmd:resourceConstraints>")

class ODSConstraint:
    """
    Manage opendata.swiss legal constraints

    Attributes :
        env : indicating the geocat's environment to work with, 'int' or 'prod', default = 'int'.

    Methods :
        add_constraint : add a new ODS legal constraint
        delete_constraint : delete an ODS legal constraint
    """

    def __init__(self, env: str = "int") -> None:

        self.api = GeocatAPI(env)

    def __check_constraints(self, md: bytes) -> bool:
        """Check if the metadata already has ODS legal constraints information"""

        xml_root = ET.fromstring(md)

        for tag in xml_root.findall(".//gmd:resourceConstraints//gmd:otherConstraints/gmx:Anchor",
                                    namespaces=constants.NS):

            if tag.attrib["{http://www.w3.org/1999/xlink}href"] in [ODS_OPEN,
            ODS_OPENBY, ODS_OPENASK, ODS_OPENBYASK]:

                return True
        return False

    def __check_contraint_exist(self, md: bytes, constraint: str):
        """
        Check if the given ODS constraint is already set up in the metadata.

        If yes and in first position : returns True
        If no : returns False
        If yes but not in first position : returns the xpath where the constraint is

        Args:
            md : metadata in bytes
            constraint : [ODS_OPEN, ODS_OPENBY, ODS_OPENASK, ODS_OPENBYASK]
        """

        root = ET.fromstring(md)
        tree = ET.ElementTree(root)

        # constraint exists and is in the first position
        if len(tree.findall(".//gmd:resourceConstraints//gmd:otherConstraints",
            namespaces=constants.NS)) > 0:

            if tree.findall(".//gmd:resourceConstraints//gmd:otherConstraints/gmx:Anchor",
                namespaces=constants.NS)[0].attrib["{http://www.w3.org/1999/xlink}href"] == constraint:
                return True

            for tag in tree.findall(".//gmd:resourceConstraints//gmd:otherConstraints",
                                        namespaces=constants.NS):

                # constraints exist but not in first position
                if tag[0].attrib["{http://www.w3.org/1999/xlink}href"] == constraint:
                    return tree.getpath(tag)

        return False

    def __bring_constraint_to_first(self, md: bytes, uuid: str, constraint: str, 
                                    constraint_xpath: str) -> object:
        """
        Bring constraints to first position

        Args:
            uuid : uuid of the metadata to process
            md : metadata as bytes
            constraint : [ODS_OPEN, ODS_OPENBY, ODS_OPENASK, ODS_OPENBYASK]
            constraint_xpath : xpath of the given constraint

        Returns the response of batch editing API request
        """

        root = ET.fromstring(md)
        tree = ET.ElementTree(root)

        # if only one resourceConstraint tag or the matching ODS constraint is in the first
        # resourceConstraint. Delete the matching ODS constraint and add it at first position
        if not constraint_xpath.split("/")[-3].endswith("]") or \
                constraint_xpath.split("/")[-3].endswith("[1]"):

            xpath_to_delete = constraint_xpath
            xpath_to_add = constraint_xpath[:-3] + "[1]"
            value_to_add = ODS_LEGAL_CONSTRAINTS[constraint]

        # multiple resourceConstraints. Delete matching ODS tag if it's the only constraint. If not,
        # delete the entire resourceConstraint. Add a new resourceConstraint at first position.
        else:
            if len(tree.xpath("/".join(constraint_xpath.split("/")[:-1]),
                            namespaces=constants.NS)[0].getchildren()) > 1:

                xpath_to_delete = constraint_xpath

            else:
                xpath_to_delete = "/".join(constraint_xpath.split("/")[:-2])

            xpath_to_add = ".//gmd:resourceConstraints[1]"
            value_to_add = RESOURCE_CONSTRAINTS_TAG[0] + ODS_LEGAL_CONSTRAINTS[constraint] + RESOURCE_CONSTRAINTS_TAG[1]

        body = [
            {
                "xpath": xpath_to_delete,
                "value": "<gn_delete></gn_delete>",
            },
            {
                "xpath": xpath_to_add,
                "value": f"<gn_add>{value_to_add}</gn_add>",
            },
        ]

        response = self.api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)
        return response

    def __get_body_to_add_constraint(self, md: bytes, constraint: str) -> list:
        """
        Get body xpath/value as list to add the new constraint with batch editing API request

        Args:
            md : metadata in bytes
            constraint : [ODS_OPEN, ODS_OPENBY, ODS_OPENASK, ODS_OPENBYASK]
        """

        root = ET.fromstring(md)
        tree = ET.ElementTree(root)

        tag_other = tree.find(".//gmd:resourceConstraints//gmd:otherConstraints",
                                namespaces=constants.NS)

        tag_legal = tree.find(".//gmd:resourceConstraints/gmd:MD_LegalConstraints",
                                namespaces=constants.NS)

        tag_che_legal = tree.find(".//gmd:resourceConstraints/che:CHE_MD_LegalConstraints",
                                namespaces=constants.NS)

        if tag_other is not None:

            xpath = tree.getpath(tag_other)
            if not xpath.endswith("]"):
                xpath = xpath + "[1]"

            value = ODS_LEGAL_CONSTRAINTS[constraint]

        else:
            if tag_che_legal is not None:

                xpath = tree.getpath(tag_che_legal)
                value = ODS_LEGAL_CONSTRAINTS[constraint]

            elif tag_legal is not None:

                xpath = tree.getpath(tag_legal)
                value = ODS_LEGAL_CONSTRAINTS[constraint]

            else:
                if len(root.findall(".//gmd:resourceConstraints", namespaces=constants.NS)) > 0:

                    xpath = ".//gmd:resourceConstraints[1]"
                    value = RESOURCE_CONSTRAINTS_TAG[0] + ODS_LEGAL_CONSTRAINTS[constraint] + RESOURCE_CONSTRAINTS_TAG[1]

                    # if there is an empty resourceConstraints tag, we fill it with the ODS const.
                    for tag in tree.findall(".//gmd:resourceConstraints", namespaces=constants.NS):
                        if len(tag.getchildren()) == 0:
                            xpath = tree.getpath(tag)
                            value = LEGAL_CONSTRAINTS_TAG[0] + ODS_LEGAL_CONSTRAINTS[constraint] + LEGAL_CONSTRAINTS_TAG[1]
                            break

                else:

                    xpath = ".//gmd:identificationInfo[1]/*"
                    value = RESOURCE_CONSTRAINTS_TAG[0] + ODS_LEGAL_CONSTRAINTS[constraint] + RESOURCE_CONSTRAINTS_TAG[1]

        return [
            {
            "xpath": xpath,
            "value": f"<gn_add>{value}</gn_add>",
            }
        ]

    def __get_body_to_delete_constraint(self, md: bytes, constraint: str) -> list:
        """
        Get body xpath/value as list to delete the constraint with batch editing API request

        Args:
            md : metadata in bytes
            constraint : [ODS_OPEN, ODS_OPENBY, ODS_OPENASK, ODS_OPENBYASK]
        """

        root = ET.fromstring(md)
        tree = ET.ElementTree(root)

        body = list()

        for el in tree.findall(f".//gmd:resourceConstraints//gmd:otherConstraints/gmx:Anchor",
                                namespaces=constants.NS):

            if el.attrib["{http://www.w3.org/1999/xlink}href"] == constraint:
                xpath = tree.getpath(el)

                # if more than one Constraints under the legalConstraint tag,
                # we erase only the matching otherConstraint, we let the rest untouched.
                if len(tree.xpath("/".join(xpath.split("/")[:-2]), 
                        namespaces=constants.NS)[0].getchildren()) > 1:

                    body.append({
                        "xpath": "/".join(xpath.split("/")[:-1]),
                        "value": "<gn_delete></gn_delete>",
                    })

                # if only one constraint under the legalConstraint tag,
                # we erase the entire matching resourceConstraint (since we cannot have multiple
                # children under the resourceConstraint tag)
                else:

                    body.append({
                        "xpath": "/".join(xpath.split("/")[:-3]),
                        "value": "<gn_delete></gn_delete>",
                    })

                return body

        return body

    def add_constraint(self, uuids: list, constraint: str, backup: bool = True) -> None:
        """
        Add an ODS legal constraint to a list of metadata.

        Args:
            uuids : a list of metadata uuid
            constraint : [ODS_OPEN, ODS_OPENBY, ODS_OPENASK, ODS_OPENBYASK]
            backup : True or False. If True, backup all metadata before changes are made
        """

        if backup is True:
            self.api.backup_metadata(uuids)

        logger = utils.setup_logger(f"AddODSLegalConstraint_{datetime.now().strftime('%Y%m%d-%H%M%S')}")

        print("Add new ODS legal constraint : ", end="\r")

        successful = 0
        unsuccessful = 0
        already_existing = 0

        count = 0
        for uuid in uuids:

            print(f"Add new ODS legal constraint : {round((count / len(uuids)) * 100, 1)}%", end="\r")
            count += 1

            md = self.api.get_metadata_from_mef(uuid=uuid)

            if md == None:
                logger.error(f"{count}/{len(uuids)} - {uuid} - metadata couldn't be retrieved")
                unsuccessful += 1
                continue

            if self.__check_contraint_exist(md=md, constraint=constraint) is True:
                logger.info(f"{count}/{len(uuids)} - {uuid} - constraint already exists")
                already_existing += 1
                continue

            if self.__check_contraint_exist(md=md, constraint=constraint) is not False:
                logger.info(f"{count}/{len(uuids)} - {uuid} - constraint already exists but not in first position")

                xpath = self.__check_contraint_exist(md=md, constraint=constraint)
                response = self.__bring_constraint_to_first(uuid=uuid, md=md, constraint=constraint, constraint_xpath=xpath)

                if utils.process_ok(response):
                    logger.info(f"{count}/{len(uuids)} - {uuid} - constraint has been moved to first position")
                    already_existing += 1
                else:
                    logger.error(f"{count}/{len(uuids)} - {uuid} - constraint couldn't be moved to first position")
                    unsuccessful += 1

                continue

            if self.__check_constraints(md=md):
                logger.error(f"{count}/{len(uuids)} - {uuid} - An ODS legal constraint already exists ! Please review the metadata to avoid conflicts")
                unsuccessful += 1
                continue

            body = self.__get_body_to_add_constraint(md=md, constraint=constraint)
            response = self.api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)

            if utils.process_ok(response):
                logger.info(f"{count}/{len(uuids)} - {uuid} - new constraint has been successfuly added")
                successful += 1
            else:
                logger.error(f"{count}/{len(uuids)} - {uuid} - new constraint couldn't be added")
                unsuccessful += 1

        print(f"Add new ODS legal constraint : {utils.okgreen('Done')}")
        print(f"ODS legal constraint successfuly added: {utils.okgreen(successful)}")
        print(f"ODS legal constraint already existing: {utils.okgreen(already_existing)}")
        print(f"ODS legal constraint unsuccessfuly added: {utils.warningred(unsuccessful)}")

    def delete_constraint(self, uuids: list, constraint: str, backup: bool = True) -> None:
        """
        Delete an ODS legal constraint from a list of metadata.

        Args:
            uuids : a list of metadata uuid
            constraint : [ODS_OPEN, ODS_OPENBY, ODS_OPENASK, ODS_OPENBYASK]
            backup : True or False. If True, backup all metadata before changes are made
        """

        if backup is True:
            self.api.backup_metadata(uuids)

        logger = utils.setup_logger(f"DeleteODSLegalConstraint_{datetime.now().strftime('%Y%m%d-%H%M%S')}")

        print("Delete ODS legal constraint : ", end="\r")

        successful = 0
        unsuccessful = 0
        not_existing = 0

        count = 0
        for uuid in uuids:

            print(f"Delete ODS legal constraint : {round((count / len(uuids)) * 100, 1)}%", end="\r")
            count += 1

            md = self.api.get_metadata_from_mef(uuid=uuid)

            if md == None:
                logger.error(f"{count}/{len(uuids)} - {uuid} - metadata couldn't be retrieved")
                unsuccessful += 1
                continue

            if self.__check_contraint_exist(md=md, constraint=constraint) is False:
                logger.info(f"{count}/{len(uuids)} - {uuid} - constraint doesn't exist")
                not_existing += 1
                continue

            while self.__check_contraint_exist(md=md, constraint=constraint):

                body = self.__get_body_to_delete_constraint(md=md, constraint=constraint)
                response = self.api.edit_metadata(uuid=uuid, body=body, updateDateStamp=True)

                if utils.process_ok(response):
                    logger.info(f"{count}/{len(uuids)} - {uuid} - constraint has been successfuly deleted")
                    successful += 1
                else:
                    logger.error(f"{count}/{len(uuids)} - {uuid} - constraint couldn't be deleted")
                    unsuccessful += 1

                md = self.api.get_metadata_from_mef(uuid=uuid)

        print(f"Delete ODS legal constraint : {utils.okgreen('Done')}")
        print(f"ODS legal constraint successfuly deleted: {utils.okgreen(successful)}")
        print(f"ODS legal constraint not existing: {utils.okgreen(not_existing)}")
        print(f"ODS legal constraint unsuccessfuly deleted: {utils.warningred(unsuccessful)}")
