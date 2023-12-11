import pandas as pd
import geopycat

geocat = geopycat.geocat()

# Read excel file
df = pd.read_excel("//v0t0020a.adr.admin.ch/prod/kogis/igeb/"\
    "geocat/Koordination Geometadaten (573)/geocat.ch Management/"\
    "geocat.ch Applikation/geocat.ch-Qualität/Bereinigung Formate/"\
    "geocat_Formate_Vergleich.xlsx")

# Filter df with first col value == "X" 
# (format to be cleaned-up automatically)
df = df[df.iloc[:,0] == "X"]

# df structure
# col[2] : new format name
# col[4] : format UUID
# col[5] : replaced by other format (UUID)
# col[6] : former format name
# col[7] : former version


def cleanup_format(df: pd.DataFrame):
    for index, row in df.iterrows():

        # Replace format name and set empty version
        body = [
            {
                "xpath": "/gmd:MD_Format/gmd:name/gco:CharacterString",
                "value": f"<gn_replace>{row[2]}</gn_replace>"
            },
            {
                "xpath": "/gmd:MD_Format/gmd:version",
                "value": "<gn_delete></gn_delete>"
            },
            {
                "xpath": "/gmd:MD_Format/gmd:version",
                "value": "<gn_add>"\
                            "<gmd:version xmlns:gco='http://www.isotc211.org/2005/gco' "\
                            "xmlns:gmd='http://www.isotc211.org/2005/gmd' gco:nilReason='unknown'/>"\
                        "</gn_add>"
            }
        ]

        try:
            res = geocat.edit_metadata(uuid=row[4], body=body, updateDateStamp=False)
        except:
            print(geopycat.utils.warningred(f"Format UUID : {row[4]} could not be updated"))
            continue

        if geopycat.utils.process_ok(res):
            print(geopycat.utils.okgreen(f"Format UUID : {row[4]} successfully updated"))
        else:
            print(geopycat.utils.warningred(f"Format UUID : {row[4]} could not be updated"))
            continue

        if not pd.isnull(row[5]):
            geocat.search_and_replace(
                search=f'xlink:href="local://srv/api/registries/entries/{row[4]}',
                replace=f'xlink:href="local://srv/api/registries/entries/{row[5]}')


def revert_cleanup(df: pd.DataFrame):
    for index, row in df.iterrows():

        # Replace format name and set empty version
        body = [
            {
                "xpath": "/gmd:MD_Format/gmd:name/gco:CharacterString",
                "value": f"<gn_replace>{row[6]}</gn_replace>"
            },
            {
                "xpath": "/gmd:MD_Format/gmd:version",
                "value": "<gn_delete></gn_delete>"
            },
            {
                "xpath": "/gmd:MD_Format/gmd:version",
                "value": "<gn_add>"\
                            "<gmd:version xmlns:gmd='http://www.isotc211.org/2005/gmd'>"\
                            f"{row[7]}</gmd:version>"
                        "</gn_add>"
            }
        ]

        try:
            res = geocat.edit_metadata(uuid=row[4], body=body, updateDateStamp=False)
        except:
            print(geopycat.utils.warningred(f"Format UUID : {row[4]} could not be updated"))
            continue

        if geopycat.utils.process_ok(res):
            print(geopycat.utils.okgreen(f"Format UUID : {row[4]} successfully updated"))
        else:
            print(geopycat.utils.warningred(f"Format UUID : {row[4]} could not be updated"))
            continue

