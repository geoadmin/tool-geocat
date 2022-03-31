"""
This module aims at inspecting and managing (update & delete) administrative boundaries in geocat.ch

Administrative boundaries are stored as extent subtemplates in geocat. Any user can create a new extent subtemplate but
the admin boundaries (commune, canton, country) have been created and managed by the geocat team. They have a special
UUID structure making them easily accessible and thus manageable.

Usage examples :
    1) Inspect the municipalities. Compare geocat content with given geojson reference file.
        CheckMunicipalityBoundaries(ref_geojson=ref_geojson, gmdnr=GMDNR, gmdname=GMDNAME, output_dir=output_dir)

    2) Update and delete extent subtemplates.
        foo = UpdateSubtemplatesExtent(ref_geojson=ref_geojson, number=LANDNR, name=LANDNAME, type="l",
                                        output_dir=output_dir, update_name=False)
        foo.update_all_subtemplates()
        foo.delete_subtemplates(uuids=uuids)
"""

from geocat import GeocatAPI
from geocat import okgreen, warningred
from geocat import setup_logger
import os
import colorama
import pandas as pd
import xml.etree.ElementTree as ET
import json
import sys
from zipfile import ZipFile
import io
from datetime import datetime
from string import ascii_uppercase

colorama.init()


def geojson_to_geocatgml(geojson_feature: dict):
    """
    Transform a single geojson feature (type=Feature) into a GML ready for extent subtemplate of geocat.

    The geojson feature must be in WGS84. Coordinates of exterior polygons must be in the clock-wise order.
    Coordinates of interior polygons must be in the counter-clock-wise order.
    The returned GML starts at the tag <gmd:Polygon>.

    Args:
        geojson_feature:
            dict, required, geojson feature

    Returns:
        GML snippet at the tag level <gmd:Polygon> ready for extent subtemplate in geocat.
    """
    gml_start = "<gmd:polygon xmlns:gmd='http://www.isotc211.org/2005/gmd'>" \
                "<gml:MultiSurface xmlns='http://www.opengis.net/gml/3.2' xmlns:gml='http://www.opengis.net/gml/3.2' srsDimension='2'>"

    gml_end = "</gml:MultiSurface></gmd:polygon>"

    gml_core = ""

    # Exterior polygons

    if "coordinates" in geojson_feature["geometry"]:
        exteriors = geojson_feature["geometry"]["coordinates"]
    else:
        exteriors = geojson_feature["geometry"]["geometries"][0]["coordinates"]

    for exterior in exteriors:
        gml_core += "<gml:surfaceMember>" \
                    "<gml:Polygon>" \
                    "<gml:exterior>" \
                    "<gml:LinearRing>" \
                    "<gml:posList>"

        for coordinates in exterior[0]:
            gml_core += f"{coordinates[0]} {coordinates[1]} "
        gml_core = gml_core[:-1]  # remove the space once all coordinates are written

        gml_core += "</gml:posList>" \
                    "</gml:LinearRing>" \
                    "</gml:exterior>"

        # Interior polygons, if exist
        if len(exterior) > 1:
            for interior in exterior[1:]:
                gml_core += "<gml:interior>" \
                            "<gml:LinearRing>" \
                            "<gml:posList>"

                for coordinates in interior:
                    gml_core += f"{coordinates[0]} {coordinates[1]} "
                gml_core = gml_core[:-1]  # remove the space once all coordinates are written

                gml_core += "</gml:posList>" \
                            "</gml:LinearRing>" \
                            "</gml:interior>"

        gml_core += "</gml:Polygon>" \
                    "</gml:surfaceMember>"

    return gml_start + gml_core + gml_end


def process_ok(response):
    """
    Process the response of the geocat API requests.

    Works for following requests :
     - /{portal}/api/0.1/records/batchediting
     - /{portal}/api/0.1/records/validate
     - /{portal}/api/0.1/records/{metadataUuid}/ownership

    Args:
        response:
            object, required, the response object of the API request

    Returns:
        boolean: True if the process was successful, False if not
    """
    if response.status_code == 201:
        r_json = json.loads(response.text)
        if len(r_json["errors"]) == 0 and r_json["numberOfRecordNotFound"] == 0 \
                and r_json["numberOfRecordsNotEditable"] == 0 and r_json["numberOfNullRecords"] == 0 \
                and r_json["numberOfRecordsWithErrors"] == 0 and r_json["numberOfRecordsProcessed"] == 1:
            return True
        else:
            return False
    else:
        return False


