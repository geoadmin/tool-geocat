# Remove_BGDI_Keyword_from_list
The uuid list is given from Veronique Constantin in a excel-sheet
With this script, you can add or delete the keyword {BGDI Bundesgeodaten-Infrastruktur} from MDs with the given list of uuids 
Lots of documentations are directly in the scrtipt

### Requirements
This script runs on python 3.7
- sys
- urllib3
- Path from pathlib
- HTTPBasicAuth from requests.auth
- geocatLoginGUI
- \* from geocatFunctionLib

### Usage
1. Clone the repository anywhere you like.
2. Clone ClassLibrary in the same root-Folder
2. Open the python files either with an IDE or a text editor.
3. Run the file with a python 3 interpreter. (swisstopo : C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe) or direct from the IDE

### Remarks
If you use this script outside from **Visual Studio** it is necessary to add the following statments
```Python
import sys
sys.path.append("..\\ClassLibrary")
```

### Methods
<details><summary>getKeywordNode</summary>

    ````Python
    def getKeywordNode(isThesaurusExist):
        """
        Purpose:
        if the script in add-mode, this method return a xml-node-object from type Element

        Parameter:
        :isThesaurusExist: [bool]
            :True
                need to add the keyword if any keywords exist for geocat
                returns only the keyword-node
            :False
                need to add the keyword if no other keyword exist for geocat
                returns the full descriptiveKeywords-node

        return:
            :xmlFragmentString [Element]
        """
        pass
    ````
</details>

<details><summary>checkIsKeywordExist</summary>

    ````Python
    def checkIsKeywordExist(sessionCalls, uuid, mdRecord):
        """
        Purpose:
        if the script was broken by a proxy-error it is helpfull to know which MD must skip if you run the script again

        Parameter:
            :sessionCalls: [API.geocatSession] current API session-object
            :uuid: [str] the uuid from MD
            :mdRecord: [Element]

        return:
            True if exist otherwise False
        """
        pass
    ````
</details>

<details><summary>addKeywords</summary>

    ````Python
    def addKeywords(gcRequests, uuidsList):
        """
        Purpose:
        add the keyword {BGDI Bundesgeodaten-Infrastruktur} to all mdRecord which uuid is in list

        Parameter:
            :gcRequests: [dict] current API session- and request-object
            :uuidsList: [list] all used uuids

        return:
            void
        """
        pass
    ````
</details>

<details><summary>removeKeyword</summary>

    ````Python
    def removeKeyword(sessionCalls, mdRecordDetails, mdRecordAsElement):
        """
        Purpose:

        """
        pass
    ````
</details>

<details><summary>removeKeywords</summary>

    ````Python
    def removeKeywords(gcRequests, uuidsList):
        """
        Purpose:
        remove the keyword {BGDI Bundesgeodaten-Infrastruktur} from all mdRecord which uuid is in list

        Parameter:
            :gcRequests: [dict] current API session- and request-object
            :uuidsList: [list] all used uuids

        return:
            void
        """
        pass
    ````
</details>

<details><summary>main</summary>

    ````Python
    def main():
        """
        Purpose:
        """
        pass
    ````
</details>

  
  
  
  
