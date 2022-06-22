import requests
from requests.auth import HTTPBasicAuth
import getpass
import urllib3
import sys
import xml.etree.ElementTree as ET
import json
import colorama
import logging

colorama.init()

NS = {
    'csw': 'http://www.opengis.net/cat/csw/2.0.2',
    'gco': 'http://www.isotc211.org/2005/gco',
    'che': 'http://www.geocat.ch/2008/che',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'srv': 'http://www.isotc211.org/2005/srv',
    'gmx': 'http://www.isotc211.org/2005/gmx',
    'gts': 'http://www.isotc211.org/2005/gts',
    'gsr': 'http://www.isotc211.org/2005/gsr',
    'gmi': 'http://www.isotc211.org/2005/gmi',
    'gml': 'http://www.opengis.net/gml/3.2',
    'xlink': 'http://www.w3.org/1999/xlink',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'geonet': 'http://www.fao.org/geonetwork',
    'java': 'java:org.fao.geonet.util.XslUtil',
}

ENV = {
    'int': 'https://geocat-int.dev.bgdi.ch',
    'prod': 'https://www.geocat.ch',
}

PROXY = [
    {
        "http": "prp01.adb.intra.admin.ch:8080",
        "https": "prp01.adb.intra.admin.ch:8080",
    },
    {
        "http": "proxy-bvcol.admin.ch:8080",
        "https": "proxy-bvcol.admin.ch:8080",
    },
    {
        "http": "proxy.admin.ch:8080",
        "https": "proxy.admin.ch:8080",
    }
]


def xpath_ns_url2code(path: str) -> str:
    """Replace the namespace url by the namespace acronym in the given xpath"""
    for key in NS:
        path = path.replace("{" + NS[key] + "}", f"{key}:")

    return path


def xpath_ns_code2url(path: str) -> str:
    """Replace the namespace url by the namespace acronym in the given xpath"""
    for key in NS:
        path = path.replace(f"{key}:", "{" + NS[key] + "}")

    return path


def setup_logger(name: str, log_file: str, level=logging.INFO) -> object:
    """Setup a logger for logging
    Args:
        name: required, the mane of the logger
        log_file: required, the path where to write the logger
        level: optional, the level to log

    Returns:
        Logger object
    """
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", '%d-%m-%y %H:%M:%S')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def okgreen(text):
    return f"\033[92m{text}\033[00m"


def warningred(text):
    return f"\033[91m{text}\033[00m"


