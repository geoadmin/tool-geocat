import requests
from requests.auth import HTTPBasicAuth
import getpass
import urllib3
import sys
import xml.etree.ElementTree as ET
import json
import colorama

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
        "http": "proxy-bvcol.admin.ch:8080",
        "https": "proxy-bvcol.admin.ch:8080",
    },
    {
        "http": "proxy.admin.ch:8080",
        "https": "proxy.admin.ch:8080",
    }
]


def okgreen(text):
    return f"\033[92m{text}\033[00m"


def warningred(text):
    return f"\033[91m{text}\033[00m"


class GeocatAPI():
    """
    Class to facilitate work with the geocat Restful API.

    Connect to geocat.ch with your username and password.
    Store request's session, XSRF Token, http authentication, proxies

    Attributes :
        env: str 'int' or 'prod' (default = 'int')
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

        # TODO : Check what happen when no proxies are needed (outside of swisstopo)
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

    def edit_metadata(self, uuid: str, body: list, updateDateStamp: str ='false'):
        """
        Edit a metadata by giving sets of xpath and xml.
        Parameters :
        uuid : the uuid of the metadata to edit.
        body : the edits you want to perform : [{"xpath": xpath, "value": xml}, {"xpath": xpath, "value": xml}, ...]
        updateDateStamp : 'true' or 'false', default = 'false'. If 'true', the update date and time of the metadata is
        updated
        Return the response of the API request
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