class CheckMunicipalityBoundaries:
    """
    Check the municipalities admin boundaries from geocat by comparing them to a reference geojson file.
    The geojson file must be encoded in utf-8 to support special characters (accents).

    Args:
        ref_geojson:
            str, required ! The path to the reference geojson file.
        gmdnr:
            str, required ! The attribute name in the reference file corresponding to the municipalities BFS number
        gmdname:
            str, required ! The attribute name in the reference file corresponding to the municipalities name
        env:
            str, indicating the geocat's environment to work with, 'int' or 'prod', default = 'int'.
        output_dir:
            str, the directory path where to save the results, default = current directory.

    It saves 5 csv lists (if not empty):
            correct_municipalities.csv : ID and Name correct in geocat and reference
            name_incorrect_municipalities.csv : ID is found but Name is different in geocat
            id_incorrect_municipalities.csv : Name is found but ID is different in geocat
            new_municipalities.csv : ID and Name not found in geocat
            old_municipalities.csv : ID and Name not found in reference
    """

    def __init__(self, ref_geojson, gmdnr, gmdname, env: str = 'int', output_dir: str = os.path.dirname(__file__)):

        self.api = GeocatAPI(env)
        self.output_dir = output_dir
        self.ref_geojson = ref_geojson
        self.gmdnr = gmdnr
        self.gmdname = gmdname

        self.export_municipalities()
        self.check_gmd()
        self.check_old_municipalities_md_link()

    def export_municipalities(self):
        """
        Export all municipalities from geocat. I.e. subtemplates with UUID matching
        'geocatch-subtpl-extent-hoheitsgebiet-[1:10000].

        It saves a csv list named 'geocat_municipalities.csv' with the attributes GMDNR and GMDNAME at the root of
        the folder given at the class level.
        """
        print("Exporting all municipalities from geocat : ", end="\r")
        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.api.token}
        df = pd.DataFrame(columns=["GMDNR", "GMDNAME"])

        count = 0
        for i in range(1, 10000):

            uuid = f"geocatch-subtpl-extent-hoheitsgebiet-{i}"
            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/registries/entries/{uuid}",
                                            proxies=self.api.proxies, auth=self.api.auth, headers=headers)

            xmlroot = ET.fromstring(response.content)

            if xmlroot.tag != "apiError":
                gmd_name = xmlroot.find("{http://www.isotc211.org/2005/gmd}description").find(
                    "{http://www.isotc211.org/2005/gco}CharacterString").text

                df = df.append({"GMDNR": i, "GMDNAME": gmd_name}, ignore_index=True)

            count += 1
            print(f"Exporting all municipalities from geocat : {round((count / 10000) * 100, 1)}%", end="\r")

        df.to_csv(os.path.join(self.output_dir, "geocat_municipalities.csv"), index=False)
        print(f"Exporting all municipalities from geocat : {okgreen('Done')}")

    def check_gmd(self):
        """
        Compare the municipalities (names and id) from geocat (i.e. from the csv list created by the
        export_municipalities function) with the municipalities from the reference geojson file.

        It saves 5 csv lists at the root of the folder given at the class level :
                correct_municipalities.csv : ID and Name correct in geocat and reference
                name_incorrect_municipalities.csv : ID is found but Name is different in geocat
                id_incorrect_municipalities.csv : Name is found but ID is different in geocat
                new_municipalities.csv : ID and Name not found in geocat
                old_municipalities.csv : ID and Name not found in reference
        """
        print("Checking municipalities...", end="\r")

        with open(self.ref_geojson, "rb") as file:
            geojson_ref_file = json.load(file)

        df_geocat = pd.read_csv(os.path.join(self.output_dir, "geocat_municipalities.csv"))

        df_name_change = pd.DataFrame(columns=["GMDNR", "GMDNAME_new", "GMDNAME_old"])
        df_id_change = pd.DataFrame(columns=["GMDNAME", "GMDNR_new", "GMDNR_old"])
        df_new = pd.DataFrame(columns=["GMDNR", "GMDNAME"])
        df_old = pd.DataFrame(columns=["GMDNR", "GMDNAME"])
        df_correct = pd.DataFrame(columns=["GMDNR", "GMDNAME"])

        # 1 - Testing new municipalities against geocat
        for feature in geojson_ref_file[0]["features"]:
            gmdnr = feature["properties"][self.gmdnr]
            gmdname = feature["properties"][self.gmdname]

            # Case where id exists but name is different
            if gmdnr in df_geocat.values:
                if gmdname != df_geocat.loc[df_geocat["GMDNR"] == gmdnr].iloc[0]["GMDNAME"]:
                    df_name_change = df_name_change.append({
                        "GMDNR": gmdnr,
                        "GMDNAME_new": gmdname,
                        "GMDNAME_old": df_geocat.loc[df_geocat["GMDNR"] == gmdnr].iloc[0]["GMDNAME"],
                    }, ignore_index=True)
                else:
                    df_correct = df_correct.append({
                        "GMDNR": gmdnr,
                        "GMDNAME": gmdname,
                    }, ignore_index=True)
            # Case where id is different for a given name
            else:
                if gmdname in df_geocat.values:
                    df_id_change = df_id_change.append({
                        "GMDNAME": gmdname,
                        "GMDNR_new": gmdnr,
                        "GMDNR_old": df_geocat.loc[df_geocat["GMDNAME"] == gmdname].iloc[0]["GMDNR"],
                    }, ignore_index=True)
                # Case where id and name doesn't exist. New municipality to add to geocat.
                else:
                    df_new = df_new.append({
                        "GMDNAME": gmdname,
                        "GMDNR": gmdnr,
                    }, ignore_index=True)

        # 2 - Testing geocat against new municipalities
        ref_gmdnrs = [feature["properties"][self.gmdnr] for feature in geojson_ref_file[0]["features"]]
        ref_gmdnames = [feature["properties"][self.gmdname] for feature in geojson_ref_file[0]["features"]]

        for index, row in df_geocat.iterrows():

            # Case where municipalities in geocat doesn't exist at all (no id, no name) in the new ones
            if (row["GMDNR"] not in ref_gmdnrs) and (row["GMDNAME"] not in ref_gmdnames):
                df_old = df_old.append({
                    "GMDNAME": row["GMDNAME"],
                    "GMDNR": row["GMDNR"],
                }, ignore_index=True)

        if len(df_name_change) > 0:
            df_name_change.to_csv(os.path.join(self.output_dir, "name_incorrect_municipalities.csv"), index=False)
        if len(df_id_change) > 0:
            df_id_change.to_csv(os.path.join(self.output_dir, "id_incorrect_municipalities.csv"), index=False)
        if len(df_new) > 0:
            df_new.to_csv(os.path.join(self.output_dir, "new_municipalities.csv"), index=False)
        if len(df_old) > 0:
            df_old.to_csv(os.path.join(self.output_dir, "old_municipalities.csv"), index=False)
        if len(df_correct) > 0:
            df_correct.to_csv(os.path.join(self.output_dir, "correct_municipalities.csv"), index=False)

        print(f"Checking municipalities...{okgreen('Done')}")

    def get_harvested_uuid(self) -> list:
        """
        Get all uuid from harvested metadata

        Returns:
            List of all UUIDs
        """
        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.api.token}
        uuid = []
        start = 1

        while True:
            parameters = {
                "facet.q": "isHarvested/y",
                "from": start,
            }

            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/fre/q", proxies=self.api.proxies,
                                            auth=self.api.auth, headers=headers, params=parameters)

            xmlroot = ET.fromstring(response.content)
            metadatas = xmlroot.findall("metadata")

            if len(metadatas) == 0:
                break

            for metadata in metadatas:
                if metadata.find("*/uuid").text not in uuid:
                    uuid.append(metadata.find("*/uuid").text)

            start += 1499

        return uuid

    def export_harvested_md(self) -> list:
        """
        Export all harvested metadata.

        Export a MEF archive per metadata and extract the metadata XML from it. The list of UUID is taken by the
        get_harvested_uuid method.

        Returns:
            List of metadata in byte string corresponding to XML
        """

        print("Export all harvested metadata :", end="\r")

        # Get list of harvested metadata UUID
        uuids = self.get_harvested_uuid()
        headers = {"accept": "application/x-gn-mef-2-zip", "X-XSRF-TOKEN": self.api.token}

        metadata = []

        count = 0
        for uuid in uuids:

            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/records/{uuid}/formatters/zip",
                                            proxies=self.api.proxies, auth=self.api.auth, headers=headers)

            with ZipFile(io.BytesIO(response.content)) as zip:
                if f'{uuid}/metadata/metadata.xml' in zip.namelist():
                    metadata.append(zip.read(f'{uuid}/metadata/metadata.xml'))

            count += 1
            print(f"Export all harvested metadata : {round((count / len(uuids)) * 100, 1)}%", end="\r")
        print(f"Export all harvested metadata : {okgreen('Done')}")

        return metadata

    def check_old_municipalities_md_link(self):
        """
        Check if the municipalities in geocat from the CSV list old_municipalities.csv are linked to metadata.

        Check both the normal metadata and the harvested ones (even if they normally don't contain subtemplates).
        Updates the CSV list old_municipalities.csv with a attribute 'MD_linked' corresponding to the number of
        metadata records that use the municipality.
        """

        # 1)   Check if extent subtemplates are linked to not harvested metadata. Uses the catalogue MEF.
        print("Export Catalogue as MEF...", end="\r")
        headers = {"accept": "application/zip", "Content-Type": "application/zip", "X-XSRF-TOKEN": self.api.token}
        response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/records/backups/latest",
                                        proxies=self.api.proxies, auth=self.api.auth, headers=headers)

        with ZipFile(io.BytesIO(response.content)) as zip:
            print(f"Export Catalogue as MEF {okgreen('Done')}")

            df_old_gmd = pd.read_csv(os.path.join(self.output_dir, "old_municipalities.csv"))
            df_old_gmd_link = pd.DataFrame(columns=["GMDNR", "GMDNAME", "MD_Linked"])

            print(f"Fetching all UUID in MD : ", end="\r")
            hrefs = []

            total = len([i for i in zip.namelist() if i.split('/')[-1] == "metadata.xml"])
            count = 0
            for md in [i for i in zip.namelist() if i.split('/')[-1] == "metadata.xml"]:

                xml_string = zip.open(md).read().decode('utf-8')
                xmlroot = ET.fromstring(xml_string)

                for href in xmlroot.findall('.//*[@{http://www.w3.org/1999/xlink}href]'):
                    hrefs.append(href.attrib["{http://www.w3.org/1999/xlink}href"].split("registries/entries/")[-1].split(" ")[0].split("/")[0].split("?")[0])

                count += 1
                print(f"Fetching all UUID in MD : {round((count / total) * 100, 1)}%", end="\r")
            print(f"Fetching all UUID in MD : {okgreen('Done')}")

            print(f"Checking if municipalities are linked in MD : ", end="\r")
            total = len(df_old_gmd)
            count = 0

            for index, row in df_old_gmd.iterrows():

                uuid = f"geocatch-subtpl-extent-hoheitsgebiet-{row['GMDNR']}"

                df_old_gmd_link = df_old_gmd_link.append({
                    "GMDNR": row["GMDNR"],
                    "GMDNAME": row["GMDNAME"],
                    "MD_Linked": hrefs.count(uuid),
                }, ignore_index=True)

                count += 1
                print(f"Checking if municipalities are linked in MD : {round((count / total) * 100, 1)}%", end="\r")

            print(f"Checking if municipalities are linked in MD : {okgreen('Done')}")

        # 2)    Check if extent subtemplates are linked to harvested metadata. Uses the xml exported by
        #       the export_harvested_md method.
        metadata = self.export_harvested_md()

        total = len(metadata)
        count = 0
        print(f"Fetching all UUID in harvested MD : ", end="\r")

        hrefs = []

        for md in metadata:
            xmlroot = ET.fromstring(md.decode('utf-8'))

            for href in xmlroot.findall('.//*[@{http://www.w3.org/1999/xlink}href]'):
                hrefs.append(href.attrib["{http://www.w3.org/1999/xlink}href"].split("registries/entries/")[-1].split(" ")[0].split("/")[0].split("?")[0])

            count += 1
            print(f"Fetching all UUID in harvested MD : {round((count / total) * 100, 1)}%", end="\r")
        print(f"Fetching all UUID in harvested MD : {okgreen('Done')}")

        print(f"Checking if municipalities are linked in harvested MD : ", end="\r")
        total = len(df_old_gmd_link)
        count = 0
        for index, row in df_old_gmd_link.iterrows():

            gmd_link = row["MD_Linked"]
            uuid = f"geocatch-subtpl-extent-hoheitsgebiet-{row['GMDNR']}"
            gmd_link += hrefs.count(uuid)

            df_old_gmd_link.at[index, "MD_Linked"] = gmd_link

            count += 1
            print(f"Checking if municipalities are linked in harvested MD : {round((count / total) * 100, 1)}%", end="\r")

        df_old_gmd_link.to_csv(os.path.join(self.output_dir, "old_municipalities.csv"), index=False)
        print(f"Checking if municipalities are linked in harvested MD : {okgreen('Done')}")


