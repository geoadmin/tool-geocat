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

import geopycat
import logging
import os
import colorama
import pandas as pd
import xml.etree.ElementTree as ET
import json
import sys
from datetime import datetime
from string import ascii_uppercase

colorama.init()

CANTON_NAMES = {
    "ZH": {"DE": "Kanton Zürich (ZH)", "FR": "Canton de Zurich (ZH)", "IT": "Cantone di Zurigo (ZH)", 
           "EN": "Canton of Zurich (ZH)", "RM": "Chantun Turitg (ZH)"},
    "BE": {"DE": "Kanton Bern (BE)", "FR": "Canton de Berne (BE)", "IT": "Cantone di Berna (BE)", 
           "EN": "Canton of Bern (BE)", "RM": "Chantun Berna (BE)"},
    "LU": {"DE": "Kanton Luzern (LU)", "FR": "Canton de Lucerne (LU)", "IT": "Cantone di Lucerna (LU)", 
           "EN": "Canton of Lucerne (LU)", "RM": "Chantun Lucerna (LU)"},
    "UR": {"DE": "Kanton Uri (UR)", "FR": "Canton d'Uri (UR)", "IT": "Cantone di Uri (UR)", 
           "EN": "Canton of Uri (UR)", "RM": "Chantun Uri (UR)"},
    "SZ": {"DE": "Kanton Schwyz (SZ)", "FR": "Canton de Schwytz (SZ)", "IT": "Cantone di Svitto (SZ)", 
           "EN": "Canton of Schwyz (SZ)", "RM": "Chantun Sviz (SZ)"},
    "OW": {"DE": "Kanton Obwalden (OW)", "FR": "Canton d'Obwald (OW)", "IT": "Cantone di Obvaldo (OW)", 
           "EN": "Canton of Obwalden (OW)", "RM": "Chantun Sursilvania (OW)"},
    "NW": {"DE": "Kanton Nidwalden (NW)", "FR": "Canton de Nidwald (NW)", "IT": "Cantone di Nidvaldo (NW)", 
           "EN": "Canton of Nidwalden (NW)", "RM": "Chantun Sutsilvania (NW)"},
    "GL": {"DE": "Kanton Glarus (GL)", "FR": "Canton de Glaris (GL)", "IT": "Cantone di Glarona (GL)", 
           "EN": "Canton of Glarus (GL)", "RM": "Chantun Glaruna (GL)"},
    "ZG": {"DE": "Kanton Zug (ZG)", "FR": "Canton de Zoug (ZG)", "IT": "Cantone di Zugo (ZG)", 
           "EN": "Canton of Zug (ZG)", "RM": "Chantun Zug (ZG)"},
    "FR": {"DE": "Kanton Freiburg (FR)", "FR": "Canton de Fribourg (FR)", "IT": "Cantone di Friborgo (FR)", 
           "EN": "Canton of Fribourg (FR)", "RM": "Chantun Friburg (FR)"},
    "SO": {"DE": "Kanton Solothurn (SO)", "FR": "Canton de Soleure (SO)", "IT": "Cantone di Soletta (SO)", 
           "EN": "Canton of Solothurn (SO)", "RM": "Chantun Soloturn (SO)"},
    "BS": {"DE": "Kanton Basel-Stadt (BS)", "FR": "Canton de Bâle-Ville (BS)", "IT": "Cantone di Basilea Città (BS)", 
           "EN": "Canton of Basel-Stadt (BS)", "RM": "Chantun Basilea-Citad (BS)"},
    "BL": {"DE": "Kanton Basel-Landschaft (BL)", "FR": "Canton de Bâle-Campagne (BL)", "IT": "Cantone di Basilea Campagna (BL)", 
           "EN": "Canton of Basel-Landschaft (BL)", "RM": "Chantun Basilea-Champagna (BL)"},
    "SH": {"DE": "Kanton Schaffhausen (SH)", "FR": "Canton de Schaffhouse (SH)", "IT": "Cantone di Sciaffusa (SH)", 
           "EN": "Canton of Schaffhausen (SH)", "RM": "Chantun Schaffusa (SH)"},
    "AR": {"DE": "Kanton Appenzell Ausserrhoden (AR)", "FR": "Canton d'Appenzell Rhodes-Extérieures (AR)", "IT": "Cantone di Appenzello Esterno (AR)", 
           "EN": "Canton of Appenzell Ausserrhoden (AR)", "RM": "Chantun Appenzell dadora Rodens (AR)"},
    "AI": {"DE": "Kanton Appenzell Innerrhoden (AI)", "FR": "Canton d'Appenzell Rhodes-Intérieures (AI)", "IT": "Cantone di Appenzello Interno (AI)", 
           "EN": "Canton of Appenzell Innerrhoden (AI)", "RM": "Chantun Appenzell davent Rodens (AI)"},
    "SG": {"DE": "Kanton St. Gallen (SG)", "FR": "Canton de Saint-Gall (SG)", "IT": "Cantone di San Gallo (SG)", 
           "EN": "Canton of St. Gallen (SG)", "RM": "Chantun Son Gagl (SG)"},
    "GR": {"DE": "Kanton Graubünden (GR)", "FR": "Canton des Grisons (GR)", "IT": "Cantone dei Grigioni (GR)", 
           "EN": "Canton of Grisons (GR)", "RM": "Chantun Grischun (GR)"},
    "AG": {"DE": "Kanton Aargau (AG)", "FR": "Canton d'Argovie (AG)", "IT": "Cantone di Argovia (AG)", 
           "EN": "Canton of Aargau (AG)", "RM": "Chantun Argovia (AG)"},
    "TG": {"DE": "Kanton Thurgau (TG)", "FR": "Canton de Thurgovie (TG)", "IT": "Cantone di Turgovia (TG)", 
           "EN": "Canton of Thurgau (TG)", "RM": "Chantun Turgovia (TG)"},
    "TI": {"DE": "Kanton Tessin (TI)", "FR": "Canton du Tessin (TI)", "IT": "Cantone Ticino (TI)", 
           "EN": "Canton of Ticino (TI)", "RM": "Chantun Tessin (TI)"},
    "VD": {"DE": "Kanton Waadt (VD)", "FR": "Canton de Vaud (VD)", "IT": "Cantone di Vaud (VD)", 
           "EN": "Canton of Vaud (VD)", "RM": "Chantun Vad (VD)"},
    "VS": {"DE": "Kanton Wallis (VS)", "FR": "Canton du Valais (VS)", "IT": "Cantone Vallese (VS)", 
           "EN": "Canton of Valais (VS)", "RM": "Chantun Vallais (VS)"},
    "NE": {"DE": "Kanton Neuenburg (NE)", "FR": "Canton de Neuchâtel (NE)", "IT": "Cantone di Neuchâtel (NE)", 
           "EN": "Canton of Neuchâtel (NE)", "RM": "Chantun Neuchâtel (NE)"},
    "GE": {"DE": "Kanton Genf (GE)", "FR": "Canton de Genève (GE)", "IT": "Cantone di Ginevra (GE)", 
           "EN": "Canton of Geneva (GE)", "RM": "Chantun Genevra (GE)"},
    "JU": {"DE": "Kanton Jura (JU)", "FR": "Canton du Jura (JU)", "IT": "Cantone del Giura (JU)", 
           "EN": "Canton of Jura (JU)", "RM": "Chantun Giura (JU)"},
}

