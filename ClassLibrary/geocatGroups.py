import requests
import json
from requests.auth import HTTPBasicAuth
import geocatConstants as const
from geocatApiCalls import GeocatSession

class GeocatGroups():
    """this class is a container-class for the GeocatGroup-class"""

    def __init__(self, urlPrefix :str, user :str, password :str):
        self.__urlPrefix = urlPrefix
        self.__user = user
        self.__password = password
        self.__sessionCalls = GeocatSession(urlPrefix, "eng/info?type=me", user, password)
        self.__groupOwners = self.__loadGroups()

    def __loadGroups(self):
        _resultList = []
        _response = self.__sessionCalls.sendGetRequest("api/0.1/groups?withReservedGroup=false").json()
        for group in _response:
            gG = GeocatGroup(group)
            _resultList.append(gG)
        return _resultList

    def getGroupOwnerId(self, groupOwnerName :str):
        for owner in self.groupOwners:
            if owner.labelGer.find(groupOwnerName) != -1:
                return owner.groupId
        return -1

    def __getGroupOwners(self):
        return self.__groupOwners
    groupOwners = property(__getGroupOwners)

class GeocatGroup():
    """description of class"""

    def __init__(self, group :dict):
        self.__logo = group['logo']
        self.__website = group['website']
        self.__defaultCategory = group['defaultCategory']
        self.__allowedCategories = group['allowedCategories']
        self.__enableAllowedCategories = group['enableAllowedCategories']
        self.__id = group['id']
        self.__email = group['email']
        self.__referrer = group['referrer']
        self.__name = group['name']
        self.__description = group['description']
        self.__labelGer = group['label']['ger']
        self.__labelIta = group['label']['ita']
        self.__labelFre = group['label']['fre']
        self.__labelRoh = group['label']['roh']
        self.__labelEng = group['label']['eng']


    def __getLogo(self):
        return self.__logo
    logo = property(__getLogo)

    def __getWebsite(self):
        return self.__website
    website = property(__getWebsite)

    def __getDefaultCategory(self):
        return self.__defaultCategory
    defaultCategory = property()

    def __getAllowedCategories(self):
        return self.__allowedCategories
    allowedCategories = property()

    def __getEnableAllowedCategories(self):
        return self.__enableAllowedCategories
    enableAllowedCategories = property()

    def __getId(self):
        return self.__id
    groupId = property(__getId)

    def __getEmail(self):
        return self.__email
    email = property(__getEmail)

    def __getReferrer(self):
        return self.__referrer
    referrer = property(__getReferrer)

    def __getName(self):
        return self.__name
    name = property(__getName)

    def __getDescription(self):
        return self.__description
    description = property(__getDescription)

    def __getLabelGer(self):
        return self.__labelGer
    labelGer = property(__getLabelGer)

    def __getLabelIta(self):
        return self.__labelIta
    labelIta = property(__getLabelIta)

    def __getLabelFre(self):
        return self.__labelFre
    labelFre = property(__getLabelFre)

    def __getLabelRoh(self):
        return self.__labelRoh
    labelRo = property(__getLabelRoh)

    def __getLabelEng(self):
        return self.__labelEng
    labelEng = property(__getLabelEng)