class GeocatAPI():
    """
    Class to facilitate work with the geocat Restful API. Connect to geocat.ch with your username and password.
    Store request's session, XSRF Token, http authentication, proxies
    Parameters :
    env -> str (default = 'int'), can be set to 'prod'
    """

    def __init__(self, env: str = 'int'):
        if env not in ENV:
            print(warningred(f"No environment : {env}"))
            sys.exit()
        if env == 'prod':
            print(warningred("WARNING : you choose the Production environment ! Be careful, all changes will be live on geocat.ch"))
        self.env = ENV[env]
        self.username = input("Geocat Username : ")
        self.password = getpass.getpass("Geocat Password : ")
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.session, self.token, self.proxies = self.get_token()

    def get_token(self):
        """Function to get the token and test which proxy is needed"""
        session = requests.Session()
        session.cookies.clear()

        for proxies in PROXY:
            try:
                session.post(url=self.env + '/geonetwork/srv/eng/info?type=me', proxies=proxies, auth=self.auth)
            except (requests.exceptions.ProxyError, OSError, urllib3.exceptions.MaxRetryError):
                pass
            else:
                break

        cookies = session.cookies.get_dict()
        token = cookies["XSRF-TOKEN"]

        headers = {"X-XSRF-TOKEN": token}
        response = session.post(url=self.env + '/geonetwork/srv/eng/info?type=me', proxies=proxies, auth=self.auth,
                                headers=headers)

        if response.status_code != 200:
            print(warningred('Username or password not valid !'))
            sys.exit()

        xmlroot = ET.fromstring(response.text)
        if xmlroot.find("me").attrib["authenticated"] != "true":
            print(warningred('Username or password not valid !'))
            sys.exit()

        return session, token, proxies

    def check_admin(self):
        """
        Check if the user is a geocat admin. If not, abort the program
        """
        headers = {"accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": self.token}
        response = self.session.get(url=self.env + '/geonetwork/srv/api/0.1/me', proxies=self.proxies, auth=self.auth, headers=headers)
        if json.loads(response.text)["profile"] == "Administrator":
            return True

        return False

    def getMDbyUUID(self, UUID: str):
        """
        Get the metadata as XML by giving its uuid (parameter UUID).
        All the reusable objects are written as subtemplates. I.e. the xlink are lost.
        """
        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.token}
        response = self.session.get(self.env + f"/geonetwork/srv/api/0.1/records/{UUID}/formatters/xml",
                                    proxies=self.proxies, auth=self.auth, headers=headers)

        if response.status_code == 404:
            print(warningred("The given UUID doesn't exist !"))
            return

        elif response.status_code == 403:
            print(warningred("Access to this metadata denied !"))
            return

        return response

    def get_uuids_all(self, valid_only: bool = False, published_only: bool = False,
                      with_templates: bool = False) -> list:
        """
        Get a list of metadata uuid of all records.
        You can specify if you want only the valid and/or published records and the templates.
        """

        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.token}

        uuids = []
        start = 1

        while True:

            facetq = str()

            if valid_only:
                facetq += "&isValid/1"
            if published_only:
                facetq += "&isPublishedToAll/y"

            parameters = {
                "from": start,
            }

            if len(facetq) > 0:
                parameters["facet.q"] = facetq[1:]

            if with_templates:
                parameters["_isTemplate"] = "y or n"

            response = self.session.get(url=self.env + f"/geonetwork/srv/fre/q", proxies=self.proxies,
                                            auth=self.auth, headers=headers, params=parameters)

            xmlroot = ET.fromstring(response.content)
            metadatas = xmlroot.findall("metadata")

            if len(metadatas) == 0:
                break

            for metadata in metadatas:
                if metadata.find("*/uuid").text not in uuids:
                    uuids.append(metadata.find("*/uuid").text)

            start += 1499

        return uuids

    def get_uuids_by_group(self, group_id: str, valid_only: bool = False, published_only: bool = False,
                      with_templates: bool = False) -> list:
        """
        Get a list of metadata uuid belonging to a given group.
        You can specify if you want only the valid and/or published records and the templates.
        """

        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.token}

        uuids = []
        start = 1

        while True:

            facetq = str()

            if valid_only:
                facetq += "&isValid/1"
            if published_only:
                facetq += "&isPublishedToAll/y"

            parameters = {
                "_groupOwner": group_id,
                "from": start,
            }

            if len(facetq) > 0:
                parameters["facet.q"] = facetq[1:]

            if with_templates:
                parameters["_isTemplate"] = "y or n"

            response = self.session.get(url=self.env + f"/geonetwork/srv/fre/q", proxies=self.proxies,
                                            auth=self.auth, headers=headers, params=parameters)

            xmlroot = ET.fromstring(response.content)
            metadatas = xmlroot.findall("metadata")

            if len(metadatas) == 0:
                break

            for metadata in metadatas:
                if metadata.find("*/uuid").text not in uuids:
                    uuids.append(metadata.find("*/uuid").text)

            start += 1499

        return uuids

    def get_uuids_harvested(self) -> list:
        """
        Get a list of metadata uuid of all harvested records (no templates).
        """

        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.token}

        uuid = []
        start = 1

        while True:
            parameters = {
                "facet.q": "isHarvested/y",
                "from": start,
            }

            response = self.session.get(url=self.env + f"/geonetwork/srv/fre/q", proxies=self.proxies,
                                            auth=self.auth, headers=headers, params=parameters)

            xmlroot = ET.fromstring(response.content)
            metadatas = xmlroot.findall("metadata")

            if len(metadatas) == 0:
                break

            for metadata in metadatas:
                if metadata.find("*/uuid").text not in uuid:
                    uuid.append(metadata.find("*/uuid").text)

            start += 1499

        return uuid

    def get_uuids_notharvested(self, valid_only: bool = False, published_only: bool = False,
                      with_templates: bool = False) -> list:
        """
        Get a list of metadata uuid of all non harvested records.
        You can specify if you want only the valid and/or published records and the templates.
        """

        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.token}

        uuids = []
        start = 1

        while True:

            facetq = str()

            if valid_only:
                facetq += "&isValid/1"
            if published_only:
                facetq += "&isPublishedToAll/y"

            parameters = {
                "facet.q": "isHarvested/n",
                "from": start,
            }

            if len(facetq) > 0:
                parameters["facet.q"] = facetq[1:]

            if with_templates:
                parameters["_isTemplate"] = "y or n"

            response = self.session.get(url=self.env + f"/geonetwork/srv/fre/q", proxies=self.proxies,
                                            auth=self.auth, headers=headers, params=parameters)

            xmlroot = ET.fromstring(response.content)
            metadatas = xmlroot.findall("metadata")

            if len(metadatas) == 0:
                break

            for metadata in metadatas:
                if metadata.find("*/uuid").text not in uuids:
                    uuids.append(metadata.find("*/uuid").text)

            start += 1499

        return uuids

    def edit_metadata(self, uuid: str, body: list, updateDateStamp: str ='false') -> object:
        """
        Edit a metadata by giving sets of xpath and xml.

        Args:
            uuid : the uuid of the metadata to edit.
            body : the edits you want to perform : [{"xpath": xpath, "value": xml}, {"xpath": xpath, "value": xml}, ...]
            updateDateStamp : 'true' or 'false', default = 'false'. If 'true', the update date and time of the metadata is
            updated

        Returns:
            The response of the batchediting request
        """
        headers = {"accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": self.token}
        params = {
            "uuids": [uuid],
            "updateDateStamp": updateDateStamp,
        }

        body = json.dumps(body)

        response = self.session.put(self.env + "/geonetwork/srv/api/0.1/records/batchediting",
                                    params=params, proxies=self.proxies, auth=self.auth, headers=headers, data=body)

        return response