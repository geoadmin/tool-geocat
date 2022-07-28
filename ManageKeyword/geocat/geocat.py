import getpass
import os
import sys
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from zipfile import ZipFile
import io
import requests
import urllib3
from dotenv import load_dotenv
import psycopg2
from . import constants
from . import utils

class GeocatAPI():
    """
    Class to facilitate work with the geocat Restful API.
    Connect to geocat.ch with your username and password.
    Store request's session, XSRF Token, http authentication, proxies

    Parameters :
        env -> str (default = 'int'), can be set to 'prod'
    """

    def __init__(self, env: str = 'int'):
        if env not in constants.ENV:
            print(utils.warningred(f"No environment : {env}"))
            sys.exit()
        if env == 'prod':
            print(utils.warningred("WARNING : you choose the Production environment ! Be careful, all changes will be live on geocat.ch"))
        self.env = constants.ENV[env]
        self.__username = getpass.getpass("Geocat Username : ")
        self.__password = getpass.getpass("Geocat Password : ")
        self.session = self.__get_token()

    def __get_token(self) -> object:
        """Function to get the token and test which proxy is needed"""
        session = requests.Session()
        session.cookies.clear()

        session.auth = (self.__username, self.__password)

        for proxies in constants.PROXY:
            try:
                session.post(url=self.env + '/geonetwork/srv/eng/info?type=me', proxies=proxies)
            except (requests.exceptions.ProxyError, OSError, urllib3.exceptions.MaxRetryError):
                pass
            else:
                break

        session.proxies.update(proxies)

        cookies = session.cookies.get_dict()
        token = cookies["XSRF-TOKEN"]
        session.headers.update({"X-XSRF-TOKEN": token})

        response = session.post(url=self.env + '/geonetwork/srv/eng/info?type=me')

        if response.status_code != 200:
            print(utils.warningred('Username or password not valid !'))
            sys.exit()

        xmlroot = ET.fromstring(response.text)
        if xmlroot.find("me").attrib["authenticated"] != "true":
            print(utils.warningred('Username or password not valid !'))
            sys.exit()

        return session

    def __db_connect(self) -> object:
        """Connect to geocat DB and returns a psycopg2 connection object"""

        # Access database credentials from .env variable if exist
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path=env_path)

        db_username = os.getenv('DB_USERNAME')
        db_password = os.getenv('DB_PASSWORD')

        if db_username is None or db_password is None:
            db_username = getpass.getpass("Geocat Database Username : ")
            db_password = getpass.getpass("Geocat Database Password : ")

        _env = [k for k, v in constants.ENV.items() if v == self.env][0]

        connection = psycopg2.connect(
                host="database-lb.geocat.swisstopo.cloud",
                database=f"geocat-{_env}",
                user=db_username,
                password=db_password)

        return connection

    def check_admin(self) -> bool:
        """
        Check if the user is a geocat admin. If not, abort the program
        """
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        response = self.session.get(url=self.env + '/geonetwork/srv/api/0.1/me', headers=headers)
        if json.loads(response.text)["profile"] == "Administrator":
            return True

        return False

    def get_uuids_all(self, valid_only: bool = False, published_only: bool = False,
                      with_templates: bool = False) -> list:
        """
        Get a list of metadata uuid of all records.
        You can specify if you want only the valid and/or published records and the templates.
        """

        headers = {"accept": "application/xml", "Content-Type": "application/xml"}

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

            response = self.session.get(url=self.env + "/geonetwork/srv/fre/q", headers=headers, params=parameters)

            xmlroot = ET.fromstring(response.content)
            metadatas = xmlroot.findall("metadata")

            if len(metadatas) == 0:
                break

            for metadata in metadatas:
                if metadata.find("*/uuid").text not in uuids:
                    uuids.append(metadata.find("*/uuid").text)

            start += 1499

        return uuids

    def get_uuids_by_group(self, group_id: str, valid_only: bool = False, 
                    published_only: bool = False, with_templates: bool = False) -> list:
        """
        Get a list of metadata uuid belonging to a given group.
        You can specify if you want only the valid and/or published records and the templates.
        """

        headers = {"accept": "application/xml", "Content-Type": "application/xml"}

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

            response = self.session.get(url=self.env + "/geonetwork/srv/fre/q", headers=headers, params=parameters)

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

        headers = {"accept": "application/xml", "Content-Type": "application/xml"}

        uuid = []
        start = 1

        while True:
            parameters = {
                "facet.q": "isHarvested/y",
                "from": start,
            }

            response = self.session.get(url=self.env + "/geonetwork/srv/fre/q", headers=headers, params=parameters)

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

        headers = {"accept": "application/xml", "Content-Type": "application/xml"}

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

            response = self.session.get(url=self.env + "/geonetwork/srv/fre/q", headers=headers, params=parameters)

            xmlroot = ET.fromstring(response.content)
            metadatas = xmlroot.findall("metadata")

            if len(metadatas) == 0:
                break

            for metadata in metadatas:
                if metadata.find("*/uuid").text not in uuids:
                    uuids.append(metadata.find("*/uuid").text)

            start += 1499

        return uuids

    def get_ro_uuids(self, valid_only: bool = False, published_only: bool = False) -> dict:
        """
        Get UUID of all reusable objects (subtemplates).
        You can specify if you want only the valid and/or published records. The subtemplates template are not returned.
        Returns a dictionnary with the 3 kinds of RO : {"contact": ,"extent": ,"format": }
        """

        if not self.check_admin():
            print(utils.warningred("You need to be admin to use this method"))
            return

        uuids_contact = list()
        uuids_extent = list()
        uuids_format = list()

        try:
            connection = self.__db_connect()

            with connection.cursor() as cursor:

                if valid_only and not published_only:
                    cursor.execute("SELECT UUID,data FROM public.metadata WHERE istemplate='s'" \
                    "AND id IN (SELECT metadataid FROM public.validation WHERE status=1 AND required=true)")

                elif published_only and not valid_only:
                    cursor.execute("SELECT UUID,data FROM public.metadata WHERE istemplate='s'" \
                    "AND id IN (SELECT metadataid FROM public.operationallowed WHERE groupid=1 AND operationid=0)")
                elif valid_only and published_only:
                    cursor.execute("SELECT UUID,data FROM public.metadata WHERE istemplate='s'" \
                    "AND id IN (SELECT metadataid FROM public.validation WHERE status=1 AND required=true)" \
                    "AND id IN (SELECT metadataid FROM public.operationallowed WHERE groupid=1 AND operationid=0)")
                else:
                    cursor.execute("SELECT UUID,data FROM public.metadata WHERE istemplate='s'")

                for row in cursor:
                    if row[1].startswith("<che:CHE_CI_ResponsibleParty"):
                        uuids_contact.append(row[0])
                    elif row[1].startswith("<gmd:EX_Extent"):
                        uuids_extent.append(row[0])
                    elif row[1].startswith("<gmd:MD_Format"):
                        uuids_format.append(row[0])

        except (Exception, psycopg2.Error) as error:
            print("Error while fetching data from PostgreSQL", error)

        else:
            return {
                "contact": uuids_contact,
                "extent": uuids_extent,
                "format": uuids_format,
            }

        finally:
            if connection:
                connection.close()

    def get_metadata_from_mef(self, uuid: str) -> str:
        """
        Get metadata XML from MEF (metadata exchange format).
        """

        headers = {"accept": "application/x-gn-mef-2-zip"}

        proxy_error = True
        while proxy_error:
            try:
                response = self.session.get(url=self.env + f"/geonetwork/srv/api/0.1/records/{uuid}/formatters/zip",
                                            headers=headers)
            except requests.exceptions.ProxyError:
                print("Proxy Error Occured, retry connection")
            else:
                proxy_error = False

        if response.status_code != 200:
            print(f"{utils.warningred('The following Metadata could not be exported in MEF : ') + uuid}")
            return None

        with ZipFile(io.BytesIO(response.content)) as zip:
            if f"{uuid}/metadata/metadata.xml" in zip.namelist():
                return zip.open(f"{uuid}/metadata/metadata.xml").read()
            else:
                print(f"{utils.warningred('The following Metadata could not be exported in MEF : ') + uuid}")

    def get_metadata_from_db(self, uuid: str) -> str:
        """
        Get metadata XML directly from database.
        """

        if not self.check_admin():
            print(utils.warningred("You need to be admin to use this method"))
            return

        try:
            connection = self.__db_connect()

            with connection.cursor() as cursor:
                cursor.execute(f"SELECT data FROM public.metadata WHERE uuid='{uuid}'")
                md_xml = cursor.fetchone()[0]

        except (Exception, psycopg2.Error) as error:
            print("Error while fetching data from PostgreSQL", error)

        else:
            return md_xml

        finally:
            if connection:
                connection.close()

    def backup_metadata(self, uuids: list):
        """
        Backup list of metadata as MEF zip file.
        """

        if sys.platform == "win32":

            if not os.path.isdir(f"C:/Users/{os.getlogin()}/AppData/Local/geocat"):
                os.mkdir(f"C:/Users/{os.getlogin()}/AppData/Local/geocat")

            backup_dir = f"C:/Users/{os.getlogin()}/AppData/Local/geocat/MetadataBackup_{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            os.mkdir(backup_dir)

        else:
            print(utils.warningred("You are not on windows ! Directory to backup metadata not found !"))
            return None

        headers = {"accept": "application/x-gn-mef-2-zip"}

        print("Backup metadata : ", end="\r")

        count = 1
        for uuid in uuids:

            proxy_error = True
            while proxy_error:
                try:
                    response = self.session.get(url=self.env + f"/geonetwork/srv/api/0.1/records/{uuid}/formatters/zip",
                                                headers=headers)
                except requests.exceptions.ProxyError:
                    print("Proxy Error Occured, retry connection")
                else:
                    proxy_error = False

            if response.status_code != 200:
                print(f"{utils.warningred('The following Metadata could not be backup : ') + uuid}")
                continue

            with open(os.path.join(backup_dir, f"{uuid}.zip"), "wb") as f:
                f.write(response.content)

            print(f"Backup metadata : {round((count / len(uuids)) * 100, 1)}%", end="\r")

            count += 1

        print(f"Backup metadata : {utils.okgreen('Done')}")
        print(f"Backup available at : {backup_dir}")

    def edit_metadata(self, uuid: str, body: list, updateDateStamp: str ='false') -> object:
        """
        Edit a metadata by giving sets of xpath and xml.

        Args:
            uuid : the uuid of the metadata to edit.
            body : the edits you want to perform : [{"xpath": xpath, "value": xml}, {"xpath": xpath, "value": xml}, ...]
            updateDateStamp : 'true' or 'false', default = 'false'. If 'true', 
            the update date and time of the metadata is updated

        Returns:
            The response of the batchediting request
        """
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        params = {
            "uuids": [uuid],
            "updateDateStamp": updateDateStamp,
        }

        body = json.dumps(body)

        response = self.session.put(self.env + "/geonetwork/srv/api/0.1/records/batchediting",
                                    params=params, headers=headers, data=body)

        return response