def geojson_to_geocatgml(geojson_feature: dict):
    """
    Transform a single geojson feature (type=Feature) into a GML ready for extent subtemplate of geocat (ISO 19115-3).

    The geojson feature must be in WGS84. Coordinates of exterior polygons must be in the clock-wise order.
    Coordinates of interior polygons must be in the counter-clock-wise order.
    The returned GML starts at the tag <gex:polygon>.

    Args:
        geojson_feature:
            dict, required, geojson feature

    Returns:
        GML snippet at the tag level <gex:polygon> ready for extent subtemplate in geocat (ISO 19115-3).
    """
    import uuid as uuid_module
    
    # Generate unique IDs for GML elements
    multisurface_id = f"ms-{uuid_module.uuid4().hex[:8]}"
    
    gml_start = f"<gex:polygon xmlns:gex='http://standards.iso.org/iso/19115/-3/gex/1.0'>" \
                f"<gml:MultiSurface xmlns:gml='http://www.opengis.net/gml/3.2' gml:id='{multisurface_id}' srsDimension='2'>"

    gml_end = "</gml:MultiSurface></gex:polygon>"

    gml_core = ""

    # Exterior polygons
    if "coordinates" in geojson_feature["geometry"]:
        exteriors = geojson_feature["geometry"]["coordinates"]
    else:
        exteriors = geojson_feature["geometry"]["geometries"][0]["coordinates"]

    for exterior in exteriors:
        polygon_id = f"poly-{uuid_module.uuid4().hex[:8]}"
        
        gml_core += "<gml:surfaceMember>" \
                    f"<gml:Polygon gml:id='{polygon_id}'>" \
                    "<gml:exterior>" \
                    "<gml:LinearRing>" \
                    "<gml:posList>"

        for coordinates in exterior[0]:
            gml_core += f"{coordinates[0]} {coordinates[1]} "
        gml_core = gml_core[:-1]

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
                gml_core = gml_core[:-1]

                gml_core += "</gml:posList>" \
                            "</gml:LinearRing>" \
                            "</gml:interior>"

        gml_core += "</gml:Polygon>" \
                    "</gml:surfaceMember>"

    return gml_start + gml_core + gml_end


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

        self.api = geopycat.geocat(env)
        self.output_dir = output_dir
        self.ref_geojson = ref_geojson
        self.gmdnr = gmdnr
        self.gmdname = gmdname

        self.export_municipalities()
        self.check_gmd()

    def export_municipalities(self):
        """
        Export all municipalities from geocat. I.e. subtemplates with UUID matching
        'geocatch-subtpl-extent-hoheitsgebiet-[1:10000].

        It saves a csv list named 'geocat_municipalities.csv' with the attributes GMDNR and GMDNAME at the root of
        the folder given at the class level.
        """
        print("Exporting all municipalities from geocat : ", end="\r")
        headers = {"accept": "application/xml", "Content-Type": "application/xml"}
        df = pd.DataFrame(columns=["GMDNR", "GMDNAME"])

        # Namespaces ISO 19115-3
        ns = {
            'gex': 'http://standards.iso.org/iso/19115/-3/gex/1.0',
            'gco': 'http://standards.iso.org/iso/19115/-3/gco/1.0'
        }

        count = 0
        for i in range(1, 10000):

            uuid = f"geocatch-subtpl-extent-hoheitsgebiet-{i}"
            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/registries/entries/{uuid}",
                                            headers=headers)

            if response.status_code == 200:
                xmlroot = ET.fromstring(response.content)
                
                # Nouveau chemin ISO 19115-3
                gmd_name_elem = xmlroot.find('.//gex:description/gco:CharacterString', ns)
                if gmd_name_elem is not None:
                    gmd_name = gmd_name_elem.text

                    row = pd.Series({"GMDNR": i, "GMDNAME": gmd_name})
                    df = pd.concat([df, row.to_frame().T], ignore_index=True)

            count += 1
            print(f"Exporting all municipalities from geocat : {round((count / 10000) * 100, 1)}%", end="\r")

        df.to_csv(os.path.join(self.output_dir, "geocat_municipalities.csv"), index=False)
        print(f"Exporting all municipalities from geocat : {geopycat.utils.okgreen('Done')}")

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
        for feature in geojson_ref_file["features"]:
            gmdnr = feature["properties"][self.gmdnr]
            gmdname = feature["properties"][self.gmdname]

            # Case where id exists but name is different
            if gmdnr in df_geocat.values:
                if gmdname != df_geocat.loc[df_geocat["GMDNR"] == gmdnr].iloc[0]["GMDNAME"]:
                    
                    new_row = pd.Series({
                        "GMDNR": gmdnr,
                        "GMDNAME_new": gmdname,
                        "GMDNAME_old": df_geocat.loc[df_geocat["GMDNR"] == gmdnr].iloc[0]["GMDNAME"],
                    })

                    df_name_change = pd.concat([df_name_change, new_row.to_frame().T], ignore_index=True)

                else:

                    new_row = pd.Series({
                        "GMDNR": gmdnr,
                        "GMDNAME": gmdname,
                    })

                    df_correct = pd.concat([df_correct, new_row.to_frame().T], ignore_index=True)

            # Case where id is different for a given name
            else:
                if gmdname in df_geocat.values:

                    new_row = pd.Series({
                        "GMDNAME": gmdname,
                        "GMDNR_new": gmdnr,
                        "GMDNR_old": df_geocat.loc[df_geocat["GMDNAME"] == gmdname].iloc[0]["GMDNR"],
                    })

                    df_id_change = pd.concat([df_id_change, new_row.to_frame().T], ignore_index=True)

                # Case where id and name doesn't exist. New municipality to add to geocat.
                else:

                    new_row = pd.Series({
                        "GMDNAME": gmdname,
                        "GMDNR": gmdnr,
                    })

                    df_new = pd.concat([df_new, new_row.to_frame().T], ignore_index=True)

        # 2 - Testing geocat against new municipalities
        # 2 - Testing geocat against new municipalities
        ref_gmdnrs = [feature["properties"][self.gmdnr] for feature in geojson_ref_file["features"]]  # ← CORRIGÉ
        ref_gmdnames = [feature["properties"][self.gmdname] for feature in geojson_ref_file["features"]]  # ← CORRIGÉ

        for _, row in df_geocat.iterrows():

            # Case where municipalities in geocat doesn't exist at all (no id, no name) in the new ones
            if (row["GMDNR"] not in ref_gmdnrs) and (row["GMDNAME"] not in ref_gmdnames):

                new_row = pd.Series({
                    "GMDNAME": row["GMDNAME"],
                    "GMDNR": row["GMDNR"],
                })

                df_old = pd.concat([df_old, new_row.to_frame().T], ignore_index=True)

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

        print(f"Checking municipalities...{geopycat.utils.okgreen('Done')}")