class CheckCantonBoundaries:
    """
    Check the cantons admin boundaries from geocat by comparing them to a reference geojson file.
    The geojson file must be encoded in utf-8 to support special characters (accents).

    Args:
        ref_geojson:
            str, required ! The path to the reference geojson file.
        ktnr:
            str, required ! The attribute name in the reference file corresponding to the canton BFS number
        ktname:
            str, required ! The attribute name in the reference file corresponding to the canton name
        env:
            str, indicating the geocat's environment to work with, 'int' or 'prod', default = 'int'.
        output_dir:
            str, the directory path where to save the results, default = current directory.

    It saves 5 csv lists (if not empty):
            correct_cantons.csv : ID and Name correct in geocat and reference
            name_incorrect_cantons.csv : ID is found but Name is different in geocat
            id_incorrect_cantons.csv : Name is found but ID is different in geocat
            new_cantons.csv : ID and Name not found in geocat
            old_cantons.csv : ID and Name not found in reference
    """

    def __init__(self, ref_geojson, ktnr, ktname, env: str = 'int', output_dir: str = os.path.dirname(__file__)):

        self.api = GeocatAPI(env)
        self.output_dir = output_dir
        self.ref_geojson = ref_geojson
        self.ktnr = ktnr
        self.ktname = ktname

        self.export_cantons()
        self.check_kt()

    def export_cantons(self):
        """
        Export all cantons from geocat. I.e. subtemplates with UUID matching
        'geocatch-subtpl-extent-kantonsgebiet-[1:100]'.

        It saves a csv list named 'geocat_cantons.csv' with the attributes KTNR and KTNAME at the root of
        the folder given at the class level.
        """
        print("Exporting all cantons from geocat : ", end="\r")
        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.api.token}
        df = pd.DataFrame(columns=["KTNR", "KTNAME"])

        count = 0
        for i in range(1, 100):

            uuid = f"geocatch-subtpl-extent-kantonsgebiet-{i}"
            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/registries/entries/{uuid}",
                                            proxies=self.api.proxies, auth=self.api.auth, headers=headers)

            xmlroot = ET.fromstring(response.content)

            if xmlroot.tag != "apiError":
                kt_name = xmlroot.find("{http://www.isotc211.org/2005/gmd}description").find(
                    "{http://www.isotc211.org/2005/gco}CharacterString").text

                df = df.append({"KTNR": i, "KTNAME": kt_name}, ignore_index=True)

            count += 1
            print(f"Exporting all cantons from geocat : {round((count / 100) * 100, 1)}%", end="\r")

        df.to_csv(os.path.join(self.output_dir, "geocat_cantons.csv"), index=False)
        print(f"Exporting all cantons from geocat : {okgreen('Done')}")

    def check_kt(self):
        """
        Compare the cantons (names and id) from geocat (i.e. from the csv list created by the
        export_cantons function) with the cantons from the reference geojson file.

        It saves 5 csv lists at the root of the folder given at the class level (if not emtpy) :
                correct_cantons.csv : ID and Name correct in geocat and reference
                name_incorrect_cantons.csv : ID is found but Name is different in geocat
                id_incorrect_cantons.csv : Name is found but ID is different in geocat
                new_cantons.csv : ID and Name not found in geocat
                old_cantons.csv : ID and Name not found in reference
        """
        print("Checking cantons...", end="\r")

        with open(self.ref_geojson, "rb") as file:
            geojson_ref_file = json.load(file)

        df_geocat = pd.read_csv(os.path.join(self.output_dir, "geocat_cantons.csv"))

        df_name_change = pd.DataFrame(columns=["KTNR", "KTNAME_new", "KTNAME_old"])
        df_id_change = pd.DataFrame(columns=["KTNAME", "KTNR_new", "KTNR_old"])
        df_new = pd.DataFrame(columns=["KTNR", "KTNAME"])
        df_old = pd.DataFrame(columns=["KTNR", "KTNAME"])
        df_correct = pd.DataFrame(columns=["KTNR", "KTNAME"])

        # 1 - Testing new cantons against geocat
        for feature in geojson_ref_file[0]["features"]:
            ktnr = feature["properties"][self.ktnr]
            ktname = feature["properties"][self.ktname]

            # Case where id exists but name is different
            if ktnr in df_geocat.values:
                if ktname != df_geocat.loc[df_geocat["KTNR"] == ktnr].iloc[0]["KTNAME"]:
                    df_name_change = df_name_change.append({
                        "KTNR": ktnr,
                        "KTNAME_new": ktname,
                        "KTNAME_old": df_geocat.loc[df_geocat["KTNR"] == ktnr].iloc[0]["KTNAME"],
                    }, ignore_index=True)
                else:
                    df_correct = df_correct.append({
                        "KTNR": ktnr,
                        "KTNAME": ktname,
                    }, ignore_index=True)
            # Case where id is different for a given name
            else:
                if ktname in df_geocat.values:
                    df_id_change = df_id_change.append({
                        "KTNAME": ktname,
                        "KTNR_new": ktnr,
                        "KTNR_old": df_geocat.loc[df_geocat["KTNAME"] == ktname].iloc[0]["KTNR"],
                    }, ignore_index=True)
                # Case where id and name doesn't exist. New canton to add to geocat.
                else:
                    df_new = df_new.append({
                        "KTNAME": ktname,
                        "KTNR": ktnr,
                    }, ignore_index=True)

        # 2 - Testing geocat against new cantons
        ref_ktnrs = [feature["properties"][self.ktnr] for feature in geojson_ref_file[0]["features"]]
        ref_ktnames = [feature["properties"][self.ktname] for feature in geojson_ref_file[0]["features"]]

        for index, row in df_geocat.iterrows():

            # Case where cantons in geocat doesn't exist at all (no id, no name) in the new ones
            if (row["KTNR"] not in ref_ktnrs) and (row["KTNAME"] not in ref_ktnames):
                df_old = df_old.append({
                    "KTNAME": row["KTNAME"],
                    "KTNR": row["KTNR"],
                }, ignore_index=True)

        if len(df_name_change) > 0:
            df_name_change.to_csv(os.path.join(self.output_dir, "name_incorrect_cantons.csv"), index=False)
        if len(df_id_change) > 0:
            df_id_change.to_csv(os.path.join(self.output_dir, "id_incorrect_cantons.csv"), index=False)
        if len(df_new) > 0:
            df_new.to_csv(os.path.join(self.output_dir, "new_cantons.csv"), index=False)
        if len(df_old) > 0:
            df_old.to_csv(os.path.join(self.output_dir, "old_cantons.csv"), index=False)
        if len(df_correct) > 0:
            df_correct.to_csv(os.path.join(self.output_dir, "correct_cantons.csv"), index=False)

        print(f"Checking cantons...{okgreen('Done')}")


