import os
import requests
from requests.auth import HTTPBasicAuth
import getpass
import urllib3
import sys
import xml.etree.ElementTree as ET
import json
import pandas as pd
from zipfile import ZipFile
from datetime import datetime
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
        Return 2 values : 1) True if process successful and False if not. 2) The error message if 1 = False
        """
        headers = {"accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": self.token}
        params = {
            "uuids": [uuid],
            "updateDateStamp": updateDateStamp,
        }

        body = json.dumps(body)

        response = self.session.put(self.env + "/geonetwork/srv/api/0.1/records/batchediting",
                                    params=params, proxies=self.proxies, auth=self.auth, headers=headers, data=body)

        if json.loads(response.text)['numberOfNullRecords'] > 0:
            error_message = "The metadata UUID is wrong !"
            process_ok = False

        elif json.loads(response.text)['numberOfRecordsWithErrors'] > 0:
            error_message = "Something is wrong in the request's body !"
            process_ok = False

        elif json.loads(response.text)['numberOfRecordsNotEditable'] > 0:
            error_message = "Access to the metadata denied !"
            process_ok = False

        elif json.loads(response.text)['numberOfRecordsProcessed'] == 0:
            error_message = "Something went wrong, no metadata processed !"
            process_ok = False
        else:
            error_message = None
            process_ok = True

        return process_ok, error_message


class GeocatBackup():
    """
    Generate a backup of geocat (of the chosen environment).
    ---
    Parameters :
    backup_dir: str - The directory where to store the backup
    env: str (default = 'int') - Can be set to 'prod'
    catalogue: bool (default = True) - If True backup all metadatas as an MEF archive
    users: bool (default = True) - If True backup users
    groups: bool (default = True) - If True backup groups
    reusable_objects: bool (default = True) - If True backup reusable objects
    thesaurus: bool (default = True) - If True backup thesaurus (keywords)
    """
    def __init__(self, backup_dir: str, env: str = 'int', catalogue: bool = True, users: bool = True,
                 groups: bool = True, reusable_objects: bool = True, thesaurus: bool = True):

        self.api = GeocatAPI(env)
        print("Backup started...")
        self.backup_dir = backup_dir

        if not GeocatAPI.check_admin(self.api):
            print(f"{warningred('You must be admin to launch a backup of geocat')}")
            sys.exit()
            
        self.check_backup_dir()

        if catalogue:
            self.backup_catalogue_mef()
        if users:
            self.backup_users()
        if groups:
            self.backup_groups()
        if reusable_objects:
            self.backup_ro()
        if thesaurus:
            self.backup_thesaurus()

        self.write_logfile()
        self.backup_unpublish_report()

        print(okgreen("Backup Done"))

    def write_logfile(self):
        """
        Write a logfile. Runs everytime the class is initiated
        """
        if os.path.isfile(os.path.join(self.backup_dir, "backup.log")):
            os.remove(os.path.join(self.backup_dir, "backup.log"))

        # Number of MDs
        if os.path.isfile(os.path.join(self.backup_dir, f"backup_{datetime.today().strftime('%Y-%m-%d')}.zip")):

            zip = ZipFile(os.path.join(self.backup_dir, f"backup_{datetime.today().strftime('%Y-%m-%d')}.zip"))
            md_xml = [i.split('/')[0] for i in zip.namelist() if i.split('/')[-1] == "metadata.xml"]
            md_total = []
            for md in zip.namelist():
                if md.split(".")[-1] != "html" and md.split(".")[-1] != "csv":
                    if md.split("/")[0] not in md_total:
                        md_total.append(md.split("/")[0])

            md_without_xml = list(set(md_total) - set(md_xml))

            with open(os.path.join(self.backup_dir, "backup.log"), "w") as logfile:
                logfile.write(f"Metadatas backcup : {len(md_total)}\n")
                logfile.write(f"Metadatas backcup with xml : {len(md_xml)}\n")
                logfile.write(f"Metadatas backcup without xml : {len(md_without_xml)}\n")
                for md in md_without_xml:
                    logfile.write(f"Couldn't find an XML file for this metadata : {md}\n")

        # Number of users
        if os.path.isfile(self.backup_dir + "/users/users.json"):
            with open(self.backup_dir + "/users/users.json") as users:
                with open(os.path.join(self.backup_dir, "backup.log"), "a") as logfile:
                    logfile.write(f"Users backup : {len(json.load(users))}\n")

        # Number of groups
        if os.path.isfile(self.backup_dir + "/groups/groups.json"):
            with open(self.backup_dir + "/groups/groups.json") as groups:
                with open(os.path.join(self.backup_dir, "backup.log"), "a") as logfile:
                    logfile.write(f"Groups backup : {len(json.load(groups))}\n")

        # Number of ro contacts
        if os.path.isdir(self.backup_dir + "/RO_contacts"):
            with open(os.path.join(self.backup_dir, "backup.log"), "a") as logfile:
                logfile.write(f"Contacts (reusable objects) backup : {len(os.listdir(self.backup_dir + '/RO_contacts'))}\n")

        # Number of ro extents
        if os.path.isdir(self.backup_dir + "/RO_extents"):
            with open(os.path.join(self.backup_dir, "backup.log"), "a") as logfile:
                logfile.write(f"Extents (reusable objects) backup : {len(os.listdir(self.backup_dir + '/RO_extents'))}\n")

        # Number of ro formats
        if os.path.isdir(self.backup_dir + "/RO_formats"):
            with open(os.path.join(self.backup_dir, "backup.log"), "a") as logfile:
                logfile.write(f"Formats (reusable objects) backup : {len(os.listdir(self.backup_dir + '/RO_formats'))}\n")

    def check_backup_dir(self):
        """
        Check if the given backup directory is correct and creates it if it doesn't exist
        """
        if not os.path.exists(self.backup_dir):
            try:
                os.mkdir(self.backup_dir)
            except FileNotFoundError:
                print(warningred("The path for the backup directory doesn't exist !"))
                sys.exit()

    def backup_catalogue_mef(self):
        """
        Download the geocat MEF archive as zip file
        """
        print("Backup Catalogue as MEF...", end="\r")
        headers = {"accept": "application/zip", "Content-Type": "application/zip", "X-XSRF-TOKEN": self.api.token}
        response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/records/backups/latest",
                                        proxies=self.api.proxies, auth=self.api.auth, headers=headers)

        with open(os.path.join(self.backup_dir, f"backup_{datetime.today().strftime('%Y-%m-%d')}.zip"), 'wb') as file:
            file.write(response.content)

        print(f"Backup Catalogue as MEF {okgreen('Done')}")

    def backup_users(self):
        """
        Backup all users in a single json file.
        Backup a json file per user with group information.
        Backup a csv file with list of users.
        """
        print("Backup users : ", end="\r")
        output_dir = os.path.join(self.backup_dir, "users")

        # If output dir doesn't already exist, creates it.
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        # Save the users list as json file
        headers = {"accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": self.api.token}
        response = self.api.session.get(url=self.api.env + "/geonetwork/srv/api/0.1/users", proxies=self.api.proxies, auth=self.api.auth, headers=headers)
        with open(os.path.join(output_dir, "users.json"), 'w') as file:
            json.dump(response.json(), file)

        # Collect group information for each user
        if not os.path.exists(os.path.join(output_dir, "users_with_groups")):
            os.mkdir(os.path.join(output_dir, "users_with_groups"))

        columns = ["id", "username", "profile", "enabled", "group_name", "groupID_UserAdmin", "groupID_Editor",
                   "groupID_Reviewer", "groupID_RegisteredUser"]

        df = pd.DataFrame(columns=columns)
        total = len(json.loads(response.text))
        count = 0

        for user in json.loads(response.text):
            response_usergroup = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/users/{user['id']}/groups",
                                            proxies=self.api.proxies, auth=self.api.auth, headers=headers)

            # Save a json file per user with groups information
            with open(os.path.join(output_dir, f"users_with_groups/{user['id']}.json"), 'w') as file:
                json.dump(response_usergroup.json(), file)

            # Crate a DataFrame with information about the users, one row per user
            group_names = []
            useradmin_id = []
            editor_id = []
            reviewer_id = []
            registereduser_id = []

            for user_group in json.loads(response_usergroup.text):
                if user_group["group"]["name"] not in group_names:
                    group_names.append(user_group["group"]["name"])
                if user_group["id"]["profile"] == "UserAdmin" and user_group["id"]["groupId"] not in useradmin_id:
                    useradmin_id.append(user_group["id"]["groupId"])
                if user_group["id"]["profile"] == "Editor" and user_group["id"]["groupId"] not in editor_id:
                    editor_id.append(user_group["id"]["groupId"])
                if user_group["id"]["profile"] == "Reviewer" and user_group["id"]["groupId"] not in reviewer_id:
                    reviewer_id.append(user_group["id"]["groupId"])
                if user_group["id"]["profile"] == "RegisteredUser" and user_group["id"]["groupId"] not in registereduser_id:
                    registereduser_id.append(user_group["id"]["groupId"])

            group_names = "/".join(group_names)
            useradmin_id = "/".join([str(i) for i in useradmin_id])
            editor_id = "/".join([str(i) for i in editor_id])
            reviewer_id = "/".join([str(i) for i in reviewer_id])
            registereduser_id = "/".join([str(i) for i in registereduser_id])

            if user["profile"] == "Administrator":
                group_names, useradmin_id, editor_id, reviewer_id, registereduser_id = "all", "all", "all", "all", "all"

            row = {
                "id": user["id"],
                "username": user["username"],
                "profile": user["profile"],
                "enabled": user["enabled"],
                "group_name": group_names,
                "groupID_UserAdmin": useradmin_id,
                "groupID_Editor": editor_id,
                "groupID_Reviewer": reviewer_id,
                "groupID_RegisteredUser": registereduser_id,
            }

            df = df.append(row, ignore_index=True)

            count += 1
            print(f"Backup users : {round((count/total) * 100)}%", end="\r")

        df.to_csv(os.path.join(output_dir, "users_with_groups.csv"), index=False)
        print(f"Backup users : {okgreen('Done')}")

    def backup_groups(self):
        """
        Backup all groups in a single json file
        Backup a json file per group with list of users
        Backup a csv with list of groups
        """
        print("Backup groups : ", end="\r")
        output_dir = os.path.join(self.backup_dir, "groups")

        # If output dir doesn't already exist, creates it.
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        # Save the groups list as json file
        headers = {"accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": self.api.token}
        response = self.api.session.get(url=self.api.env + "/geonetwork/srv/api/0.1/groups?withReservedGroup=True",
                                        proxies=self.api.proxies, auth=self.api.auth, headers=headers)
        with open(os.path.join(output_dir, "groups.json"), 'w') as file:
            json.dump(response.json(), file)

        # Save one json per group with list of users of this group and logo of the group
        # If output dir doesn't already exist, creates it.
        if not os.path.exists(os.path.join(output_dir, "groups_users")):
            os.mkdir(os.path.join(output_dir, "groups_users"))

        if not os.path.exists(os.path.join(output_dir, "groups_logo")):
            os.mkdir(os.path.join(output_dir, "groups_logo"))

        # Create csv file with the following attributes
        df = pd.DataFrame(columns=["id", "group_name", "users_number"])

        total = len(json.loads(response.text))
        count = 0

        for group in json.loads(response.text):
            response_group_users = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/groups/{group['id']}/users",
                                            proxies=self.api.proxies, auth=self.api.auth, headers=headers)
            with open(os.path.join(output_dir, f"groups_users/{group['id']}.json"), 'w') as file:
                json.dump(response_group_users.json(), file)

            # Save logo only if exists
            if group["logo"] != "" and group["logo"] is not None:
                logo_extension = group["logo"].split(".")[-1]

                response_group_logo = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/groups/{group['id']}/logo",
                                                proxies=self.api.proxies, auth=self.api.auth, headers=headers)

                with open(os.path.join(output_dir, f"groups_logo/{group['id']}.{logo_extension}"), 'wb') as file:
                    file.write(response_group_logo.content)

            row = {"id": str(group['id']), "group_name": group['name'],
                   "users_number": str(len(json.loads(response_group_users.text)))}
            df = df.append(row, ignore_index=True)

            count += 1
            print(f"Backup groups : {round((count / total) * 100)}%", end="\r")

        df.to_csv(os.path.join(output_dir, "groups.csv"), index=False)
        print(f"Backup groups : {okgreen('Done')}")

    def get_ro_ids(self) -> list:
        """
        Get reusable ids in all metadata stored in the MEF archive. Search for attributes uuidref and xlink:href.
        Return a list of ids
        """
        print("Searching reusable object IDs : ", end="\r")
        # If the catalogue MEF backup doesn't already exist, download it
        if not os.path.isfile(os.path.join(self.backup_dir, f"backup_{datetime.today().strftime('%Y-%m-%d')}.zip")):
            self.backup_catalogue_mef()

        ro_ids = []
        zip = ZipFile(os.path.join(self.backup_dir, f"backup_{datetime.today().strftime('%Y-%m-%d')}.zip"))

        count = 0
        total = len([i for i in zip.namelist() if i.split('/')[-1] == "metadata.xml"])

        for md in [i for i in zip.namelist() if i.split('/')[-1] == "metadata.xml"]:
            xmlroot = ET.fromstring(zip.open(md).read())

            for uuidref in xmlroot.findall(".//*[@uuidref]"):
                if uuidref.attrib["uuidref"] not in ro_ids:
                    ro_ids.append(uuidref.attrib["uuidref"])

            for xlinkhref in xmlroot.findall(".//*[@{http://www.w3.org/1999/xlink}href]"):
                link = xlinkhref.attrib["{http://www.w3.org/1999/xlink}href"]
                if "srv/api/registries/entries/" in link:
                    start_index = link.find("srv/api/registries/entries/") + len("srv/api/registries/entries/")
                    if link[start_index:].split("/")[0].split("?")[0] not in ro_ids:
                        ro_ids.append(link[start_index:].split("/")[0].split("?")[0])

            count += 1
            print(f"Searching reusable object IDs : {round((count / total) * 100)}%", end="\r")

        print(f"Searching reusable object IDs : {okgreen('Done')}")
        return ro_ids

    def backup_ro(self):
        """
        Takes a list of reusable ids and save them in xml format. The ids not found are written in a log file.
        """
        print("Backup reusable objects : ", end="\r")

        output_dir_contacts = os.path.join(self.backup_dir, "RO_contacts")
        output_dir_extents = os.path.join(self.backup_dir, "RO_extents")
        output_dir_formats = os.path.join(self.backup_dir, "RO_formats")

        # If output dir doesn't already exist, creates it.
        if not os.path.exists(output_dir_contacts):
            os.mkdir(output_dir_contacts)
        if not os.path.exists(output_dir_extents):
            os.mkdir(output_dir_extents)
        if not os.path.exists(output_dir_formats):
            os.mkdir(output_dir_formats)

        # Delete logfile if already exists
        if os.path.exists(os.path.join(self.backup_dir, "RO_error.log")):
            os.remove(os.path.join(self.backup_dir, "RO_error.log"))

        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.api.token}
        parameters = {"lang": "ger,fre,ita,eng,roh"}
        ro_ids = self.get_ro_ids()

        count = 0
        for ro_id in ro_ids:
            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/registries/entries/{ro_id}",
                                            proxies=self.api.proxies, auth=self.api.auth, headers=headers,
                                            params=parameters)

            if response.status_code != 200:
                with open(os.path.join(self.backup_dir, "RO_error.log"), "a") as logfile:
                    logfile.write(f"Reusable object not found : {ro_id}\n")
            else:
                xmlroot = ET.fromstring(response.text)

                # Error
                if xmlroot.tag == "apiError":
                    with open(os.path.join(self.backup_dir, "RO_error.log"), "a") as logfile:
                        logfile.write(f"Reusable object not found : {ro_id}\n")
                # Contact
                elif xmlroot.tag == "{http://www.geocat.ch/2008/che}CHE_CI_ResponsibleParty":
                    with open(os.path.join(output_dir_contacts, f"{ro_id}.xml"), 'wb') as file:
                        file.write(response.content)
                # Format
                elif xmlroot.tag == "{http://www.isotc211.org/2005/gmd}MD_Format":
                    with open(os.path.join(output_dir_formats, f"{ro_id}.xml"), 'wb') as file:
                        file.write(response.content)
                # Extent
                elif xmlroot.tag == "{http://www.isotc211.org/2005/gmd}EX_Extent":
                    with open(os.path.join(output_dir_extents, f"{ro_id}.xml"), 'wb') as file:
                        file.write(response.content)
                # Unknown
                else:
                    output_dir_unknown = os.path.join(self.backup_dir, "RO_unknown")
                    if not os.path.exists(output_dir_unknown):
                        os.mkdir(output_dir_unknown)

                    with open(os.path.join(output_dir_unknown, f"{ro_id}.xml"), 'wb') as file:
                        file.write(response.content)

            count += 1
            print(f"Backup reusable objects : {round((count / len(ro_ids)) * 100)}%", end="\r")
        print(f"Backup reusable objects : {okgreen('Done')}")

    def backup_thesaurus(self):
        """
        Backup 4 thesaurus in rdf format (xml) : geocat.ch, GEMET, GEMET Inspire, GEMET-theme
        """
        print("Backup thesaurus...", end="\r")
        thesaurus_ref = ["external.theme.inspire-theme", "external.theme.gemet", "external.theme.gemet-theme",
                         "local.theme.geocat.ch"]

        headers = {"accept": "text/xml", "Content-Type": "text/xml", "X-XSRF-TOKEN": self.api.token}

        for thesaurus_name in thesaurus_ref:
            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/registries/vocabularies/{thesaurus_name}",
                                            proxies=self.api.proxies, auth=self.api.auth, headers=headers)

            with open(os.path.join(self.backup_dir, f"{thesaurus_name}.rdf"), 'wb') as file:
                file.write(response.content)

        print(f"Backup thesaurus {okgreen('Done')}")

    def backup_unpublish_report(self):
        """
        Backup the de-publication report in csv
        """
        response = self.api.session.get(url=self.api.env + "/geonetwork/srv/fre/unpublish.report.csv",
                                        proxies=self.api.proxies, auth=self.api.auth)

        with open(os.path.join(self.backup_dir, "unpublish_report.csv"), 'wb') as file:
            file.write(response.content)

