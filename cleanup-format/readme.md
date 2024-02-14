# Clean up format subtemplate
![Static Badge](https://img.shields.io/badge/Python-3.9%2B-%2334eb77)

Format subtemplate are solely managed by the geocat team. This tool take correction information from an excel file and apply them to the format subtemplate 

The tools performs the following :

* Rename format name and set empty version in subtemplate
* Rename accordingly all online resource protocol that use a renamed format name. In the case : `WWW:DOWNLOAD:{format-name}`
* Migrate duplicated one or wrong one to correct one in metadata (change UUID)


## Installation
Clone the repo and install dependencies in a python virtual environment (recommended)
```
git clone https://github.com/geoadmin/tool-geocat.git

cd tool-geocat/cleanup-format

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### at swisstopo (using powershell)
```
git clone https://github.com/geoadmin/tool-geocat.git

cd tool-geocat/cleanup-format

& "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\Scripts\pip3" install --trusted-host github.com --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --proxy=proxy-bvcol.admin.ch:8080 -r requirements.txt
```

## Usage
Read the correction from an excel file and transform it into a pandas dataframe. In the end, the dataframe should have the folloring structure :
```
# df structure
# col[2] : new format name
# col[4] : format UUID
# col[5] : replaced by other format (UUID)
# col[6] : former format name
# col[7] : former version
``` 
The run the `cleanup_format(df: pd.DataFrame)` function from `main.py` giving the dataframe as argument.

After the clean-up, following actions are required :
* Delete format subtemplate that have been replaced (they should not be linked to any metadata anymore)
* Re-index all metadata (otherwise, changes in format are not reflected in index and thus default view)