class CheckCountryBoundaries:
    """
    Check the countries admin boundaries from geocat by comparing them to a reference geojson file.
    The geojson file must be encoded in utf-8 to support special characters (accents).

    Args:
        ref_geojson:
            str, required ! The path to the reference geojson file.
        landnr:
            str, required ! The attribute name in the reference file corresponding to the canton BFS number
        landname:
            str, required ! The attribute name in the reference file corresponding to the canton name
        env:
            str, indicating the geocat's environment to work with, 'int' or 'prod', default = 'int'.
        output_dir:
            str, the directory path where to save the results, default = current directory.

    It saves 5 csv lists (if not empty):
            correct_countries.csv : ID and Name correct in geocat and reference
            name_incorrect_countries.csv : ID is found but Name is different in geocat
            id_incorrect_countries.csv : Name is found but ID is different in geocat
            new_countries.csv : ID and Name not found in geocat
            old_countries.csv : ID and Name not found in reference
    """

    def __init__(self, ref_geojson, landnr, landname, env: str = 'int', output_dir: str = os.path.dirname(__file__)):

        self.api = GeocatAPI(env)
        self.output_dir = output_dir
        self.ref_geojson = ref_geojson
        self.landnr =landnr
        self.landname = landname

        self.export_countries()
        self.check_land()

    def export_countries(self):
        """
        Export all countries from geocat. I.e. subtemplates with UUID matching
        'geocatch-subtpl-extent-landesgebiet-[A:Z][A:Z]'.

        It saves a csv list named 'geocat_countries.csv' with the attributes LANDNR and LANDNAME at the root of
        the folder given at the class level.
        """
        print("Exporting all countries from geocat : ", end="\r")
        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.api.token}
        df = pd.DataFrame(columns=["LANDNR", "LANDNAME"])

        count = 0
        for first in ascii_uppercase:
            for second in ascii_uppercase:
                uuid = f"geocatch-subtpl-extent-landesgebiet-{first}{second}"

                response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/registries/entries/{uuid}",
                                                proxies=self.api.proxies, auth=self.api.auth, headers=headers)

                xmlroot = ET.fromstring(response.content)

                if xmlroot.tag != "apiError":
                    land_name = xmlroot.find("{http://www.isotc211.org/2005/gmd}description").find(
                        "{http://www.isotc211.org/2005/gco}CharacterString").text

                    df = df.append({"LANDNR": first + second, "LANDNAME": land_name}, ignore_index=True)

                count += 1
                print(f"Exporting all countries from geocat : {round((count / (26*26)) * 100, 1)}%", end="\r")

        df.to_csv(os.path.join(self.output_dir, "geocat_countries.csv"), index=False)
        print(f"Exporting all countries from geocat : {okgreen('Done')}")

    def check_land(self):
        """
        Compare the countries (names and id) from geocat (i.e. from the csv list created by the
        export_countries function) with the countries from the reference geojson file.

        It saves 5 csv lists at the root of the folder given at the class level (if not emtpy) :
                correct_countries.csv : ID and Name correct in geocat and reference
                name_incorrect_countries.csv : ID is found but Name is different in geocat
                id_incorrect_countries.csv : Name is found but ID is different in geocat
                new_countries.csv : ID and Name not found in geocat
                old_countries.csv : ID and Name not found in reference
        """
        print("Checking countries...", end="\r")

        with open(self.ref_geojson, "rb") as file:
            geojson_ref_file = json.load(file)

        df_geocat = pd.read_csv(os.path.join(self.output_dir, "geocat_countries.csv"))

        df_name_change = pd.DataFrame(columns=["LANDNR", "LANDNAME_new", "LANDNAME_old"])
        df_id_change = pd.DataFrame(columns=["LANDNAME", "LANDNR_new", "LANDNR_old"])
        df_new = pd.DataFrame(columns=["LANDNR", "LANDNAME"])
        df_old = pd.DataFrame(columns=["LANDNR", "LANDNAME"])
        df_correct = pd.DataFrame(columns=["LANDNR", "LANDNAME"])

        # 1 - Testing new countries against geocat
        for feature in geojson_ref_file[0]["features"]:
            landnr = feature["properties"][self.landnr]
            landname = feature["properties"][self.landname]

            # Case where id exists but name is different
            if landnr in df_geocat.values:
                if landname != df_geocat.loc[df_geocat["LANDNR"] == landnr].iloc[0]["LANDNAME"]:
                    df_name_change = df_name_change.append({
                        "LANDNR": landnr,
                        "LANDNAME_new": landname,
                        "LANDNAME_old": df_geocat.loc[df_geocat["LANDNR"] == landnr].iloc[0]["LANDNAME"],
                    }, ignore_index=True)
                else:
                    df_correct = df_correct.append({
                        "LANDNR": landnr,
                        "LANDNAME": landname,
                    }, ignore_index=True)
            # Case where id is different for a given name
            else:
                if landname in df_geocat.values:
                    df_id_change = df_id_change.append({
                        "LANDNAME": landname,
                        "LANDNR_new": landnr,
                        "LANDNR_old": df_geocat.loc[df_geocat["LANDNAME"] == landname].iloc[0]["LANDNR"],
                    }, ignore_index=True)
                # Case where id and name doesn't exist. New country to add to geocat.
                else:
                    df_new = df_new.append({
                        "LANDNAME": landname,
                        "LANDNR": landnr,
                    }, ignore_index=True)

        # 2 - Testing geocat against new countries
        ref_landnrs = [feature["properties"][self.landnr] for feature in geojson_ref_file[0]["features"]]
        ref_landnames = [feature["properties"][self.landname] for feature in geojson_ref_file[0]["features"]]

        for index, row in df_geocat.iterrows():

            # Case where countries in geocat doesn't exist at all (no id, no name) in the new ones
            if (row["LANDNR"] not in ref_landnrs) and (row["LANDNAME"] not in ref_landnames):
                df_old = df_old.append({
                    "LANDNAME": row["LANDNAME"],
                    "LANDNR": row["LANDNR"],
                }, ignore_index=True)

        if len(df_name_change) > 0:
            df_name_change.to_csv(os.path.join(self.output_dir, "name_incorrect_countries.csv"), index=False)
        if len(df_id_change) > 0:
            df_id_change.to_csv(os.path.join(self.output_dir, "id_incorrect_countries.csv"), index=False)
        if len(df_new) > 0:
            df_new.to_csv(os.path.join(self.output_dir, "new_countries.csv"), index=False)
        if len(df_old) > 0:
            df_old.to_csv(os.path.join(self.output_dir, "old_countries.csv"), index=False)
        if len(df_correct) > 0:
            df_correct.to_csv(os.path.join(self.output_dir, "correct_countries.csv"), index=False)

        print(f"Checking countries...{okgreen('Done')}")


