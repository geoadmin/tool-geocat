import io
import re
import requests
import pandas as pd
import settings
from lxml import etree as ET
import geopycat


class BGDIMapping(geopycat.geocat):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

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

        # TODO - ONLY FOR TESTING
        # with open('md_index.json') as input:
        #     self.md_index = json.load(input)

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
        bmd = pd.read_csv("report.csv")

        for i, row in bmd.iterrows():
            if row["GEOCATUUID"] in geocat_uuids:
                indexes = df.index[df['Layername (according to naming convention FSDI)'] == row["TECHPUBLAYERNAME"]].tolist()
                if len(indexes) > 0:
                    if pd.isnull(df["Geocat ID"][indexes[0]]):
                        df.at[indexes[0], "Geocat ID"] = row["GEOCATUUID"]
                        print(f"{row['TECHPUBLAYERNAME']} : Geocat UUID fixed by BMD")

                else:
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
                if layerid_geocatuuid[row["Layername (according to naming convention FSDI)"]] != row["Geocat ID"]:
                    df.at[i, "Geocat ID"] = layerid_geocatuuid[row["Layername (according to naming convention FSDI)"]]
                    print(f"{row['Layername (according to naming convention FSDI)']} : geocat uuid fixed by API")

        # Fix missing record with the API
        for key, value in layerid_geocatuuid.items():
            if key not in df["Layername (according to naming convention FSDI)"].unique():
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
            if self.md_index[row[2]]["isPublishedToAll"] and row["Layer on prod?"] in [1, 0]:
                self.mapping.at[i, "Published"] = "Published"
            elif not self.md_index[row[2]]["isPublishedToAll"] and row["Layer on prod?"] != 1:
                self.mapping.at[i, "Published"] = "Unpublished"
            elif self.md_index[row[2]]["isPublishedToAll"] and row["Layer on prod?"] not in [1, 0]:
                self.mapping.at[i, "Published"] = "To unpublish"
            elif not self.md_index[row[2]]["isPublishedToAll"] and row["Layer on prod?"] == 1:
                self.mapping.at[i, "Published"] = "To publish"

    def check_keyword(self):
        """
        Fills the mapping data frame with BGDI Keyword status
        """
        uuids_keyword = self.get_uuids(keywords=["BGDI Bundesgeodaten-Infrastruktur"])

        for i, row in self.mapping.iterrows():
            if row[0] in uuids_keyword:
                self.mapping.at[i, "Keyword"] = "Ok"
            else:
                self.mapping.at[i, "Keyword"] = "Add BGDI"

        uuids = self.get_uuids(keywords=["BGDI Bundesgeodaten-Infrastruktur"], 
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

        response = self.session.get(settings.WMS_URL)
        root = ET.fromstring(response.content)

        wms_layer_ids = root.xpath(".//wms:Layer[1]//wms:Layer/wms:Name/text()", 
                                    namespaces=settings.NS)

        for i, row in self.mapping.iterrows():

            if row["Published"] in ["Published", "To publish"]:

                wms_ok = False
                wms_tofix = False

                if "link" in self.md_index[row[0]]["_source"]:
                    for link in self.md_index[row[0]]["_source"]["link"]:
                        if link["protocol"] == "OGC:WMS" and link["url"] == settings.WMS_URL and link["name"] == row[1]:
                            wms_ok = True
                        elif link["protocol"] == "OGC:WMS" and "wms.geo.admin.ch" in link["url"]:
                            wms_tofix = True

                if row[1] in wms_layer_ids:
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

        response = self.session.get(settings.WMTS_URL[0])
        root = ET.fromstring(response.content)

        wmts_layer_ids = root.xpath(".//wmts:Contents//wmts:Layer/ows:Identifier/text()", 
                                    namespaces=settings.NS)

        for i, row in self.mapping.iterrows():
            if row["Published"] in ["Published", "To publish"]:

                wmts_ok = False
                wmts_tofix = False

                if "link" in self.md_index[row[0]]["_source"]:
                    for link in self.md_index[row[0]]["_source"]["link"]:
                        if link["protocol"] == "OGC:WMTS" and link["url"] in settings.WMTS_URL and link["name"] == row[1]:
                            wmts_ok = True
                        elif link["protocol"] == "OGC:WMTS" and "wmts.geo.admin.ch" in link["url"]:
                            wmts_tofix = True

                if row[1] in wmts_layer_ids:
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

        api3_layer_ids = list()
        response = self.session.get(url=settings.API3_URL)
        for layer in response.json()["layers"]:
            if "layerBodId" in layer:
                api3_layer_ids.append(layer["layerBodId"])


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
                if row[1] in api3_layer_ids and response.status_code == 200:
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

        response = self.session.get(f"{settings.WMTS_URL[0]}?lang=de")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text] = {
                "de": i.find("ows:Title", namespaces=settings.NS).text
                }

        response = self.session.get(f"{settings.WMTS_URL[0]}?lang=fr")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text]["fr"] = \
                i.find("ows:Title", namespaces=settings.NS).text

        response = self.session.get(f"{settings.WMTS_URL[0]}?lang=it")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text]["it"] = \
                i.find("ows:Title", namespaces=settings.NS).text

        response = self.session.get(f"{settings.WMTS_URL[0]}?lang=en")
        root = ET.fromstring(response.content)

        for i in root.xpath(".//wmts:Contents//wmts:Layer",
                                namespaces=settings.NS):

            out[i.find("ows:Identifier", namespaces=settings.NS).text]["en"] = \
                i.find("ows:Title", namespaces=settings.NS).text 
    
        return out


# t = BGDIMapping(env="prod")
# t.mapping