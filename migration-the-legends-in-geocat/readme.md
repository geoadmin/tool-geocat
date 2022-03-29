# Integrate the legends from techLayer, which have legends, in geocat-MD-records
With this script, you can add png and pdf Legendfiles to MD-records as attachment
This is a one time use Script! But it give an example, how to add files as attachment
Autor:
	Reithmeier Martin (rem) in 2022
Proceed:
    1. Download all needed legends to a local folder e.g. C:/downloads/legendsTemp
    2. Create a list with uuid, related png-Filename and related pdf-Filename
    3. Add all legends as attachement to MD-Records from the local folder
    4. Add all legends as onlineResources with this protocols: LEGEND:PDF | LEGEND:PNG
Remarks:
	All legends are on https://github.com/geoadmin/mf-chsdi3/tree/master/chsdi/static/images/legends/
    All pdf-legends has a related png-legend but not all png-legends has a related pdf-legend
Important:
	It is not easy to download files from a github repository. The workaround is: Download the complete repo as zip-file
    and extract only the legend folder to a local folder e.g. C:/downloads/legendsTemp
### Requirements
This script runs on python 3. 
It is need to have:
* A csv file with uuids and the related techLayer-Name. This is an export from BOD
* 
### Usage
1. Clone the repository anywhere you like.