class CheckDistrictBoundaries:
    """
    Check the districts admin boundaries from geocat by comparing them to a reference geojson file.
    The geojson file must be encoded in utf-8 to support special characters (accents).

    Args:
        ref_geojson:
            str, required ! The path to the reference geojson file.
        bznr:
            str, required ! The attribute name in the reference file corresponding to the municipalities BFS number
        bzname:
            str, required ! The attribute name in the reference file corresponding to the municipalities name
        env:
            str, indicating the geocat's environment to work with, 'int' or 'prod', default = 'int'.
        output_dir:
            str, the directory path where to save the results, default = current directory.

    It saves 5 csv lists (if not empty):
            correct_districts.csv : ID and Name correct in geocat and reference
            name_incorrect_districts.csv : ID is found but Name is different in geocat
            id_incorrect_districts.csv : Name is found but ID is different in geocat
            new_districts.csv : ID and Name not found in geocat
            old_districts.csv : ID and Name not found in reference
    """

    def __init__(self, ref_geojson, bznr, bzname, env: str = 'int', output_dir: str = os.path.dirname(__file__)):

        self.api = geopycat.geocat(env)
        self.output_dir = output_dir
        self.ref_geojson = ref_geojson
        self.bznr = bznr
        self.bzname = bzname

        self.export_districts()
        self.check_bz()

    def export_districts(self):
        """
        Export all districts from geocat. I.e. subtemplates with UUID matching
        'geocatch-subtpl-extent-bezirk-[1:3000].

        It saves a csv list named 'geocat_districts.csv' with the attributes BZNR and BZNAME at the root of
        the folder given at the class level.
        """
        print("Exporting all districts from geocat : ", end="\r")
        headers = {"accept": "application/xml", "Content-Type": "application/xml"}
        df = pd.DataFrame(columns=["BZNR", "BZNAME"])

        ns = {
            'gex': 'http://standards.iso.org/iso/19115/-3/gex/1.0',
            'gco': 'http://standards.iso.org/iso/19115/-3/gco/1.0'
        }

        count = 0
        for i in range(1, 3000):

            uuid = f"geocatch-subtpl-extent-bezirk-{i}"
            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/registries/entries/{uuid}",
                                            headers=headers)

            if response.status_code == 200:
                xmlroot = ET.fromstring(response.content)
                
                # Nouveau chemin ISO 19115-3
                bz_name_elem = xmlroot.find('.//gex:description/gco:CharacterString', ns)
                if bz_name_elem is not None:
                    bz_name = bz_name_elem.text

                    row = pd.Series({"BZNR": i, "BZNAME": bz_name})
                    df = pd.concat([df, row.to_frame().T], ignore_index=True)

            count += 1
            print(f"Exporting all districts from geocat : {round((count / 3000) * 100, 1)}%", end="\r")

        df.to_csv(os.path.join(self.output_dir, "geocat_districts.csv"), index=False)
        print(f"Exporting all districts from geocat : {geopycat.utils.okgreen('Done')}")

    def check_bz(self):
        """
        Compare the districcts (names and id) from geocat (i.e. from the csv list created by the
        export_districts function) with the districts from the reference geojson file.

        It saves 5 csv lists at the root of the folder given at the class level :
                correct_districts.csv : ID and Name correct in geocat and reference
                name_incorrect_districts.csv : ID is found but Name is different in geocat
                id_incorrect_districts.csv : Name is found but ID is different in geocat
                new_districts.csv : ID and Name not found in geocat
                old_districts.csv : ID and Name not found in reference
        """
        print("Checking districts...", end="\r")

        with open(self.ref_geojson, "rb") as file:
            geojson_ref_file = json.load(file)

        df_geocat = pd.read_csv(os.path.join(self.output_dir, "geocat_districts.csv"))

        df_name_change = pd.DataFrame(columns=["BZNR", "BZNAME_new", "BZNAME_old"])
        df_id_change = pd.DataFrame(columns=["BZNAME", "BZNR_new", "BZNR_old"])
        df_new = pd.DataFrame(columns=["BZNR", "BZNAME"])
        df_old = pd.DataFrame(columns=["BZNR", "BZNAME"])
        df_correct = pd.DataFrame(columns=["BZNR", "BZNAME"])

        # 1 - Testing new districts against geocat
        for feature in geojson_ref_file["features"]:
            bznr = feature["properties"][self.bznr]
            bzname = feature["properties"][self.bzname]

            # Case where id exists but name is different
            if bznr in df_geocat.values:
                if bzname != df_geocat.loc[df_geocat["BZNR"] == bznr].iloc[0]["BZNAME"]:

                    new_row = pd.Series({
                        "BZNR": bznr,
                        "BZNAME_new": bzname,
                        "BZNAME_old": df_geocat.loc[df_geocat["BZNR"] == bznr].iloc[0]["BZNAME"],
                    })

                    df_name_change = pd.concat([df_name_change, new_row.to_frame().T], ignore_index=True)

                else:

                    new_row = pd.Series({
                        "BZNR": bznr,
                        "BZNAME": bzname,
                    })

                    df_correct = pd.concat([df_correct, new_row.to_frame().T], ignore_index=True)

            # Case where id is different for a given name
            else:
                if bzname in df_geocat.values:

                    new_row = pd.Series({
                        "BZNAME": bzname,
                        "BZNR_new": bznr,
                        "BZNR_old": df_geocat.loc[df_geocat["BZNAME"] == bzname].iloc[0]["BZNR"],
                    })

                    df_id_change = pd.concat([df_id_change, new_row.to_frame().T], ignore_index=True)

                # Case where id and name doesn't exist. New district to add to geocat.
                else:

                    new_row = pd.Series({
                        "BZNAME": bzname,
                        "BZNR": bznr,
                    })

                    df_new = pd.concat([df_new, new_row.to_frame().T], ignore_index=True)


        # 2 - Testing geocat against new districts
        ref_bznrs = [feature["properties"][self.bznr] for feature in geojson_ref_file["features"]]  # ← CORRIGÉ
        ref_bznames = [feature["properties"][self.bzname] for feature in geojson_ref_file["features"]]  # ← CORRIGÉ

        for _, row in df_geocat.iterrows():

            # Case where districts in geocat doesn't exist at all (no id, no name) in the new ones
            if (row["BZNR"] not in ref_bznrs) and (row["BZNAME"] not in ref_bznames):

                new_row = pd.Series({
                    "BZNAME": row["BZNAME"],
                    "BZNR": row["BZNR"],
                })

                df_old = pd.concat([df_old, new_row.to_frame().T], ignore_index=True)

        if len(df_name_change) > 0:
            df_name_change.to_csv(os.path.join(self.output_dir, "name_incorrect_districts.csv"), index=False)
        if len(df_id_change) > 0:
            df_id_change.to_csv(os.path.join(self.output_dir, "id_incorrect_districts.csv"), index=False)
        if len(df_new) > 0:
            df_new.to_csv(os.path.join(self.output_dir, "new_districts.csv"), index=False)
        if len(df_old) > 0:
            df_old.to_csv(os.path.join(self.output_dir, "old_districts.csv"), index=False)
        if len(df_correct) > 0:
            df_correct.to_csv(os.path.join(self.output_dir, "correct_districts.csv"), index=False)

        print(f"Checking districts...{geopycat.utils.okgreen('Done')}")


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

        self.api = geopycat.geocat(env)
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
        headers = {"accept": "application/xml", "Content-Type": "application/xml"}
        df = pd.DataFrame(columns=["KTNR", "KTNAME"])

        # Namespaces ISO 19115-3
        ns = {
            'gex': 'http://standards.iso.org/iso/19115/-3/gex/1.0',
            'gco': 'http://standards.iso.org/iso/19115/-3/gco/1.0'
        }

        count = 0
        for i in range(1, 100):

            uuid = f"geocatch-subtpl-extent-kantonsgebiet-{i}"
            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/registries/entries/{uuid}",
                                            headers=headers)

            if response.status_code == 200:
                xmlroot = ET.fromstring(response.content)
                
                kt_name_elem = xmlroot.find('.//gex:description/gco:CharacterString', ns)
                if kt_name_elem is not None:
                    kt_name_full = kt_name_elem.text
                    
                    import re
                    match = re.search(r'\(([A-Z]{2})\)', kt_name_full)
                    if match:
                        kt_code = match.group(1)
                        
                        new_row = pd.Series({"KTNR": i, "KTNAME": kt_code})
                        df = pd.concat([df, new_row.to_frame().T], ignore_index=True)

            count += 1
            print(f"Exporting all cantons from geocat : {round((count / 100) * 100, 1)}%", end="\r")

        df.to_csv(os.path.join(self.output_dir, "geocat_cantons.csv"), index=False)
        print(f"Exporting all cantons from geocat : {geopycat.utils.okgreen('Done')}")

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
        for feature in geojson_ref_file["features"]:
            ktnr = feature["properties"][self.ktnr]
            ktname = feature["properties"][self.ktname]

            # Case where id exists but name is different
            if ktnr in df_geocat.values:
                if ktname != df_geocat.loc[df_geocat["KTNR"] == ktnr].iloc[0]["KTNAME"]:

                    new_row = pd.Series({
                        "KTNR": ktnr,
                        "KTNAME_new": ktname,
                        "KTNAME_old": df_geocat.loc[df_geocat["KTNR"] == ktnr].iloc[0]["KTNAME"],
                    })

                    df_name_change = pd.concat([df_name_change, new_row.to_frame().T], ignore_index=True)

                else:

                    new_row = pd.Series({
                        "KTNR": ktnr,
                        "KTNAME": ktname,
                    })

                    df_correct = pd.concat([df_correct, new_row.to_frame().T], ignore_index=True)

            # Case where id is different for a given name
            else:
                if ktname in df_geocat.values:

                    new_row = pd.Series({
                        "KTNAME": ktname,
                        "KTNR_new": ktnr,
                        "KTNR_old": df_geocat.loc[df_geocat["KTNAME"] == ktname].iloc[0]["KTNR"],
                    })

                    df_id_change = pd.concat([df_id_change, new_row.to_frame().T], ignore_index=True)

                # Case where id and name doesn't exist. New canton to add to geocat.
                else:

                    new_row = pd.Series({
                        "KTNAME": ktname,
                        "KTNR": ktnr,
                    })

                    df_new = pd.concat([df_new, new_row.to_frame().T], ignore_index=True)

        # 2 - Testing geocat against new cantons
        ref_ktnrs = [feature["properties"][self.ktnr] for feature in geojson_ref_file["features"]]  # ← CORRIGÉ
        ref_ktnames = [feature["properties"][self.ktname] for feature in geojson_ref_file["features"]]  # ← CORRIGÉ

        for _, row in df_geocat.iterrows():

            # Case where cantons in geocat doesn't exist at all (no id, no name) in the new ones
            if (row["KTNR"] not in ref_ktnrs) and (row["KTNAME"] not in ref_ktnames):

                new_row = pd.Series({
                    "KTNAME": row["KTNAME"],
                    "KTNR": row["KTNR"],
                })

                df_old = pd.concat([df_old, new_row.to_frame().T], ignore_index=True)

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

        print(f"Checking cantons...{geopycat.utils.okgreen('Done')}")


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

        self.api = geopycat.geocat(env)
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
        headers = {"accept": "application/xml", "Content-Type": "application/xml"}
        df = pd.DataFrame(columns=["LANDNR", "LANDNAME"])

        # Namespaces ISO 19115-3
        ns = {
            'gex': 'http://standards.iso.org/iso/19115/-3/gex/1.0',
            'gco': 'http://standards.iso.org/iso/19115/-3/gco/1.0'
        }

        count = 0
        for first in ascii_uppercase:
            for second in ascii_uppercase:
                uuid = f"geocatch-subtpl-extent-landesgebiet-{first}{second}"

                response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/registries/entries/{uuid}",
                                                headers=headers)

                if response.status_code == 200:
                    xmlroot = ET.fromstring(response.content)
                    
                    # Nouveau chemin ISO 19115-3
                    land_name_elem = xmlroot.find('.//gex:description/gco:CharacterString', ns)
                    if land_name_elem is not None:
                        land_name = land_name_elem.text

                        new_row = pd.Series({"LANDNR": first + second, "LANDNAME": land_name})
                        df = pd.concat([df, new_row.to_frame().T], ignore_index=True)

                count += 1
                print(f"Exporting all countries from geocat : {round((count / (26*26)) * 100, 1)}%", end="\r")

        df.to_csv(os.path.join(self.output_dir, "geocat_countries.csv"), index=False)
        print(f"Exporting all countries from geocat : {geopycat.utils.okgreen('Done')}")

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
        for feature in geojson_ref_file["features"]:
            landnr = feature["properties"][self.landnr]
            landname = feature["properties"][self.landname]

            # Case where id exists but name is different
            if landnr in df_geocat.values:
                if landname != df_geocat.loc[df_geocat["LANDNR"] == landnr].iloc[0]["LANDNAME"]:

                    new_row = pd.Series({
                        "LANDNR": landnr,
                        "LANDNAME_new": landname,
                        "LANDNAME_old": df_geocat.loc[df_geocat["LANDNR"] == landnr].iloc[0]["LANDNAME"],
                    })

                    df_name_change = pd.concat([df_name_change, new_row.to_frame().T], ignore_index=True)

                else:

                    new_row = pd.Series({
                        "LANDNR": landnr,
                        "LANDNAME": landname,
                    })

                    df_correct = pd.concat([df_correct, new_row.to_frame().T], ignore_index=True)

            # Case where id is different for a given name
            else:
                if landname in df_geocat.values:

                    new_row = pd.Series({
                        "LANDNAME": landname,
                        "LANDNR_new": landnr,
                        "LANDNR_old": df_geocat.loc[df_geocat["LANDNAME"] == landname].iloc[0]["LANDNR"],
                    })

                    df_id_change = pd.concat([df_id_change, new_row.to_frame().T], ignore_index=True)

                # Case where id and name doesn't exist. New country to add to geocat.
                else:

                    new_row = pd.Series({
                        "LANDNAME": landname,
                        "LANDNR": landnr,
                    })

                    df_new = pd.concat([df_new, new_row.to_frame().T], ignore_index=True)

        # 2 - Testing geocat against new countries
        ref_landnrs = [feature["properties"][self.landnr] for feature in geojson_ref_file["features"]]  # ← CORRIGÉ
        ref_landnames = [feature["properties"][self.landname] for feature in geojson_ref_file["features"]]  # ← CORRIGÉ

        for _, row in df_geocat.iterrows():

            # Case where countries in geocat doesn't exist at all (no id, no name) in the new ones
            if (row["LANDNR"] not in ref_landnrs) and (row["LANDNAME"] not in ref_landnames):

                new_row = pd.Series({
                    "LANDNAME": row["LANDNAME"],
                    "LANDNR": row["LANDNR"],
                })

                df_old = pd.concat([df_old, new_row.to_frame().T], ignore_index=True)

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

        print(f"Checking countries...{geopycat.utils.okgreen('Done')}")


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
            str, required ! "g" for municipalities, "b" for district, "k" for cantons, "l" for country
        env:
            str, indicating the geocat's environment to work with, 'int' or 'prod', default = 'int'.
        output_dir:
            str, the directory path where to save the backups and logfile, default = current directory.
    """

    def __init__(self, ref_geojson, number, name, type, update_name: bool = True, env: str = 'int',
                 output_dir: str = os.path.dirname(__file__)):

        self.api = geopycat.geocat(env)

        with open(ref_geojson, "rb") as file:
            self.ref_geojson = json.load(file)

        self.number = number
        self.name = name
        self.output_dir = output_dir
        self.update_name = update_name

        if type == "g":
            self.type = "hoheitsgebiet"
        elif type == "b":
            self.type = "bezirk"
        elif type == "k":
            self.type = "kantonsgebiet"
        elif type == "l":
            self.type = "landesgebiet"

        if not update_name:
            print(f"{geopycat.utils.warningred('The update_name option is set to False ! Creation of new extent not possible !')}")

        if not geopycat.geocat.check_admin(self.api):
            print(f"{geopycat.utils.warningred('You must be admin to run this tool !')}")
            sys.exit()

    def extent_to_geojson(self, uuids: list) -> list:
        """
        Convert geocat extent subtemplates (ISO 19115-3) into geojson.
        """
        print("Convert extent subtemplates to geojson : ", end="\r")

        now = datetime.now().strftime("%Y%m%d%H%M%S")
        geojson = [{"type": "FeatureCollection", "name": f"GeocatExtent_{now}", "features": []}]

        headers = {"accept": "application/xml", "Content-Type": "application/xml"}

        # Namespaces ISO 19115-3
        ns = {
            'gex': 'http://standards.iso.org/iso/19115/-3/gex/1.0',
            'gml': 'http://www.opengis.net/gml/3.2',
            'lan': 'http://standards.iso.org/iso/19115/-3/lan/1.0',
            'gco': 'http://standards.iso.org/iso/19115/-3/gco/1.0'
        }

        count = 0
        for uuid in uuids:
            response = self.api.session.get(
                url=self.api.env + f"/geonetwork/srv/api/registries/entries/{uuid}?lang=fre,ger,ita,eng,roh",
                headers=headers)

            if response.status_code == 200:
                geojson[0]["features"].append({"type": "Feature",
                                               "geometry": {"type": "MultiPolygon", "coordinates": []},
                                               "properties": {}})

                xmlroot = ET.fromstring(response.content)

                # Extract names (ISO 19115-3 paths)
                name = xmlroot.find('.//gex:description/gco:CharacterString', ns).text
                name_de = xmlroot.find('.//lan:LocalisedCharacterString[@locale="#DE"]', ns).text
                name_fr = xmlroot.find('.//lan:LocalisedCharacterString[@locale="#FR"]', ns).text
                name_it = xmlroot.find('.//lan:LocalisedCharacterString[@locale="#IT"]', ns).text
                name_en = xmlroot.find('.//lan:LocalisedCharacterString[@locale="#EN"]', ns).text
                name_rm = xmlroot.find('.//lan:LocalisedCharacterString[@locale="#RM"]', ns).text

                geojson[0]["features"][-1]["properties"][self.name] = name
                geojson[0]["features"][-1]["properties"][f"{self.name}_DE"] = name_de
                geojson[0]["features"][-1]["properties"][f"{self.name}_FR"] = name_fr
                geojson[0]["features"][-1]["properties"][f"{self.name}_IT"] = name_it
                geojson[0]["features"][-1]["properties"][f"{self.name}_EN"] = name_en
                geojson[0]["features"][-1]["properties"][f"{self.name}_RM"] = name_rm

                # Extract number
                if self.type == "landesgebiet":
                    geojson[0]["features"][-1]["properties"][self.number] = uuid.split('-')[-1]
                else:
                    geojson[0]["features"][-1]["properties"][self.number] = int(uuid.split('-')[-1])

                # Extract geometry
                for exterior in xmlroot.findall(".//gml:surfaceMember", ns):
                    geojson[0]["features"][-1]["geometry"]["coordinates"].append([[]])

                    exterior_poly = exterior.find(".//gml:exterior//gml:posList", ns)
                    coordinates = exterior_poly.text.split(" ")

                    # Coordinates order (lon-lat)
                    for i in range(0, len(coordinates), 2):
                        geojson[0]["features"][-1]["geometry"]["coordinates"][-1][-1].append(
                            [float(coordinates[i]), float(coordinates[i + 1])])

                    # Interior polygons
                    for interior in exterior.findall(".//gml:interior", ns):
                        geojson[0]["features"][-1]["geometry"]["coordinates"][-1].append([])
                        interior_poly = interior.find(".//gml:posList", ns)
                        coordinates = interior_poly.text.split(" ")

                        for i in range(0, len(coordinates), 2):
                            geojson[0]["features"][-1]["geometry"]["coordinates"][-1][-1].append(
                                [float(coordinates[i]), float(coordinates[i + 1])])

            count += 1
            print(f"Convert extent subtemplates to geojson : {round((count / len(uuids)) * 100, 1)}%", end="\r")
        
        print(f"Convert extent subtemplates to geojson : {geopycat.utils.okgreen('Done')}")
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
        for feature in self.ref_geojson["features"]:
            uuid = f"geocatch-subtpl-extent-{self.type}-{feature['properties'][self.number]}"
            uuids.append(uuid)

        geojson = self.extent_to_geojson(uuids)
        now = datetime.now().strftime("%Y%m%d%H%M%S")

        with open(os.path.join(output_dir_backup, f"Backup_{now}.json"), "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False)

        print(f"Backup subtemplates...{geopycat.utils.okgreen('Done')}")

    def create_extent(self, uuid: str) -> object:
        """
        Create a new extent subtemplate with the given uuid by uploading a complete XML template.

        Args:
            uuid:
                string, required, uuid for the subtemplate to be created.

        Returns:
            response of the PUT records API request (or dummy 404 if update_name=False).
        """

        if self.update_name:
            # Load the reference XML template
            template_path = os.path.join(os.path.dirname(__file__), "templates", "reference.xml")
            
            if not os.path.exists(template_path):
                print(f"❌ Template file not found: {template_path}")
                class ErrorResponse:
                    def __init__(self):
                        self.status_code = 500
                        self.text = f"Template file not found: {template_path}"
                return ErrorResponse()
            
            # Read the template
            with open(template_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Parse and modify the UUID
            root = ET.fromstring(xml_content)
            root.set('uuid', uuid)
            
            # Convert back to string
            xml_with_uuid = ET.tostring(root, encoding='unicode')
            
            # Upload with the new UUID
            headers = {
                "Content-Type": "application/xml",
                "Accept": "application/json"
            }
            
            params = {
                "metadataType": "SUB_TEMPLATE",
                "uuidProcessing": "OVERWRITE",  # Force l'UUID du XML
                "transformWith": "_none_",
                "group": "6"
            }
            
            response = self.api.session.put(
                url=self.api.env + "/geonetwork/srv/api/records",
                headers=headers,
                params=params,
                data=xml_with_uuid.encode('utf-8')
            )
            
            if response.status_code == 201:
                print(f"✅ Subtemplate created with UUID {uuid}")
            else:
                print(f"❌ Failed to create subtemplate: {response.status_code}")
                if hasattr(response, 'text'):
                    print(f"Error details: {response.text[:500]}")
            
            return response

        else:
            # Create a dummy class to return an object with the variable "status_code" = 404
            class Response:
                def __init__(self):
                    self.status_code = 404

            response = Response()
            return response  

    def update_extent(self, uuid: str, name: str, gml: str) -> object:
        """
        Update the name and geometry of the given extent subtemplate (ISO 19115-3).
        
        For cantons, if 'name' is a 2-letter code (e.g., "VD") and exists in CANTON_NAMES,
        the full multilingual names will be used automatically.

        Args:
            uuid: string, required, the extent subtemplate uuid
            name: string, required, the new name (for cantons: 2-letter code like "VD")
            gml: string, required, the new geometry (GML with gex: namespace)

        Returns:
            response of the PUT records API request.
        """
        
        # Load the reference XML template
        template_path = os.path.join(os.path.dirname(__file__), "templates", "reference.xml")
        
        if not os.path.exists(template_path):
            print(f"❌ Template file not found: {template_path}")
            class ErrorResponse:
                def __init__(self):
                    self.status_code = 500
                    self.text = f"Template file not found: {template_path}"
            return ErrorResponse()
        
        # Read and parse the template
        with open(template_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Namespaces
        namespaces = {
            'gex': 'http://standards.iso.org/iso/19115/-3/gex/1.0',
            'gml': 'http://www.opengis.net/gml/3.2',
            'lan': 'http://standards.iso.org/iso/19115/-3/lan/1.0',
            'gco': 'http://standards.iso.org/iso/19115/-3/gco/1.0',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        # Register namespaces to preserve prefixes
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)
        
        root = ET.fromstring(xml_content)
        
        # 1. Update UUID
        root.set('uuid', uuid)
        
        # 2. Update name (if requested)
        if self.update_name:
            # Check if this is a canton (2-letter code in CANTON_NAMES)
            is_canton = (len(name) == 2 and name.upper() in CANTON_NAMES)
            
            if is_canton:
                # Use multilingual canton names
                canton_names = CANTON_NAMES[name.upper()]
                
                # Update CharacterString (German by default)
                char_string = root.find('.//gco:CharacterString', namespaces)
                if char_string is not None:
                    char_string.text = canton_names["DE"]
                
                # Update LocalisedCharacterString for each language
                for locale_elem in root.findall('.//lan:LocalisedCharacterString', namespaces):
                    locale = locale_elem.get('locale')
                    if locale == "#DE":
                        locale_elem.text = canton_names["DE"]
                    elif locale == "#FR":
                        locale_elem.text = canton_names["FR"]
                    elif locale == "#IT":
                        locale_elem.text = canton_names["IT"]
                    elif locale == "#EN":
                        locale_elem.text = canton_names["EN"]
                    elif locale == "#RM":
                        locale_elem.text = canton_names["RM"]
            else:
                # Use single name for municipalities, districts, countries
                # Update CharacterString
                char_string = root.find('.//gco:CharacterString', namespaces)
                if char_string is not None:
                    char_string.text = name
                
                # Update all LocalisedCharacterString
                for locale_elem in root.findall('.//lan:LocalisedCharacterString', namespaces):
                    locale_elem.text = name
        
        # 3. Update geometry - parse the GML string and replace the polygon element
        # Remove the old polygon
        old_polygon = root.find('.//gex:polygon', namespaces)
        if old_polygon is not None:
            parent = root.find('.//gex:EX_BoundingPolygon', namespaces)
            parent.remove(old_polygon)
            
            # Parse the new GML and add it
            gml_element = ET.fromstring(gml)
            parent.append(gml_element)
        
        # 4. Calculate and update bounding box from the geometry
        bbox = self._calculate_bbox_from_gml(gml, namespaces)
        
        west = root.find('.//gex:westBoundLongitude/gco:Decimal', namespaces)
        if west is not None:
            west.text = f"{bbox['west']:.6f}"
        
        east = root.find('.//gex:eastBoundLongitude/gco:Decimal', namespaces)
        if east is not None:
            east.text = f"{bbox['east']:.6f}"
        
        south = root.find('.//gex:southBoundLatitude/gco:Decimal', namespaces)
        if south is not None:
            south.text = f"{bbox['south']:.6f}"
        
        north = root.find('.//gex:northBoundLatitude/gco:Decimal', namespaces)
        if north is not None:
            north.text = f"{bbox['north']:.6f}"
        
        # Convert back to string with XML declaration
        xml_updated = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_updated += ET.tostring(root, encoding='unicode')
        
        # Upload the updated XML
        headers = {
            "Content-Type": "application/xml",
            "Accept": "application/json"
        }
        
        params = {
            "metadataType": "SUB_TEMPLATE",
            "uuidProcessing": "OVERWRITE",
            "transformWith": "_none_"
        }
        
        response = self.api.session.put(
            url=self.api.env + "/geonetwork/srv/api/records",
            headers=headers,
            params=params,
            data=xml_updated.encode('utf-8')
        )
        
        return response
    
    def _calculate_bbox_from_gml(self, gml: str, namespaces: dict) -> dict:
        """
        Calculate bounding box from GML polygon.
        
        Args:
            gml: GML string
            namespaces: dict of namespaces
            
        Returns:
            dict with west, east, south, north
        """
        gml_element = ET.fromstring(gml)
        
        # Extract all coordinates from posList
        all_coords = []
        for poslist in gml_element.findall('.//gml:posList', namespaces):
            coords = poslist.text.strip().split()
            # Convert to pairs of floats (lon, lat)
            for i in range(0, len(coords), 2):
                all_coords.append((float(coords[i]), float(coords[i+1])))
        
        # Calculate bbox
        lons = [coord[0] for coord in all_coords]
        lats = [coord[1] for coord in all_coords]
        
        return {
            "west": min(lons),
            "east": max(lons),
            "south": min(lats),
            "north": max(lats)
        }

    def validate_extent(self, uuid: str) -> object:
        """
        Validate the extent subtemplate.

        Args:
            uuid:
                string, required, the extent subtemplate uuid

        Returns:
            response of the validate API request.
        """
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        parameters = {
            "uuids": [uuid],
        }

        response = self.api.session.put(url=self.api.env + "/geonetwork/srv/api/records/validate",
                                        headers=headers, params=parameters)
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
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        body = {
            "clear": True,
            "privileges": [
                {
                    "group": 6,
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

        response = self.api.session.put(url=self.api.env + f"/geonetwork/srv/api/records/{uuid}/sharing",
                                        headers=headers, data=body)
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
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        parameters = {
            "groupIdentifier": 6,
            "userIdentifier": 1,
        }

        response = self.api.session.put(url=self.api.env + f"/geonetwork/srv/api/records/{uuid}/ownership",
                                        headers=headers, params=parameters)
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
        for feature in self.ref_geojson["features"]:
            if feature["properties"][self.number] == int(uuid.split("-")[-1]):
                uuid_exist = True
                break

        if not uuid_exist:
            print("The given uuid doesn't match any feature in the geojon reference file !")
            sys.exit()

        headers = {"accept": "application/xml", "Content-Type": "application/xml"}
        response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/registries/entries/{uuid}",
                                        headers=headers)

        # If subtemplate doesn't already exist, creates it
        if response.status_code == 404:
            response = self.create_extent(uuid=uuid)
            if response.status_code == 201:
                print(f"{uuid} : {geopycat.utils.okgreen('creation successful')}")
            else:
                print(f"{uuid} : {geopycat.utils.warningred('creation unsuccessful')}")
                sys.exit()
        else:
            print(f"{uuid} : {geopycat.utils.okgreen('already exists')}")

        # Update extent
        name = feature["properties"][self.name]
        gml = geojson_to_geocatgml(feature)
        response = self.update_extent(uuid=uuid, name=name, gml=gml)
        if geopycat.utils.process_ok(response=response):
            print(f"{uuid} : {geopycat.utils.okgreen('update successful')}")
        else:
            print(f"{uuid} : {geopycat.utils.warningred('update unsuccessful')}")

        # Validate extent
        response = self.validate_extent(uuid=uuid)
        if geopycat.utils.process_ok(response=response):
            print(f"{uuid} : {geopycat.utils.okgreen('validation successful')}")
        else:
            print(f"{uuid} : {geopycat.utils.warningred('validation unsuccessful')}")

        # Set permission, good response= 204, no message
        response = self.set_extent_permissions(uuid=uuid)
        if response.status_code == 204:
            print(f"{uuid} : {geopycat.utils.okgreen('set permission successful')}")
        else:
            print(f"{uuid} : {geopycat.utils.warningred('set permission unsuccessful')}")

        # Set ownership
        response = self.set_extent_owner(uuid=uuid)
        if geopycat.utils.process_ok(response=response):
            print(f"{uuid} : {geopycat.utils.okgreen('set ownership successful')}")
        else:
            print(f"{uuid} : {geopycat.utils.warningred('set ownership unsuccessful')}")

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
        print(f"Update all subtemplates - Number of subtemplates : {len(self.ref_geojson['features'])}")  # ← CORRIGÉ

        if with_backup:
            self.backup_subtemplates()

        print("Update all subtemplates : ", end="\r")

        logfile = f"UpdateAllSubtemplates_{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

        log_config = geopycat.utils.get_log_config(logfile, log2stdout = False)
        logging.config.dictConfig(log_config)
        
        logger = logging.getLogger(__name__)

        subtemplate_created = 0
        subtemplate_updated = 0
        subtemplate_creation_failed = 0
        subtemplate_update_failed = 0

        count = 0
        total = len(self.ref_geojson["features"])
        for feature in self.ref_geojson["features"]:

            new_subtemplate = False

            count += 1
            print(f"Update all subtemplates : {round((count / total) * 100, 1)}%", end="\r")

            uuid = f'geocatch-subtpl-extent-{self.type}-{feature["properties"][self.number]}'

            headers = {"accept": "application/xml", "Content-Type": "application/xml"}
            response = self.api.session.get(url=self.api.env + f"/geonetwork/srv/api/registries/entries/{uuid}",
                                            headers=headers)

            # If subtemplate doesn't already exist, creates it
            if response.status_code == 404:
                logger.info(f"{count}/{total} - {uuid} - subtemplate does not already exist")
                response = self.create_extent(uuid=uuid)
                if response.status_code == 201:
                    logger.info(f"{count}/{total} - {uuid} - creation successful")
                    new_subtemplate = True
                    subtemplate_created += 1  # ← DÉPLACÉ ICI (incrémente immédiatement)
                else:
                    logger.error(f"{count}/{total} - {uuid} - creation unsuccessful")
                    subtemplate_creation_failed += 1
                    continue  # If creation failed, stop the process and pass to next subtemplate !
            else:
                logger.info(f"{count}/{total} - {uuid} - subtemplate already exists")

            # Update extent
            name = feature["properties"][self.name]
            gml = geojson_to_geocatgml(feature)
            response = self.update_extent(uuid=uuid, name=name, gml=gml)
            if geopycat.utils.process_ok(response=response):
                logger.info(f"{count}/{total} - {uuid} - update successful")
            else:
                logger.error(f"{count}/{total} - {uuid} - update unsuccessful")
                subtemplate_update_failed += 1
                continue

            # Validate extent
            response = self.validate_extent(uuid=uuid)
            if geopycat.utils.process_ok(response=response):
                logger.info(f"{count}/{total} - {uuid} - validation successful")
            else:
                logger.error(f"{count}/{total} - {uuid} - validation unsuccessful")
                subtemplate_update_failed += 1
                continue

            # Set permission, good response= 204, no message
            response = self.set_extent_permissions(uuid=uuid)
            if response.status_code == 204:
                logger.info(f"{count}/{total} - {uuid} - set permission successful")
            else:
                logger.error(f"{count}/{total} - {uuid} - set permission unsuccessful")
                subtemplate_update_failed += 1
                continue

            # Set ownership
            response = self.set_extent_owner(uuid=uuid)
            if geopycat.utils.process_ok(response=response):
                logger.info(f"{count}/{total} - {uuid} - set ownership successful")
                if not new_subtemplate:  # ← CORRIGÉ : incrémente seulement si c'était un update
                    subtemplate_updated += 1
            else:
                logger.error(f"{count}/{total} - {uuid} - set ownership unsuccessful")
                subtemplate_update_failed += 1
                continue

        print(f"Update all subtemplates : {geopycat.utils.okgreen('Done')}")
        print(f"Subtemplates successfully created : {geopycat.utils.okgreen(subtemplate_created)}")
        print(f"Subtemplates successfully updated : {geopycat.utils.okgreen(subtemplate_updated)}")
        print(f"Subtemplates unsuccessfully created : {geopycat.utils.warningred(subtemplate_creation_failed)}")
        print(f"Subtemplates unsuccessfully updated : {geopycat.utils.warningred(subtemplate_update_failed)}")

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

        logfile = f"DeleteSubtemplates_{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

        log_config = geopycat.utils.get_log_config(logfile, log2stdout = False)
        logging.config.dictConfig(log_config)
        
        logger = logging.getLogger(__name__)

        count = 0
        for uuid in uuids:
            count += 1

            headers = {"Content-Type": "application/json", "Accept": "application/json"}

            response = self.api.session.delete(url=self.api.env + f"/geonetwork/srv/api/records/{uuid}",
                                                headers=headers)

            if response.status_code == 204:
                logger.info(f"{count}/{len(uuids)} - {uuid} - successfully deleted")
                subtemplates_deleted += 1
            else:
                logger.error(f"{count}/{len(uuids)} - {uuid} - unsuccessfully deleted")
                subtemplates_delete_failed += 1

            print(f"Delete subtemplates : {round((count / len(uuids)) * 100, 1)}%", end="\r")
        print(f"Delete subtemplates : {geopycat.utils.okgreen('Done')}")
        print(f"Subtemplates successfully deleted : {geopycat.utils.okgreen(subtemplates_deleted)}")
        print(f"Subtemplates unsuccessfully deleted : {geopycat.utils.warningred(subtemplates_delete_failed)}")
