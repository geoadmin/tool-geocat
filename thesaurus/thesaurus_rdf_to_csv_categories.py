# -*- coding: iso-8859-1 -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      U80858786 (egs) in 2021

Purpose:    It takes the rdf from the geocat-website and writes all the keywords with its translations into a table.
            Currently, this csv-file is part of the documentation on CMS.
            It also includes the categories. This script was created during the cleanup of the geocat-ch-Thesarus and
            it creates the final output

Variables:  RDF_name - filename of the RDF-file of the thesaurus (without the path)
            Path - path to where the RDF-file lies (without RDF_name). The newly created csvs and textfiles will be
                   located in this path with the filename of the RDF
                   
Remarks:    ADAPT THE VARIABLES IN LINES THE LINES BELOW
            In case a new categorie was added to the thesaurus, you also have to add it with its translation in the
            dictionary called trans_dict
------------------------------------------------------------------------------------------------------------------------
"""
import xml.etree.ElementTree as etree
import os
import pandas as pd
import urllib3
pd.options.mode.chained_assignment = None


# TODO: adapt the following variables
RDF_name = "geocat_new.rdf"
Path = r"\\v0t0020a.adr.admin.ch\prod\kogis\igeb\geocat\Koordination Geometadaten (573)\geocat.ch Management\geocat.ch Applikation\geocat.ch-Scripts\thesaurus"

########################################################################################################################

parser = etree.XMLParser(encoding='UTF-8')
code, de, fr, it, en, de_scope = {}, {}, {}, {}, {}, {}

# translation for the categories
trans_dict = {"Basiskarten, Bodenbedeckung, Bilddaten": "Cartes de référence, couverture du sol, images aériennes",
              "Ortsangaben, Referenzsysteme": "Localisation, systèmes de référence",
              "Höhen": "Altimétrie",
              "Politische und administrative Grenzen": "Limites politiques et administratives",
              "Raumplanung, Grundstückkataster": "Développement territorial, cadastre foncier",
              "Geologie, Boden, naturbedingte Risiken": "Géologie, sols, dangers naturels",
              "Wald, Flora, Fauna": "Forêt, flore, faune",
              "Gewässer": "Hydrographie",
              "Atmosphäre, Luft, Klima": "Atmosphère, climatologie",
              "Umwelt-, Naturschutz": "Protection de l'environnement et de la nature",
              "Bevölkerung, Gesellschaft, Kultur": "Population, société, culture ",
              "Gesundheit": "Santé",
              "Gebäude, Anlagen": "difices, infrastructures, ouvrages",
              "Verkehr": "Transport",
              "Ver-, Entsorgung, Kommunikation": "Approvisionnement, élimination, communication",
              "Militär, Sicherheit": "Armée, sécurité",
              "Landwirtschaft": "Agriculture",
              "Wirtschaftliche Aktivitäten": "Activités économiques",
              "Administration": "Administration",
              "Datenhaltung, Datenbereitstellung": "Gestion des données, fourniture de données",
              "": ""}  
              # there is also one empty word here, in case somebody forgets to record the category in geocat.ch

# check if path and file exist
if os.path.isfile(os.path.join(Path, RDF_name)):
    # get the rdf-file
    tree = etree.parse(os.path.join(Path, RDF_name), parser)
    root = tree.getroot()
    descriptions = list(root)
    for desc in descriptions:
        if list(desc.attrib.keys())[0] == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about":
            cat_id = list(desc.attrib.values())[0]
            try:
                code[cat_id] = cat_id.split("#")[1]
            except:
                pass
            labels = list(desc)
            for jj in labels:
                # get the keywords and the description in the rdf-file
                if jj.tag == '{http://www.w3.org/2004/02/skos/core#}prefLabel':
                    if list(jj.attrib.values())[0] == "de":
                        de[cat_id] = jj.text
                    elif list(jj.attrib.values())[0] == "fr":
                        fr[cat_id] = jj.text
                    elif list(jj.attrib.values())[0] == "it":
                        it[cat_id] = jj.text
                    elif list(jj.attrib.values())[0] == "en":
                        en[cat_id] = jj.text
                elif jj.tag == '{http://www.w3.org/2004/02/skos/core#}scopeNote':
                    if list(jj.attrib.values())[0] == "de":
                        de_scope[cat_id] = jj.text


    # put it all into one dataframe
    data_de = pd.DataFrame.from_dict(de, orient='index', columns=['Deutsch'])
    data_fr = pd.DataFrame.from_dict(fr, orient='index', columns=['Français'])
    data_it = pd.DataFrame.from_dict(it, orient='index', columns=['Italiano'])
    data_en = pd.DataFrame.from_dict(en, orient='index', columns=['English'])
    data_de_scope = pd.DataFrame.from_dict(de_scope, orient='index', columns=['Kategorie (de)'])
    df_all = pd.concat([data_de_scope, data_de, data_fr, data_it, data_en], axis=1, join='outer')
    df_all["Categorie (fr)"] = ""
    for m in range(len(df_all)):
        df_all["Categorie (fr)"][m] = trans_dict[df_all['Kategorie (de)'][m]]
    df_all.fillna("", inplace=True)
    df_all = df_all[['Kategorie (de)', 'Categorie (fr)', 'Deutsch', 'Français', 'Italiano', 'English']]


    # save it to a CSV
    # The new columns are created in order to correctly sort, also with special characters and upper and lower cases.
    # These new columns are deleted after the sorting (In newer versions there would be the "key"-option in sort_values.
    filename = RDF_name.split(".")[0]
    df_all_fr = df_all.copy()
    df_all["kat_de"] = df_all["Kategorie (de)"].str.lower().str.normalize('NFD')
    df_all_fr["kat_fr"] = df_all_fr["Categorie (fr)"].str.lower().str.normalize('NFD')
    df_all["de"] = df_all["Deutsch"].str.lower().str.normalize('NFD')
    df_all_fr["fr"] = df_all_fr["Français"].str.lower().str.normalize('NFD')
    df_all_fr.sort_values(by=['kat_fr', 'fr'], inplace=True)
    df_all.sort_values(by=['kat_de', 'de'], inplace=True)
    del df_all["kat_de"], df_all_fr["kat_fr"], df_all_fr["fr"], df_all["de"]
    df_all.to_csv(os.path.join(Path, filename + ".csv"), sep=';', encoding='utf-8-sig', index=False)
    print("Number of Keywords: " + str(len(df_all)))


    # save it to textfile. One for german and one for french
    cat_names = df_all["Kategorie (de)"].unique()
    cat_names_fr = df_all_fr["Categorie (fr)"].unique()

    if os.path.isfile(os.path.join(Path, filename + "_de.txt")):
        os.remove(os.path.join(Path, filename + "_de.txt"))
    if os.path.isfile(os.path.join(Path, filename + "_fr.txt")):
        os.remove(os.path.join(Path, filename + "_fr.txt"))

    for name in cat_names:
        file1 = open(os.path.join(Path, filename + "_de.txt"), 'a')
        file1.write(name + "\n")
        df_test = df_all.loc[df_all["Kategorie (de)"] == name]
        for i in range(len(df_test)):
            file1.write(df_test['Deutsch'][i] + "\n")
        file1.write("\n")
        file1.close()

    for name_fr in cat_names_fr:
        file2 = open(os.path.join(Path, filename + "_fr.txt"), 'a')
        file2.write(name_fr + "\n")
        df_test_fr = df_all_fr.loc[df_all_fr["Categorie (fr)"] == name_fr]
        for i in range(len(df_test_fr)):
            file2.write(df_test_fr['Français'][i] + "\n")
        file2.write("\n")
        file2.close()
       
    print("Files were saved: " + os.path.join(Path, filename + ".csv"))

else:
    print("Folder or RDF-file don't exist... Check your inputs to the script")
