import io
import re
import requests
from datetime import datetime
import pandas as pd
import logging
import logging.config
import settings
import utils
from lxml import etree as ET
import geopycat

# Corresponds to the column name in the google doc
TechLayerNameInGDoc = "Layer/collection ID (technical layer name BGDI)"
GeocatIdInGDoc = "Geocat ID"

class BGDIMapping(geopycat.geocat):

    def __init__(self, bmd: str, **kwargs):

        super().__init__(**kwargs)

        self.bmd = bmd

        if not self.check_admin():
            print(geopycat.utils.warningred("You must be logged-in as Admin to use this tool !"))
            return

        self.bgdi_inventory = self.get_bgdi_inventory().reset_index()
        self.mapping = pd.DataFrame(columns=["Geocat UUID", "Layer ID", "Published",
                                            "Geocat Status", "Keyword", "Identifier",
                                            "WMS Link", "WMTS Link", "API3 Link", 
                                            "Map Preview Link", "ODS Permalink"])

        # initiate rows in mapping df
        for i, row in self.bgdi_inventory.iterrows():
            new_row = pd.DataFrame({"Geocat UUID": row[2], "Layer ID": row[1].strip()}, index=[0])
            self.mapping = pd.concat([new_row,self.mapping.loc[:]]).reset_index(drop=True)

        # get metadata index
        print("Get Metadata Index : ", end="\r")
        count = 1
        self.md_index = dict()
        for i, row in self.mapping.iterrows():
            self.md_index[row[0]] = self.get_metadata_index(uuid=row[0])
            print(f"Get Metadata Index : {round((count / len(self.mapping)) * 100, 1)}%", end="\r")
            count += 1
        print(f"Get Metadata Index : {geopycat.utils.okgreen('Done')}")

        self.wms = self.get_wms_layer()
        self.wmts = self.get_wmts_layer()
        self.ods_id_mapping = self.get_ods_permalink()

        self.check_publish_status()
        self.check_keyword()
        self.check_status()
        self.check_identifier()
        self.check_wms()
        self.check_wmts()
        self.check_api()
        self.check_mappreview()
        self.check_ods_permalink()

    def get_bgdi_inventory(self):
        """f
        Get BGDI inventory from google BMD.
        Improve the latter with geoadmin API3 and Google Drive Sheet

        Returns a pandas df filtered with existing geocat UUID
        """

        geocat_uuids = self.get_uuids()

        # Get the google sheet and clean it
        response = requests.get(url=settings.GD_SHEET, proxies=self.session.proxies)
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

        for i, row in df.iterrows():
            if not pd.isnull(row[TechLayerNameInGDoc]):
                df.at[i, TechLayerNameInGDoc] = \
                row[TechLayerNameInGDoc].strip()

        df=df.dropna(subset=[TechLayerNameInGDoc]).reset_index(drop=True)

        # Fix missing geocat UUID and missing records with the BMD
        bmd = pd.read_csv(self.bmd)

        for i, row in bmd.iterrows():
            if row["GEOCATUUID"] in geocat_uuids:
                indexes = df.index[df[TechLayerNameInGDoc] == row["TECHPUBLAYERNAME"]].tolist()
                if len(indexes) > 0:
                    if pd.isnull(df[GeocatIdInGDoc][indexes[0]]) and row["GEOCATUUID"] not in df[GeocatIdInGDoc].unique():
                        df.at[indexes[0], GeocatIdInGDoc] = row["GEOCATUUID"]
                        print(f"{row['TECHPUBLAYERNAME']} : Geocat UUID fixed by BMD")

                if row["TECHPUBLAYERNAME"] not in df[TechLayerNameInGDoc].unique() and \
                        row["GEOCATUUID"] not in df[GeocatIdInGDoc].unique():

                    new_row = {TechLayerNameInGDoc: row["TECHPUBLAYERNAME"], GeocatIdInGDoc: row["GEOCATUUID"]}

                    if row["INGESTSTATE"] == "Productive":
                        new_row["Layer on prod?"] = 1
                    elif row["INGESTSTATE"] == "NotProductive":
                        new_row["Layer on prod?"] = 0

                    new_row = pd.DataFrame(new_row, index=[0])
                    df = pd.concat([new_row,df.loc[:]]).reset_index(drop=True)
                    print(f"{row['TECHPUBLAYERNAME']} : record added by BMD")

        # Fix missing geocat UUID and missing records with the geoadmin API3
        # Create a dictionnary {layerid: geocat uuid} from geoadmin API3
        layerid_geocatuuid = dict()
        response = requests.get("https://api3.geo.admin.ch/rest/services/api/MapServer",
                                proxies=self.session.proxies)

        for i in response.json()["layers"]:
            layerid_geocatuuid[i["layerBodId"]] = i["idGeoCat"]

        # fix wrong geocat UUID with the API
        for i, row in df.iterrows():
            if row[TechLayerNameInGDoc] in layerid_geocatuuid:
                if layerid_geocatuuid[row[TechLayerNameInGDoc]] != row[GeocatIdInGDoc] \
                and layerid_geocatuuid[row[TechLayerNameInGDoc]] not in df[GeocatIdInGDoc].unique():
                    df.at[i, GeocatIdInGDoc] = layerid_geocatuuid[row[TechLayerNameInGDoc]]
                    print(f"{row[TechLayerNameInGDoc]} : geocat uuid fixed by API")

        # Fix missing record with the API
        for key, value in layerid_geocatuuid.items():
            if key not in df[TechLayerNameInGDoc].unique() and value not in df[GeocatIdInGDoc].unique():
                new_row = {TechLayerNameInGDoc: key, GeocatIdInGDoc: value, "INGESTSTATE": "Productive"}
                new_row = pd.DataFrame(new_row, index=[0])
                df = pd.concat([new_row,df.loc[:]]).reset_index(drop=True)
                print(f"{key} : record added by API")
        
        df=df.dropna(subset=[GeocatIdInGDoc]).reset_index(drop=True)
        df = df[df[GeocatIdInGDoc].isin(geocat_uuids)]

        return df

    def check_publish_status(self):
        """
        Fills the mapping data frame with publishing status
        """

        for i, row in self.bgdi_inventory.iterrows():

            index = self.mapping.index[self.mapping["Geocat UUID"] == row[2]].tolist()[0]

            if self.md_index[row[2]]["isPublishedToAll"] and row["Layer on prod?"] in [1, 0]:
                self.mapping.at[index, "Published"] = "Published"
            elif not self.md_index[row[2]]["isPublishedToAll"] and row["Layer on prod?"] != 1:
                self.mapping.at[index, "Published"] = "Unpublished"
            elif self.md_index[row[2]]["isPublishedToAll"] and row["Layer on prod?"] not in [1, 0]:
                self.mapping.at[index, "Published"] = "To unpublish"
            elif not self.md_index[row[2]]["isPublishedToAll"] and row["Layer on prod?"] == 1:
                self.mapping.at[index, "Published"] = "To publish"

    def check_keyword(self):
        """
        Fills the mapping data frame with BGDI Keyword status
        """

        keywords = ["BGDI Bundesgeodaten-Infrastruktur",
                        "IFDG l’Infrastructure Fédérale de données géographiques",
                        "FSDI Federal Spatial Data Infrastructure",
                        "IFDG Infrastruttura federale dei dati geografici"]

        uuids_keyword = self.get_uuids(keywords=keywords)

        for i, row in self.mapping.iterrows():
            if row[0] in uuids_keyword:
                self.mapping.at[i, "Keyword"] = "Ok"
            else:
                self.mapping.at[i, "Keyword"] = "Add BGDI"

        uuids = self.get_uuids(keywords=keywords, 
                                not_in_groups=settings.BGDI_GROUP_ID)
        for uuid in uuids:
            if uuid not in self.mapping["Geocat UUID"].unique():
                new_row = pd.DataFrame({"Geocat UUID": uuid, "Keyword": "Remove BGDI"}, index=[0])
                self.mapping = pd.concat([self.mapping, new_row]).reset_index(drop=True)
        
        cols = ["Geocat UUID", "Layer ID", "Published", "Geocat Status", "Keyword", "Identifier",
                "WMS Link", "WMTS Link", "API3 Link", "Map Preview Link", "ODS Permalink"]
        self.mapping = self.mapping[cols]

    def check_status(self):
        """
        Fills the mapping data frame with geocat status info
        """
        uuids_obsolete = self.get_uuids(q="+cl_status.key:obsolete")

        for i, row in self.mapping.iterrows():
            if row[0] in uuids_obsolete and row["Published"] in ["Unpublished", "To unpublish"]:
                self.mapping.at[i, "Geocat Status"] = "Ok"
            elif row[0] not in uuids_obsolete and row["Published"] in ["Published", "To publish"]:
                self.mapping.at[i, "Geocat Status"] = "Ok"
            elif row[0] in uuids_obsolete and row["Published"] in ["Published", "To publish"]:
                self.mapping.at[i, "Geocat Status"] = "Remove obsolete"
            elif row[0] not in uuids_obsolete and row["Published"] in ["Unpublished", "To unpublish"]:
                self.mapping.at[i, "Geocat Status"] = "Add obsolete"

    def check_identifier(self):
        """
        Fills the mapping data frame with geocat identifier info
        """
        for i, row in self.mapping.iterrows():
            if row["Keyword"] != "Remove BGDI":
                if "resourceIdentifier" in self.md_index[row[0]]["_source"]:
                    for j in self.md_index[row[0]]["_source"]["resourceIdentifier"]:
                        if j["code"] == row[1]:
                            self.mapping.at[i, "Identifier"] = "Ok"
                            break
                        else:
                            self.mapping.at[i, "Identifier"] = "Fix identifier"
                else:
                    self.mapping.at[i, "Identifier"] = "Add identifier"

    def check_wms(self):
        """
        Fills the mapping data frame with WMS Link info
        """

        for i, row in self.mapping.iterrows():

            if row["Keyword"] == "Remove BGDI":
                continue

            wms_ok = False
            wms_tofix = False

            if "link" in self.md_index[row[0]]["_source"]:
                for link in self.md_index[row[0]]["_source"]["link"]:
                    if "OGC:WMS" in link["protocol"] and re.search("^https:\/\/wms\.geo\.admin\.ch\/\?SERVICE=WMS&VERSION=1\.3\.0&REQUEST=GetCapabilities(&lang=(fr|de|it|en))?$", link["urlObject"]["default"]) and link["nameObject"]["default"] == row[1]:
                        wms_ok = True
                    elif "OGC:WMS" in link["protocol"] and "wms.geo.admin.ch" in link["urlObject"]["default"]:
                        wms_tofix = True

            if row[1] in self.wms:
                if wms_ok and not wms_tofix:
                    self.mapping.at[i, "WMS Link"] = "WMS"
                elif wms_ok and wms_tofix:
                    self.mapping.at[i, "WMS Link"] = "Fix WMS"
                elif not wms_ok and wms_tofix:
                    self.mapping.at[i, "WMS Link"] = "Fix WMS"
                else:
                    self.mapping.at[i, "WMS Link"] = "Add WMS"

            else:
                if wms_ok or wms_tofix:
                    self.mapping.at[i, "WMS Link"] = "Remove WMS"
                else:
                    self.mapping.at[i, "WMS Link"] = "No WMS"

    def check_wmts(self):
        """
        Fills the mapping data frame with WMTS Link info
        """

        for i, row in self.mapping.iterrows():

            if row["Keyword"] == "Remove BGDI":
                continue

            wmts_ok = False
            wmts_tofix = False

            if "link" in self.md_index[row[0]]["_source"]:
                for link in self.md_index[row[0]]["_source"]["link"]:
                    if "OGC:WMTS" in link["protocol"] and re.search("^https:\/\/wmts\.geo\.admin\.ch(\/EPSG\/(3857|21781|4326))?\/1\.0\.0\/WMTSCapabilities\.xml(\?lang=(de|fr|it|en))?$", link["urlObject"]["default"]) and link["nameObject"]["default"] == row[1]:
                        wmts_ok = True
                    elif "OGC:WMTS" in link["protocol"] and "wmts.geo.admin.ch" in link["urlObject"]["default"]:
                        wmts_tofix = True

            if row[1] in self.wmts:
                if wmts_ok and not wmts_tofix:
                    self.mapping.at[i, "WMTS Link"] = "WMTS"
                elif wmts_ok and wmts_tofix:
                    self.mapping.at[i, "WMTS Link"] = "Fix WMTS"
                elif not wmts_ok and wmts_tofix:
                    self.mapping.at[i, "WMTS Link"] = "Fix WMTS"
                else:
                    self.mapping.at[i, "WMTS Link"] = "Add WMTS"

            else:
                if wmts_ok or wmts_tofix:
                    self.mapping.at[i, "WMTS Link"] = "Remove WMTS"
                else:
                    self.mapping.at[i, "WMTS Link"] = "No WMTS"       

    def check_api(self):
        """
        Fills the mapping data frame with geoadmin API3 Link info
        """

        for i, row in self.mapping.iterrows():

            if row["Keyword"] == "Remove BGDI":
                continue

            api3_ok = False
            api3_tofix = False

            if "link" in self.md_index[row[0]]["_source"]:
                for link in self.md_index[row[0]]["_source"]["link"]:
                    if "ESRI:REST" in link["protocol"] and link["urlObject"]["default"] == f"{settings.API3_URL}/{row[1]}":
                        api3_ok = True
                    elif "ESRI:REST" in link["protocol"] and "api3.geo.admin.ch" in link["urlObject"]["default"]:
                        api3_tofix = True

            response = self.session.get(url=f"{settings.API3_URL}/{row[1]}")
            if response.status_code == 200:
                if api3_tofix:
                    self.mapping.at[i, "API3 Link"] = "Fix API3"
                    continue

                if api3_ok:
                    self.mapping.at[i, "API3 Link"] = "API3"
                else:
                    self.mapping.at[i, "API3 Link"] = "Add API3"
            else:
                if api3_ok or api3_tofix:
                    self.mapping.at[i, "API3 Link"] = "Remove API3"
                else:
                    self.mapping.at[i, "API3 Link"] = "No API3"

    def check_mappreview(self):
        """
        Fills the mapping data frame with map.geo.admin preview Link info
        """

        map_layer_ids = list()

        response = self.session.get("https://api3.geo.admin.ch/rest/services/api/MapServer", proxies=self.session.proxies, verify=False)

        if response.status_code == 200:
            for layer in response.json()["layers"]:
                map_layer_ids.append(layer["layerBodId"])
        else:
            print(f"Erreur lors de la récupération des layers: {response.status_code}")
            return

        for i, row in self.mapping.iterrows():

            if row["Keyword"] == "Remove BGDI":
                continue

            map_preview = False

            if "link" in self.md_index[row[0]]["_source"]:
                for link in self.md_index[row[0]]["_source"]["link"]:

                    # Check if metadata has link to map portal
                    if re.search(f"map\..*\.admin\.ch.*layers=.*{row[1]}($|[&,/])", link["urlObject"]["default"]):
                        map_preview = True

            if row[1] in map_layer_ids:
                if map_preview:
                    self.mapping.at[i, "Map Preview Link"] = "Map preview"
                else:
                    self.mapping.at[i, "Map Preview Link"] = "Add map preview"
            else:
                if map_preview:
                    # Do not remove preview since it can have other valid layers
                    self.mapping.at[i, "Map Preview Link"] = "No map preview"
                else:
                    self.mapping.at[i, "Map Preview Link"] = "No map preview"

    def check_ods_permalink(self):
        """
        Fills the mapping dataframe with ods permalink status. If the record is in ODS,
        it must have a correct ODS premalink.
        """

        # Check if record is in ODS
        for i, row in self.mapping.iterrows():

            if row["Keyword"] == "Remove BGDI":
                continue

            has_ods_permalink = False

            if "link" in self.md_index[row[0]]["_source"]:
                for link in self.md_index[row[0]]["_source"]["link"]:
                    if link["protocol"] == "OPENDATA:SWISS":
                        has_ods_permalink = True
                        break

            # Case where geocat record not in ODS
            if row[0] not in self.ods_id_mapping:
                
                # Not in ODS but ODS permalink
                if has_ods_permalink:
                    self.mapping.at[i, "ODS Permalink"] = "Remove ODS Permalink"
                
                # Not in ODS and no ODS permalink
                else:
                    self.mapping.at[i, "ODS Permalink"] = "No ODS Permalink"

            # Case where geocat record in ODS
            else:

                has_correct_ods_permalink = False

                if "link" in self.md_index[row[0]]["_source"]:
                    for link in self.md_index[row[0]]["_source"]["link"]:
                        if re.search(f"^https:\/\/opendata\.swiss\/.*\/perma\/{self.ods_id_mapping[row[0]]}$", link["urlObject"]["default"]):
                           has_correct_ods_permalink = True
                           break
                
                if has_correct_ods_permalink:
                    self.mapping.at[i, "ODS Permalink"] = "ODS Permalink"
                else:
                    if has_ods_permalink:
                        self.mapping.at[i, "ODS Permalink"] = "Fix ODS Permalink"
                    else:
                        self.mapping.at[i, "ODS Permalink"] = "Add ODS Permalink"

    def get_ods_permalink(self):
        """
        Get a mapping between geocat UUID and ODS permalink ID for every metadata in ODS
        """

        output = dict()

        start = 0

        while True:

            params = {
                "fq": "political_level:confederation",
                "rows": 1000,
                "start": start
            }

            response = self.session.get(
                "https://ckan.opendata.swiss/api/3/action/package_search",
                params=params,
                timeout=10
            ).json()

            if len(response["result"]["results"]) == 0:
                break

            else:
                for md in response["result"]["results"]:
                    if "relations" in md:
                        for relation in md["relations"]:
                            if relation["label"] == "geocat.ch permalink":
                                geocat_uuid = relation["url"].split("/")[-1]
                                ods_uuid = f"{geocat_uuid}@{md['organization']['name']}"
                                output[geocat_uuid] = ods_uuid
                                break

            start += 1000

        return output

    def get_wms_layer(self) -> dict:
        """
        Get layer id and title in 4 languages from swisstopo WMS
        """
        out = dict()

        # DE
        response = self.session.get(f"{settings.WMS_URL}&lang=de")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wms:Layer[1]//wms:Layer",
                                namespaces=settings.NS):

            out[i.find("wms:Name", namespaces=settings.NS).text] = {
                "de": f'WMS-BGDI Dienst, Layer "{i.find("wms:Title", namespaces=settings.NS).text}"'
                }

        # FR
        response = self.session.get(f"{settings.WMS_URL}&lang=fr")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wms:Layer[1]//wms:Layer",
                                namespaces=settings.NS):

            out[i.find("wms:Name", namespaces=settings.NS).text]["fr"] = \
                f'Service WMS-IFDG, couche "{i.find("wms:Title", namespaces=settings.NS).text}"'

        # IT
        response = self.session.get(f"{settings.WMS_URL}&lang=it")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wms:Layer[1]//wms:Layer",
                                namespaces=settings.NS):

            out[i.find("wms:Name", namespaces=settings.NS).text]["it"] = \
                f'Servizio WMS-IFDG, strato "{i.find("wms:Title", namespaces=settings.NS).text}"'

        # FR
        response = self.session.get(f"{settings.WMS_URL}&lang=en")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wms:Layer[1]//wms:Layer",
                                namespaces=settings.NS):

            out[i.find("wms:Name", namespaces=settings.NS).text]["en"] = \
                f'WMS-FSDI service, layer "{i.find("wms:Title", namespaces=settings.NS).text}"' 
    
        return out

    def get_wmts_layer(self) -> dict:
        """
        Get layer id and title in 4 languages from swisstopo WMTS
        """
        out = dict()

        response = self.session.get("https://wmts.geo.admin.ch/EPSG/2056/1.0.0/WMTSCapabilities.xml?lang=de")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text] = {
                "de": f'WMTS-BGDI Dienst, Layer "{i.find("ows:Title", namespaces=settings.NS).text}"'
                }

        response = self.session.get(f"{settings.WMTS_URL}?lang=fr")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text]["fr"] = \
                f'Service WMTS-IFDG, couche "{i.find("ows:Title", namespaces=settings.NS).text}"'

        response = self.session.get(f"{settings.WMTS_URL}?lang=it")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text]["it"] = \
                f'Servizio WMTS-IFDG, strato "{i.find("ows:Title", namespaces=settings.NS).text}"'

        response = self.session.get(f"{settings.WMTS_URL}?lang=en")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text]["en"] = \
                f'WMTS-FSDI service, layer "{i.find("ows:Title", namespaces=settings.NS).text}"'
    
        return out

    def repair_wmts(self, uuid: str):
        """
        Repair WMTS Link in the given metadata to match the BGDI
        """

        if uuid not in self.mapping["Geocat UUID"].unique():
            raise Exception("Metadata not in BGDI !")

        metadata = self.get_metadata_from_mef(uuid=uuid)
        if metadata is None:
            raise Exception("Metadata could not be fetch from geocat.ch !")

        body = list()
        row = self.mapping.loc[self.mapping['Geocat UUID']==uuid]

        if row["WMTS Link"].iloc[0] in ["Add WMTS", "Fix WMTS"] and row["Published"].iloc[0] not in ["Unpublished", "To unpublish"]:
            body += utils.add_wmts(metadata, row["Layer ID"].iloc[0], self.wmts[row["Layer ID"].iloc[0]])

        if row["WMTS Link"].iloc[0] == "Remove WMTS":
            body += utils.remove_wmts(metadata)

        if len(body) > 0:
            response = self.edit_metadata(uuid=uuid, body=body, updateDateStamp="false")

            return response

    def repair_api3(self, uuid: str):
        """
        Repair API3 Link in the given metadata to match the BGDI
        """

        if uuid not in self.mapping["Geocat UUID"].unique():
            raise Exception("Metadata not in BGDI !")

        metadata = self.get_metadata_from_mef(uuid=uuid)
        if metadata is None:
            raise Exception("Metadata could not be fetch from geocat.ch !")

        body = list()
        row = self.mapping.loc[self.mapping['Geocat UUID']==uuid]

        if row["API3 Link"].iloc[0] in ["Add API3", "Fix API3"] and row["Published"].iloc[0] not in ["Unpublished", "To unpublish"]:
            body += utils.add_api3(metadata, row["Layer ID"].iloc[0])

        if row["API3 Link"].iloc[0] == "Remove API3":
            body += utils.remove_api3(metadata)

        if len(body) > 0:
            response = self.edit_metadata(uuid=uuid, body=body, updateDateStamp="false")

            return response

    def repair_mappreview(self, uuid: str):
        """
        Repair Map preview Link in the given metadata to match the BGDI
        """

        if uuid not in self.mapping["Geocat UUID"].unique():
            raise Exception("Metadata not in BGDI !")

        metadata = self.get_metadata_from_mef(uuid=uuid)
        if metadata is None:
            raise Exception("Metadata could not be fetch from geocat.ch !")

        body = list()
        row = self.mapping.loc[self.mapping['Geocat UUID']==uuid]

        if row["Map Preview Link"].iloc[0] == "Add map preview" and row["Published"].iloc[0] not in ["Unpublished", "To unpublish"]:
            body += utils.add_mappreview(metadata, row["Layer ID"].iloc[0])

        if len(body) > 0:
            response = self.edit_metadata(uuid=uuid, body=body, updateDateStamp="false")

            return response

    def repair_ods_permalink(self, uuid: str):
        """
        Repair ODS permalink in the given metadata to match the BGDI
        """

        if uuid not in self.mapping["Geocat UUID"].unique():
            raise Exception("Metadata not in BGDI !")

        metadata = self.get_metadata_from_mef(uuid=uuid)
        if metadata is None:
            raise Exception("Metadata could not be fetch from geocat.ch !")

        body = list()
        row = self.mapping.loc[self.mapping['Geocat UUID']==uuid]

        if row["ODS Permalink"].iloc[0] in ["Add ODS Permalink", "Fix ODS Permalink"] and row["Published"].iloc[0] not in ["Unpublished", "To unpublish"]:
            body += utils.add_ods_permalink(metadata, self.ods_id_mapping[uuid])

        if row["ODS Permalink"].iloc[0] == "Remove ODS Permalink":
            body += utils.remove_ods_permalink(metadata)

        if len(body) > 0:
            response = self.edit_metadata(uuid=uuid, body=body, updateDateStamp="false")

            return response

    def repair_metadata(self, uuid: str):
        """
        Repair the given metadata to match the BGDI
        """

        if uuid not in self.mapping["Geocat UUID"].unique():
            raise Exception("Metadata not in BGDI !")

        metadata = self.get_metadata_from_mef(uuid=uuid)
        if metadata is None:
            raise Exception("Metadata could not be fetch from geocat.ch !")

        body = list()
        row = self.mapping.loc[self.mapping['Geocat UUID']==uuid]

        md_updated = False

        # Publish
        if row["Published"].iloc[0] == "To publish":

            response = self.session.put(f"{self.env}/geonetwork/srv/api/records/{uuid}/publish")

            md_updated = True

            if response.status_code != 204:
                raise Exception("Metadata could not be published !")

        elif row["Published"].iloc[0] == "To unpublish":
            response = self.session.put(f"{self.env}/geonetwork/srv/api/records/{uuid}/unpublish")

            md_updated = True

            if response.status_code != 204:
                raise Exception("Metadata could not be unpublished !")          

        # Status
        if row["Geocat Status"].iloc[0] == "Add obsolete":
            body += utils.add_status_obsolete(metadata)

        if row["Geocat Status"].iloc[0] == "Remove obsolete":
            body += utils.remove_status_obsolete(metadata)

        # Keyword
        if row["Keyword"].iloc[0] == "Add BGDI":
            body += utils.add_bgdi_keyword(metadata)

        if row["Keyword"].iloc[0] == "Remove BGDI":
            body += utils.remove_bgdi_keyword(metadata)

        # Identifier
        if row["Identifier"].iloc[0] == "Add identifier":
            body += utils.add_identifier(metadata, row["Layer ID"].iloc[0])

        # WMS
        if row["WMS Link"].iloc[0] in ["Add WMS", "Fix WMS"] and row["Published"].iloc[0] not in ["Unpublished", "To unpublish"]:
            body += utils.add_wms(metadata, row["Layer ID"].iloc[0], self.wms[row["Layer ID"].iloc[0]])

        if row["WMS Link"].iloc[0] == "Remove WMS":
            body += utils.remove_wms(metadata)

        if len(body) > 0:
            response = self.edit_metadata(uuid=uuid, body=body, updateDateStamp="false")

            if not geopycat.utils.process_ok(response):
                raise Exception("Keyword or Identifier or WMS could not be repaired")
            
            md_updated = True
        
        # WMTS
        if row["WMTS Link"].iloc[0] not in ["WMTS", "No WMTS"]:
            response = self.repair_wmts(uuid)
            if  response is not None:

                if not geopycat.utils.process_ok(response):
                    raise Exception("WMTS could not be repaired")
                
                md_updated = True

        # API3
        if row["API3 Link"].iloc[0] not in ["API3", "No API3"]:
            response = self.repair_api3(uuid)
            if  response is not None:

                if not geopycat.utils.process_ok(response):
                    raise Exception("API3 could not be repaired")
                
                md_updated = True

        # Map preview
        if row["Map Preview Link"].iloc[0] not in ["Map preview", "No map preview"]:
            response = self.repair_mappreview(uuid)
            if  response is not None:

                if not geopycat.utils.process_ok(response):
                    raise Exception("Map Preview could not be repaired")
                
                md_updated = True

        # ODS Permalink
        if row["ODS Permalink"].iloc[0] not in ["ODS Permalink", "No ODS Permalink"]:
            response = self.repair_ods_permalink(uuid)
            if  response is not None:

                if not geopycat.utils.process_ok(response):
                    raise Exception("ODS Permalink could not be repaired")
                
                md_updated = True

        # Logging
        if md_updated:
            print(geopycat.utils.okgreen(f"{uuid} - Metadata successfully repaired"))
        else:
            print(geopycat.utils.warningred(f"{uuid} - Metadata has nothing to repair"))

    def repair_all(self, tounpub: bool = False):
        """
        Repair all metadata to match the BGDI
        """

        logfile = f"BGDI-Mapping_{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

        log_config = geopycat.utils.get_log_config(logfile, log2stdout = False)
        logging.config.dictConfig(log_config)
        
        logger = logging.getLogger(__name__)

        print("Repair all : ", end="\r")
        count = 0

        for i, row in self.mapping.iterrows():

            count += 1

            if row["Published"] != "To unpublish" or tounpub:

                try:
                    self.repair_metadata(row["Geocat UUID"])
                except Exception as e:
                    logger.error(f"{row['Geocat UUID']} - {e}")
                else:
                    logger.info(f"{row['Geocat UUID']} - successfully repaired")
            
            print(f"Repair all : {round((count / len(self.mapping.index)) * 100, 1)}%", end="\r")
        print(f"Repair all : {geopycat.utils.okgreen('Done')}")