class UpdateSubtemplatesExtent:
    """
    Update extent subtemplate in geocat with a geojson file as reference.

    The geojson file must be in WGS84. Coordinates of exterior polygons must be in the clock-wise order.
    Coordinates of interior polygons must be in the counter-clock-wise order. The file must be encoded in utf-8
    to support special characters (accents).

    Args:
        ref_geojson:
            str, required ! The path to the reference geojson file.
        number:
            str, required ! The attribute name in the reference file corresponding to the municipalities BFS number
        name:
            str, required ! The attribute name in the reference file corresponding to the municipalities name
        type:
            str, required ! "g" for municipalities, "k" for cantons, "l" for country
        env:
            str, indicating the geocat's environment to work with, 'int' or 'prod', default = 'int'.
        output_dir:
            str, the directory path where to save the backups and logfile, default = current directory.
    """

    def __init__(self, ref_geojson, number, name, type, update_name: bool = True, env: str = 'int',
                 output_dir: str = os.path.dirname(__file__)):

        self.api = GeocatAPI(env)

        with open(ref_geojson, "rb") as file:
            self.ref_geojson = json.load(file)

        self.number = number
        self.name = name
        self.output_dir = output_dir
        self.update_name = update_name

        if type == "g":
            self.type = "hoheitsgebiet"
        elif type == "k":
            self.type = "kantonsgebiet"
        elif type == "l":
            self.type = "landesgebiet"

        if not update_name:
            print(f"{warningred('The update_name option is set to False ! Creation of new extent not possible !')}")

        if not GeocatAPI.check_admin(self.api):
            print(f"{warningred('You must be admin to run this tool !')}")
            sys.exit()

    def extent_to_geojson(self, uuids: list) -> list:
        """
        Convert geocat extent subtemplates into geojson.

        Takes several extent subtemplates and convert them into a single json string (geojson). The geojson is a
        features collection with one feature per extent. The geojson structure corresponds to the geojson given as input
        at the class level.

        Args:
            uuids : required, list of extent subtemplates uuid to convert into a single geojson

        Returns:
            A list in geojson format
        """

        # Initialize the geojson
        print("Convert extent subtemplates to geojson : ", end="\r")

        now = datetime.now().strftime("%Y%m%d%H%M%S")
        geojson = [{"type": "FeatureCollection", "name": f"GeocatExtent_{now}", "features": []}]

        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.api.token}

        count = 0
        for uuid in uuids:

            response = self.api.session.get(
                url=self.api.env + f"/geonetwork/srv/api/0.1/registries/entries/{uuid}?lang=fre,ger,ita,eng,roh",
                proxies=self.api.proxies, auth=self.api.auth, headers=headers)

            if response.status_code == 200:

                # Initialize a new feature with geometry type MultiPolygon inside the geojson (features collection)
                geojson[0]["features"].append({"type": "Feature",
                                               "geometry": {"type": "MultiPolygon", "coordinates": []},
                                               "properties": {}})

                xmlroot = ET.fromstring(response.content)

                # Extract principal name and multilingual names and store them into the geojson
                name = xmlroot.find('{http://www.isotc211.org/2005/gmd}description/{'
                                    'http://www.isotc211.org/2005/gco}CharacterString').text
                name_de = xmlroot.find('{http://www.isotc211.org/2005/gmd}description').find(
                          './/{http://www.isotc211.org/2005/gmd}LocalisedCharacterString[@locale="#DE"]').text
                name_fr = xmlroot.find('{http://www.isotc211.org/2005/gmd}description').find(
                          './/{http://www.isotc211.org/2005/gmd}LocalisedCharacterString[@locale="#FR"]').text
                name_it = xmlroot.find('{http://www.isotc211.org/2005/gmd}description').find(
                          './/{http://www.isotc211.org/2005/gmd}LocalisedCharacterString[@locale="#IT"]').text
                name_en = xmlroot.find('{http://www.isotc211.org/2005/gmd}description').find(
                          './/{http://www.isotc211.org/2005/gmd}LocalisedCharacterString[@locale="#EN"]').text
                name_rm = xmlroot.find('{http://www.isotc211.org/2005/gmd}description').find(
                          './/{http://www.isotc211.org/2005/gmd}LocalisedCharacterString[@locale="#RM"]').text

                geojson[0]["features"][-1]["properties"][self.name] = name
                geojson[0]["features"][-1]["properties"][f"{self.name}_DE"] = name_de
                geojson[0]["features"][-1]["properties"][f"{self.name}_FR"] = name_fr
                geojson[0]["features"][-1]["properties"][f"{self.name}_IT"] = name_it
                geojson[0]["features"][-1]["properties"][f"{self.name}_EN"] = name_en
                geojson[0]["features"][-1]["properties"][f"{self.name}_RM"] = name_rm

                # Add the BFS number to the geojson. If type=landesgebiet, the number is not an integer
                if self.type == "landesgebiet":
                    geojson[0]["features"][-1]["properties"][self.number] = uuid.split('-')[-1]
                else:
                    geojson[0]["features"][-1]["properties"][self.number] = int(uuid.split('-')[-1])

                # Extract geometry and store it into the geojson
                for exterior in xmlroot.findall(".//{http://www.opengis.net/gml/3.2}surfaceMember"):

                    # Initialize an exterior polygon
                    geojson[0]["features"][-1]["geometry"]["coordinates"].append([[]])

                    exterior_poly = exterior.find(".//{http://www.opengis.net/gml/3.2}exterior").find(
                        ".//{http://www.opengis.net/gml/3.2}posList")

                    coordinates = exterior_poly.text.split(" ")

                    # Coordinates order is normal (lng-lat)
                    if "srsDimension" not in exterior_poly.attrib:
                        for i in range(0, len(coordinates), 2):
                            geojson[0]["features"][-1]["geometry"]["coordinates"][-1][-1].append(
                                [float(coordinates[i]), float(coordinates[i + 1])])

                    # Coordinates order is inverted (lat-lng)
                    else:
                        for i in range(0, len(coordinates), 2):
                            geojson[0]["features"][-1]["geometry"]["coordinates"][-1][-1].append(
                                [float(coordinates[i + 1]), float(coordinates[i])])

                    # Go through all potential interior polygons (holes) of the exterior polygon
                    for interior in exterior.findall(".//{http://www.opengis.net/gml/3.2}interior"):

                        # Initialize an interior polygon
                        geojson[0]["features"][-1]["geometry"]["coordinates"][-1].append([])

                        interior_poly = interior.find(".//{http://www.opengis.net/gml/3.2}posList")

                        coordinates = interior_poly.text.split(" ")

                        # Coordinates order is normal (lng-lat)
                        if "srsDimension" not in interior_poly.attrib:
                            for i in range(0, len(coordinates), 2):
                                geojson[0]["features"][-1]["geometry"]["coordinates"][-1][-1].append(
                                    [float(coordinates[i]), float(coordinates[i + 1])])

                        # Coordinates order is inverted (lat-lng)
                        else:
                            for i in range(0, len(coordinates), 2):
                                geojson[0]["features"][-1]["geometry"]["coordinates"][-1][-1].append(
                                    [float(coordinates[i + 1]), float(coordinates[i])])

            count += 1
            print(f"Convert extent subtemplates to geojson : {round((count / len(uuids)) * 100, 1)}%", end="\r")
        print(f"Convert extent subtemplates to geojson : {okgreen('Done')}")

        return geojson

    def backup_subtemplates(self):
        """
        Backup all subtemplates that are in the reference geojson file. It uses the method extent_to_geojson
        to generate the geojson

        Save the subtemplates into a single geojson (FeaturesCollection)
        """
        print("Backup subtemplates...")

        output_dir_backup = os.path.join(self.output_dir, "subtemplates_backup")

        if not os.path.exists(output_dir_backup):
            os.mkdir(output_dir_backup)

        uuids = []
        for feature in self.ref_geojson[0]["features"]:
            uuid = f"geocatch-subtpl-extent-{self.type}-{feature['properties'][self.number]}"
            uuids.append(uuid)

        geojson = self.extent_to_geojson(uuids)
        now = datetime.now().strftime("%Y%m%d%H%M%S")

        with open(os.path.join(output_dir_backup, f"Backup_{now}.json"), "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False)

        print(f"Backup subtemplates...{okgreen('Done')}")

    def create_extent(self, uuid: str) -> object:
        """
        Create a new extent subtemplate with the given uuid. It duplicates an existing
        subtemplate : geocatch-subtpl-extent-{type}-1.

        Args:
            uuid:
                string, required, uuid for the subtemplate to be created.

        Returns:
            response of the duplicate API request.
        """

        # Creates a new subtemplate only if the name should be updated.
        # Otherwise, the name will be from the copied subtemplate
        if self.update_name:
            headers = {"Content-Type": "application/json", "Accept": "application/json", "X-XSRF-TOKEN": self.api.token}
            parameters = {
                "metadataType": "SUB_TEMPLATE",
                "sourceUuid": f"geocatch-subtpl-extent-hoheitsgebiet-1",
                "targetUuid": uuid,
                "group": "1",
                "isVisibleByAllGroupMembers": "false",
                "hasCategoryOfSource": "false",
                "isChildOfSource": "false",
            }

            response = self.api.session.put(url=self.api.env + "/geonetwork/srv/api/0.1/records/duplicate",
                                            proxies=self.api.proxies, auth=self.api.auth, headers=headers,
                                            params=parameters)
            return response

        else:
            # Create a dummy class to return an object with the variable "status_code" = 404. Hence, when the option
            # update_name is set to false, no new subtemplate is created and the response returned has an unvalid code.
            class Response:
                def __init__(self):
                    self.status_code = 404

            response = Response()
            return response

    def update_extent(self, uuid: str, name: str, gml: str) -> object:
        """
        Update the name and geometry of the given extent subtemplate.

        Args:
            uuid:
                string, required, the extent subtemplate uuid
            name:
                string, required, the new name
            gml:
                string, required, the new geometry (GML)

        Returns:
            response of the batch editing API request.
        """
        body = [
            # Delete surfaceMember section
            {
                "xpath": "/gmd:EX_Extent/gmd:geographicElement/gmd:EX_BoundingPolygon/gmd:polygon",
                "value": '<gn_delete></gn_delete>',
            },
            # add new surfaceMember section
            {
                "xpath": "/gmd:EX_Extent/gmd:geographicElement/gmd:EX_BoundingPolygon",
                "value": f"<gn_add>{gml}</gn_add>",
            },
        ]

        # If update name is choosen
        if self.update_name:
            body.insert(0, {
                    "xpath": "/gmd:EX_Extent/gmd:description/gmd:PT_FreeText/gmd:textGroup/gmd:LocalisedCharacterString",
                    "value": f'<gn_replace>{name}</gn_replace>',
                })

        response = self.api.edit_metadata(uuid=uuid, body=body, updateDateStamp="true")

        return response

    def validate_extent(self, uuid: str) -> object:
        """
        Validate the extent subtemplate.

        Args:
            uuid:
                string, required, the extent subtemplate uuid

        Returns:
            response of the validate API request.
        """
        headers = {"Content-Type": "application/json", "Accept": "application/json", "X-XSRF-TOKEN": self.api.token}
        parameters = {
            "uuids": [uuid],
        }

        response = self.api.session.put(url=self.api.env + "/geonetwork/srv/api/0.1/records/validate",
                                        proxies=self.api.proxies, auth=self.api.auth, headers=headers,
                                        params=parameters)
        return response

    def set_extent_permissions(self, uuid: str) -> object:
        """
        Set the permission of the extent subtemplate. Gives to group=1 (all) read permission.

        Args:
            uuid:
                string, required, the extent subtemplate uuid

        Returns:
            response of the sharing API request.
        """
        headers = {"Content-Type": "application/json", "Accept": "application/json", "X-XSRF-TOKEN": self.api.token}

        body = {
            "clear": True,
            "privileges": [
                {
                    "group": 1,
                    "operations": {
                        "view": True,
                        "download": False,
                        "dynamic": False,
                        "featured": False,
                        "notify": False,
                        "editing": False
                    }
                }
            ]
        }

        body = json.dumps(body)

        response = self.api.session.put(url=self.api.env + f"/geonetwork/srv/api/0.1/records/{uuid}/sharing",
                                        proxies=self.api.proxies, auth=self.api.auth, headers=headers, data=body)
        return response

    def set_extent_owner(self, uuid: str) -> object:
        """
        Set the owner and group of the extent subtemplate. Owner=1 (geocat.ch admin) and group=1 (all).

        Args:
            uuid:
                string, required, the extent subtemplate uuid

        Returns:
            /{portal}/api/0.1/records/{metadataUuid}/ownership
        """
        headers = {"Content-Type": "application/json", "Accept": "application/json", "X-XSRF-TOKEN": self.api.token}

        parameters = {
            "groupIdentifier": 1,
            "userIdentifier": 1,
        }

        response = self.api.session.put(url=self.api.env + f"/geonetwork/srv/api/0.1/records/{uuid}/ownership",
                                        proxies=self.api.proxies, auth=self.api.auth, headers=headers,
                                        params=parameters)
        return response

    def update_single_subtemplate(self, uuid: str):
        """
        Update a single extent subtemplate. If the subtemplate doesn't exist, it is created.

        Args:
            uuid:
                string, required, the extent subtemplate uuid
        """

        # Get the feature in the geojson reference matching the given subtemplate uuid
        uuid_exist = False
        for feature in self.ref_geojson[0]["features"]:
            if feature["properties"][self.number] == int(uuid.split("-")[-1]):
                uuid_exist = True
                break

        if not uuid_exist:
            print("The given uuid doesn't match any feature in the geojon reference file !")
            sys.exit()

        headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.api.token}
        response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/registries/entries/{uuid}",
                                        proxies=self.api.proxies, auth=self.api.auth, headers=headers)

        # If subtemplate doesn't already exist, creates it
        if response.status_code == 404:
            response = self.create_extent(uuid=uuid)
            if response.status_code == 201:
                print(f"{uuid} : {okgreen('creation successful')}")
            else:
                print(f"{uuid} : {warningred('creation unsuccessful')}")
                sys.exit()
        else:
            print(f"{uuid} : {okgreen('already exists')}")

        # Update extent
        name = feature["properties"][self.name]
        gml = geojson_to_geocatgml(feature)
        response = self.update_extent(uuid=uuid, name=name, gml=gml)
        if process_ok(response=response):
            print(f"{uuid} : {okgreen('update successful')}")
        else:
            print(f"{uuid} : {warningred('update unsuccessful')}")

        # Validate extent
        response = self.validate_extent(uuid=uuid)
        if process_ok(response=response):
            print(f"{uuid} : {okgreen('validation successful')}")
        else:
            print(f"{uuid} : {warningred('validation unsuccessful')}")

        # Set permission, good response= 204, no message
        response = self.set_extent_permissions(uuid=uuid)
        if response.status_code == 204:
            print(f"{uuid} : {okgreen('set permission successful')}")
        else:
            print(f"{uuid} : {warningred('set permission unsuccessful')}")

        # Set ownership
        response = self.set_extent_owner(uuid=uuid)
        if process_ok(response=response):
            print(f"{uuid} : {okgreen('set ownership successful')}")
        else:
            print(f"{uuid} : {warningred('set ownership unsuccessful')}")

    def update_all_subtemplates(self, with_backup: bool = True):
        """
        Update all subtemplates that match a feature in the reference geojson.

        If the subtemplate doesn't exist, it is created. By default, the subtemplates that already exist in geocat
        are backed-up into a single geojson file before the update.

        The method write and save a log file in the output directory specified at the class level. It contains a line
        by step (creation, update, validation, permission setting, ownership setting) indicating if the process was
        successful or not.

        Args:
            with_backup: optional, default = True, if set to False no backup is done before the update
        """
        print(f"Update all subtemapltes - Number of subtemplates : {len(self.ref_geojson[0]['features'])}")

        if with_backup:
            self.backup_subtemplates()

        print("Update all subtemplates : ", end="\r")

        logfile = os.path.join(self.output_dir, f"UpdateAllSubtemplates_{datetime.now().strftime('%Y%m%d-%H%M%S')}.log")
        logger = setup_logger(f"UpdateAllSubtemplates_{datetime.now().strftime('%Y%m%d-%H%M%S')}", logfile)

        subtemplate_created = 0
        subtemplate_updated = 0
        subtemplate_creation_failed = 0
        subtemplate_update_failed = 0

        count = 0
        total = len(self.ref_geojson[0]["features"])
        for feature in self.ref_geojson[0]["features"]:

            new_subtemplate = False

            count += 1
            print(f"Update all subtemplates : {round((count / total) * 100, 1)}%", end="\r")

            uuid = f'geocatch-subtpl-extent-{self.type}-{feature["properties"][self.number]}'

            headers = {"accept": "application/xml", "Content-Type": "application/xml", "X-XSRF-TOKEN": self.api.token}
            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/0.1/registries/entries/{uuid}",
                                            proxies=self.api.proxies, auth=self.api.auth, headers=headers)

            # If subtemplate doesn't already exist, creates it
            if response.status_code == 404:
                logger.info(f"{count}/{total} - {uuid} - subtemplate does not already exist")
                response = self.create_extent(uuid=uuid)
                if response.status_code == 201:
                    logger.info(f"{count}/{total} - {uuid} - creation successful")
                    new_subtemplate = True
                else:
                    logger.error(f"{count}/{total} - {uuid} - creation unsuccessful")
                    subtemplate_creation_failed += 1
                    continue  # If creation failed, stop the process and pass to next subtemplate !
            else:
                logger.info(f"{count}/{total}- {uuid}- subtemplate already exists")

            # Update extent
            name = feature["properties"][self.name]
            gml = geojson_to_geocatgml(feature)
            response = self.update_extent(uuid=uuid, name=name, gml=gml)
            if process_ok(response=response):
                logger.info(f"{count}/{total} - {uuid} - update successful")
            else:
                logger.error(f"{count}/{total} - {uuid} - update unsuccessful")
                subtemplate_update_failed += 1  # If update failed, stop the process and pass to next subtemplate !
                continue

            # Validate extent
            response = self.validate_extent(uuid=uuid)
            if process_ok(response=response):
                logger.info(f"{count}/{total} - {uuid} - validation successful")
            else:
                logger.error(f"{count}/{total} - {uuid} - validation unsuccessful")
                subtemplate_update_failed += 1  # If validation failed, stop the process and pass to next subtemplate !
                continue

            # Set permission, good response= 204, no message
            response = self.set_extent_permissions(uuid=uuid)
            if response.status_code == 204:
                logger.info(f"{count}/{total} - {uuid} - set permission successful")
            else:
                logger.error(f"{count}/{total} - {uuid} - set permission unsuccessful")
                subtemplate_update_failed += 1  # If permission failed, stop the process and pass to next subtemplate !
                continue

            # Set ownership
            response = self.set_extent_owner(uuid=uuid)
            if process_ok(response=response):
                logger.info(f"{count}/{total} - {uuid} - set ownership successful")
                if new_subtemplate:
                    subtemplate_created += 1
                else:
                    subtemplate_updated += 1
            else:
                logger.error(f"{count}/{total} - {uuid} - set ownership unsuccessful")
                subtemplate_update_failed += 1  # If ownership failed, stop the process and pass to next subtemplate !
                continue

        print(f"Update all subtemplates : {okgreen('Done')}")
        print(f"Subtemplates successfully created : {okgreen(subtemplate_created)}")
        print(f"Subtemplates successfully updated : {okgreen(subtemplate_updated)}")
        print(f"Subtemplates unsuccessfully created : {warningred(subtemplate_creation_failed)}")
        print(f"Subtemplates unsuccessfully updated : {warningred(subtemplate_update_failed)}")

    def delete_subtemplates(self, uuids: list, with_backup: bool = True):
        """
        Delete a list of subtemplates. As an option, the subtemplates can be backed-up first.

        If the backup option is choosen, the subtemplates are saved in a single geojson file using the
        extent_to_geojson method.

        The method write and save a log file in the output directory specified at the class level. It contains a line
        by step (deletion) indicating if the process was successful or not.

        Args:
            with_backup: optional, default = True, if set to False no backup is done before the update
        """
        print(f"Delete subtemplates - Number of subtemplates : {len(uuids)}")

        # If backup is needed, creates a directory and save the subtemplates as a single geojson
        if with_backup:
            output_dir_backup = os.path.join(self.output_dir, "subtemplates_backup")

            if not os.path.exists(output_dir_backup):
                os.mkdir(output_dir_backup)

            geojson = self.extent_to_geojson(uuids)
            now = datetime.now().strftime("%Y%m%d%H%M%S")

            with open(os.path.join(output_dir_backup, f"BackupDeleted_{now}.json"), "w", encoding="utf-8") as f:
                json.dump(geojson, f, ensure_ascii=False)

        print("Delete subtemplates : ", end="\r")

        subtemplates_deleted = 0
        subtemplates_delete_failed = 0

        logfile = os.path.join(self.output_dir, f"DeleteSubtemplates_{datetime.now().strftime('%Y%m%d-%H%M%S')}.log")
        logger = setup_logger(f"DeleteSubtemplates_{datetime.now().strftime('%Y%m%d-%H%M%S')}", logfile)

        count = 0
        for uuid in uuids:
            count += 1

            headers = {"Content-Type": "application/json", "Accept": "application/json", "X-XSRF-TOKEN": self.api.token}

            response = self.api.session.delete(url=self.api.env + f"/geonetwork/srv/api/0.1/records/{uuid}",
                                            proxies=self.api.proxies, auth=self.api.auth, headers=headers)

            if response.status_code == 204:
                logger.info(f"{count}/{len(uuids)} - {uuid} - successfully deleted")
                subtemplates_deleted += 1
            else:
                logger.error(f"{count}/{len(uuids)} - {uuid} - unsuccessfully deleted")
                subtemplates_delete_failed += 1

            print(f"Delete subtemplates : {round((count / len(uuids)) * 100, 1)}%", end="\r")
        print(f"Delete subtemplates : {okgreen('Done')}")
        print(f"Subtemplates successfully deleted : {okgreen(subtemplates_deleted)}")
        print(f"Subtemplates unsuccessfully deleted : {warningred(subtemplates_delete_failed)}")