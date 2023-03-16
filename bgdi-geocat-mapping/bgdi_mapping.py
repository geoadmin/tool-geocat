import io
import re
import requests
from datetime import datetime
import pandas as pd
import settings
import utils
from lxml import etree as ET
import geopycat


class BGDIMapping(geopycat.geocat):

    def __init__(self, bmd: str, **kwargs):

        super().__init__(**kwargs)

        self.bmd = bmd

        if not self.check_admin():
            print(geopycat.utils.warningred("You must be logged-in as Admin to generate a backup !"))
            return

        self.bgdi_inventory = self.get_bgdi_inventory().reset_index()
        self.mapping = pd.DataFrame(columns=["Geocat UUID", "Layer ID", "Published",
                                            "Geocat Status", "Keyword", "Identifier",
                                            "WMS Link", "WMTS Link", "API3 Link", 
                                            "Map Preview Link"])

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

        self.check_publish_status()
        self.check_keyword()
        self.check_status()
        self.check_identifier()
        self.check_wms()
        self.check_wmts()
        self.check_api()
        self.check_mappreview()

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
            if not pd.isnull(row["Layername (according to naming convention FSDI)"]):
                df.at[i, "Layername (according to naming convention FSDI)"] = \
                row["Layername (according to naming convention FSDI)"].strip()

        df=df.dropna(subset=['Layername (according to naming convention FSDI)']).reset_index(drop=True)

        # Fix missing geocat UUID and missing records with the BMD
        bmd = pd.read_csv(self.bmd)

        for i, row in bmd.iterrows():
            if row["GEOCATUUID"] in geocat_uuids:
                indexes = df.index[df['Layername (according to naming convention FSDI)'] == row["TECHPUBLAYERNAME"]].tolist()
                if len(indexes) > 0:
                    if pd.isnull(df["Geocat ID"][indexes[0]]) and row["GEOCATUUID"] not in df['Geocat ID'].unique():
                        df.at[indexes[0], "Geocat ID"] = row["GEOCATUUID"]
                        print(f"{row['TECHPUBLAYERNAME']} : Geocat UUID fixed by BMD")

                if row["TECHPUBLAYERNAME"] not in df['Layername (according to naming convention FSDI)'].unique() and \
                        row["GEOCATUUID"] not in df['Geocat ID'].unique():

                    new_row = {'Layername (according to naming convention FSDI)': row["TECHPUBLAYERNAME"], "Geocat ID": row["GEOCATUUID"]}

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
            if row["Layername (according to naming convention FSDI)"] in layerid_geocatuuid:
                if layerid_geocatuuid[row["Layername (according to naming convention FSDI)"]] != row["Geocat ID"] \
                and layerid_geocatuuid[row["Layername (according to naming convention FSDI)"]] not in df['Geocat ID'].unique():
                    df.at[i, "Geocat ID"] = layerid_geocatuuid[row["Layername (according to naming convention FSDI)"]]
                    print(f"{row['Layername (according to naming convention FSDI)']} : geocat uuid fixed by API")

        # Fix missing record with the API
        for key, value in layerid_geocatuuid.items():
            if key not in df["Layername (according to naming convention FSDI)"].unique() and value not in df['Geocat ID'].unique():
                new_row = {'Layername (according to naming convention FSDI)': key, 'Geocat ID': value, "INGESTSTATE": "Productive"}
                new_row = pd.DataFrame(new_row, index=[0])
                df = pd.concat([new_row,df.loc[:]]).reset_index(drop=True)
                print(f"{key} : record added by API")
        
        df=df.dropna(subset=['Geocat ID']).reset_index(drop=True)
        df = df[df["Geocat ID"].isin(geocat_uuids)]

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
                "WMS Link", "WMTS Link", "API3 Link", "Map Preview Link"]
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
            elif row[0] not in uuids_obsolete and row["Published"] == "Unpublished":
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

            if row["Published"] in ["Published", "To publish"]:

                wms_ok = False
                wms_tofix = False

                if "link" in self.md_index[row[0]]["_source"]:
                    for link in self.md_index[row[0]]["_source"]["link"]:
                        if link["protocol"] == "OGC:WMS" and re.search("^https:\/\/wms\.geo\.admin\.ch\/\?SERVICE=WMS&VERSION=1\.3\.0&REQUEST=GetCapabilities(&lang=(fr|de|it|en))?$", link["url"]) and link["name"] == row[1]:
                            wms_ok = True
                        elif link["protocol"] == "OGC:WMS" and "wms.geo.admin.ch" in link["url"]:
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
            if row["Published"] in ["Published", "To publish"]:

                wmts_ok = False
                wmts_tofix = False

                if "link" in self.md_index[row[0]]["_source"]:
                    for link in self.md_index[row[0]]["_source"]["link"]:
                        if link["protocol"] == "OGC:WMTS" and re.search("^https:\/\/wmts\.geo\.admin\.ch(\/EPSG\/(3857|21781|4326))?\/1\.0\.0\/WMTSCapabilities\.xml(\?lang=(de|fr|it|en))?$", link["url"]) and link["name"] == row[1]:
                            wmts_ok = True
                        elif link["protocol"] == "OGC:WMTS" and "wmts.geo.admin.ch" in link["url"]:
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
            if row["Published"] in ["Published", "To publish"]:

                api3_ok = False
                api3_tofix = False

                if "link" in self.md_index[row[0]]["_source"]:
                    for link in self.md_index[row[0]]["_source"]["link"]:
                        if link["protocol"] == "ESRI:REST" and link["url"] == f"{settings.API3_URL}/{row[1]}":
                            api3_ok = True
                        elif link["protocol"] == "ESRI:REST" and "api3.geo.admin.ch" in link["url"]:
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
        response = self.session.get("https://map.geo.admin.ch/configs/en/layersConfig.json")
        for layer in response.json():
            if "parentLayerId" not in response.json()[layer]:
                map_layer_ids.append(layer)

        for i, row in self.mapping.iterrows():
            if row["Published"] in ["Published", "To publish"]:

                map_preview = False

                if "link" in self.md_index[row[0]]["_source"]:
                    for link in self.md_index[row[0]]["_source"]["link"]:

                        # Check if metadata has link to map portal
                        if re.search(f"map\..*\.admin\.ch.*layers=.*{row[1]}($|[&,/])", link["url"]):
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

    def get_wms_layer(self) -> dict:
        """
        Get layer id and title in 4 languages from swisstopo WMS
        """
        out = dict()

        response = self.session.get(f"{settings.WMS_URL}&lang=de")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wms:Layer[1]//wms:Layer",
                                namespaces=settings.NS):

            out[i.find("wms:Name", namespaces=settings.NS).text] = {
                "de": i.find("wms:Title", namespaces=settings.NS).text
                }

        response = self.session.get(f"{settings.WMS_URL}&lang=fr")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wms:Layer[1]//wms:Layer",
                                namespaces=settings.NS):

            out[i.find("wms:Name", namespaces=settings.NS).text]["fr"] = \
                i.find("wms:Title", namespaces=settings.NS).text

        response = self.session.get(f"{settings.WMS_URL}&lang=it")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wms:Layer[1]//wms:Layer",
                                namespaces=settings.NS):

            out[i.find("wms:Name", namespaces=settings.NS).text]["it"] = \
                i.find("wms:Title", namespaces=settings.NS).text 

        response = self.session.get(f"{settings.WMS_URL}&lang=en")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wms:Layer[1]//wms:Layer",
                                namespaces=settings.NS):

            out[i.find("wms:Name", namespaces=settings.NS).text]["en"] = \
                i.find("wms:Title", namespaces=settings.NS).text  
    
        return out

    def get_wmts_layer(self) -> dict:
        """
        Get layer id and title in 4 languages from swisstopo WMTS
        """
        out = dict()

        response = self.session.get(f"{settings.WMTS_URL}?lang=de")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text] = {
                "de": i.find("ows:Title", namespaces=settings.NS).text
                }

        response = self.session.get(f"{settings.WMTS_URL}?lang=fr")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text]["fr"] = \
                i.find("ows:Title", namespaces=settings.NS).text

        response = self.session.get(f"{settings.WMTS_URL}?lang=it")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text]["it"] = \
                i.find("ows:Title", namespaces=settings.NS).text

        response = self.session.get(f"{settings.WMTS_URL}?lang=en")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text]["en"] = \
                i.find("ows:Title", namespaces=settings.NS).text 
    
        return out

    def repair_metadata(self, uuid: str):
        """
        Repair the given metadata to match the BGDI
        """

        if uuid not in self.mapping["Geocat UUID"].unique():
            raise Exception(f"{uuid} not in BGDI !")

        metadata = self.get_metadata_from_mef(uuid=uuid)
        if metadata is None:
            raise Exception(f"{uuid} could not be fetch from geocat.ch !")

        body = list()
        row = self.mapping.loc[self.mapping['Geocat UUID']==uuid]

        # # Publish
        # if row["Published"].iloc[0] == "To publish":

        #     response = self.session.put(f"{self.env}/geonetwork/srv/api/records/{uuid}/publish")

        #     if response.status_code != 204:
        #         raise Exception(f"{uuid} could not be published !")

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
        if row["Identifier"].iloc[0] in ["Add identifier", "Fix identifier"]:
            body += utils.add_identifier(metadata, row["Layer ID"].iloc[0])

        # WMS
        if row["WMS Link"].iloc[0] in ["Add WMS", "Fix WMS"]:
            body += utils.add_wms(metadata, row["Layer ID"].iloc[0], self.wms[row["Layer ID"].iloc[0]])

        if row["WMS Link"].iloc[0] == "Remove WMS":
            body += utils.remove_wms(metadata)

        # WMTS
        if row["WMTS Link"].iloc[0] in ["Add WMTS", "Fix WMTS"]:
            body += utils.add_wmts(metadata, row["Layer ID"].iloc[0], self.wmts[row["Layer ID"].iloc[0]])

        if row["WMTS Link"].iloc[0] == "Remove WMTS":
            body += utils.remove_wmts(metadata)

        # API3
        if row["API3 Link"].iloc[0] in ["Add API3", "Fix API3"]:
            body += utils.add_api3(metadata, row["Layer ID"].iloc[0])

        if row["API3 Link"].iloc[0] == "Remove API3":
            body += utils.remove_api3(metadata)

        # Map preview
        if row["Map Preview Link"].iloc[0] == "Add map preview":
            body += utils.add_mappreview(metadata, row["Layer ID"].iloc[0])

        # Editing
        if len(body) > 0:
            response = self.edit_metadata(uuid=uuid, body=body, updateDateStamp="false")

            if geopycat.utils.process_ok(response):
                print(geopycat.utils.okgreen(f"{uuid} successfully repaired"))
            else:
                raise Exception(f"{uuid} could not be repaired")

        else:
            print(geopycat.utils.warningred(f"{uuid} nothing to repair"))

    def repair_all(self):
        """
        Repair all metadata to match the BGDI
        """

        logger = geopycat.utils.setup_logger(f"BGDI-Mapping_{datetime.now().strftime('%Y%m%d-%H%M%S')}")

        print("Repair all : ", end="\r")
        count = 0

        for i, row in self.mapping.iterrows():

            count += 1

            try:
                self.repair_metadata(row["Geocat UUID"])
            except Exception as e:
                logger.error(f"{row['Geocat UUID']} - {e}")
            else:
                logger.info(f"{row['Geocat UUID']} - successfully repaired")
            
            print(f"Repair all : {round((count / len(self.mapping.index)) * 100, 1)}%", end="\r")
        print(f"Repair all : {geopycat.utils.okgreen('Done')}")
