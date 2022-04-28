from geocat import GeocatAPI, okgreen, warningred
import xml.etree.ElementTree as ET
import os
import pysftp
import shutil
import sys

HOST_NAME = "upload-admin.geocat.ch"


class S3ConsistencyCheck:
    """
    Check the consistency of metadata in AWS S3 Bucket (Harvesting partner).

    Check if XML is well formed.
    Check if schema is correct. If at least the UUID is given correctly.
    Check if UUID is duplicated, used in more than one XML
    Check if number of correct XML (satisfying the 3 first tests) matches the number of metadata inside geocat.ch

    Args:
        group_id: str, the group ID corresponding to the S3 Bucket to check
        s3_path: str, the path of the Bucket from the root of the SFTP Server
        private_key: str, path to the SSH private Key (.rem, OpenSSH format)
        env: str, default="prod". Id set to "int", check the content of the Integration instance of geocat.ch

    Usage : S3-consistency-checker.py groupID={group ID} S3path={s3 path} pk={private key path} {-int}
    """
    def __init__(self, group_id: str, s3_path: str, private_key: str, env: str = "prod"):

        self.api = GeocatAPI(env)
        self.sftp_username = input("SFTP Username : ")
        self.group_id = group_id
        self.s3_path = s3_path
        self.private_key = private_key

        self.xml_error = []
        self.schema_error = []
        self.uuids = {}  # dictionary {uuid: file}
        self.duplicated_uuid = {}  # dictionary {uuid: [file1, file2, ...]}
        self.missing_uuid = []
        self.geocat_uuids = self.api.get_uuids_by_group(group_id=self.group_id)

        self.get_metadata_from_s3()
        self.check_consistency()
        self.print_results()

        shutil.rmtree(os.path.join(os.path.dirname(__file__), "tmp"))

    def get_metadata_from_s3(self):
        print("Downloading metadata from S3 : ", end="\r")
        output_dir = os.path.join(os.path.dirname(__file__), "tmp")

        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        srv = pysftp.Connection(host=HOST_NAME, username=self.sftp_username, private_key=self.private_key,
                                cnopts=cnopts)

        with srv.cd(self.s3_path):

            count = 0
            total = len(srv.listdir())
            for file in srv.listdir():
                srv.get(file, os.path.join(output_dir, file))
                count += 1
                print(f"Downloading metadata from S3 : {round((count / total) * 100, 1)}%", end="\r")

        print(f"Downloading metadata from S3 : {okgreen('Done')}")

    def check_consistency(self):
        print("Checking consistency : ", end="\r")

        count = 0
        total = len(os.listdir(os.path.join(os.path.dirname(__file__), "tmp")))

        for file in os.listdir(os.path.join(os.path.dirname(__file__), "tmp")):

            # Check if XML is well formed
            try:
                tree = ET.parse(os.path.join(os.path.join(os.path.dirname(__file__), "tmp"), file))
            except ET.ParseError:
                self.xml_error.append(file)
            else:
                root = tree.getroot()

                # Check if schema is ok (at least the UUID is found)
                try:
                    uuid = root.find("./{http://www.isotc211.org/2005/gmd}fileIdentifier/"
                                     "{http://www.isotc211.org/2005/gco}CharacterString").text
                except AttributeError:
                    self.schema_error.append(file)
                else:
                    # Check for duplicated UUID
                    if uuid not in self.uuids:
                        self.uuids[uuid] = file
                    else:
                        if uuid not in self.duplicated_uuid:
                            self.duplicated_uuid[uuid] = [file]
                            self.duplicated_uuid[uuid].append(self.uuids[uuid])
                        else:
                            self.duplicated_uuid[uuid].append(file)

            count += 1
            print(f"Checking consistency : {round((count / total) * 100)}%", end="\r")

        for uuid in self.uuids:
            if uuid not in self.geocat_uuids:
                self.missing_uuid.append(uuid)

        print(f"Checking consistency : {okgreen('Done')}")

    def print_results(self):
        print(f"Number of XML in S3 : {len(os.listdir(os.path.join(os.path.dirname(__file__), 'tmp')))}")
        print(f"Number of XML in geocat : {len(self.geocat_uuids)}")

        print("---")

        if len(self.xml_error) > 0:
            print(f"Number of not well formed XML : {warningred(len(self.xml_error))}")
            for i in self.xml_error:
                print(f"{warningred(i)}")
        else:
            print(f"Number of not well formed XML : {okgreen('0')}")

        print("---")

        if len(self.schema_error) > 0:
            print(f"Number of XML with wrong schema: {warningred(len(self.schema_error))}")
            for i in self.schema_error:
                print(f"{warningred(i)}")
        else:
            print(f"Number of XML with wrong schema : {okgreen('0')}")

        print("---")

        if len(self.duplicated_uuid) > 0:
            print(f"Number of duplicated UUID : {warningred(len(self.duplicated_uuid))}")
            for i in self.duplicated_uuid:
                dup_files = ""
                for j in self.duplicated_uuid[i]:
                    dup_files += j + ", "
                dup_files = dup_files[:-2]
                print(f"This UUID : {i} is used in {len(self.duplicated_uuid[i])} XML : {dup_files}")
        else:
            print(f"Number of duplicated UUID : {okgreen('0')}")

        print("---")

        if len(self.missing_uuid) > 0:
            print(f"Number of correct XML missing in geocat : {warningred(len(self.missing_uuid))}")
            for i in self.missing_uuid:
                print(f"{warningred(i)}")
        else:
            print(f"Number of correct XML missing in geocat : {okgreen('0')}")


if __name__ == "__main__":

    prod = True

    for arg in sys.argv:

        if arg.split("=")[0] == "groupID":
            group_id = arg.split("=")[1]

        elif arg.split("=")[0] == "S3path":
            s3_path = arg.split("=")[1]

        elif arg.split("=")[0] == "pk":
            private_key = arg.split("=")[1]

        if arg == "-int":
            prod = False

    if prod:
        S3ConsistencyCheck(group_id=group_id, s3_path=s3_path, private_key=private_key)
    else:
        S3ConsistencyCheck(group_id=group_id, s3_path=s3_path, private_key=private_key, env="int")


