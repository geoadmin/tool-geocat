

class GeoCategory():
    """The geo-categories are oriented on the official eCH-0166 standard.
    To see the standard description please use https://www.ech.ch/de/standards/39393 """

    def __init__(self, gCategory :dict):
        self.__id = gCategory.get('id')
        self.__code = gCategory.get('code')
        self.__notation = gCategory.get('notation')
        self.__number = gCategory.get('number')
        self.__parent = gCategory.get('parent')
        self.__name = gCategory.get('name')
        self.__nameDe = gCategory.get('nameDe')
        self.__nameFr = gCategory.get('nameFr')
        self.__nameIt = gCategory.get('nameIt')
        self.__nameRm = gCategory.get('nameRm')
    #

    def __getId(self):
        return self.__id
    id = property(__getId)

    def __getCode(self):
        return self.__code
    code = property(__getCode)

    def __getNotation(self):
        return self.__notation
    notation = property(__getNotation)

    def __getNumber(self):
        return self.__number
    number = property(__getNumber)

    def __getParent(self):
        return self.__parent
    parent = property(__getParent)

    def __getName(self):
        return self.__name
    name = property(__getName)

    def __getNameDe(self):
        return self.__nameDe
    nameDe = property(__getNameDe)

    def __getNameFr(self):
        return self.__nameFr
    nameFr = property(__getNameFr)

    def __getNameIt(self):
        return self.__nameIt
    nameIt = property(__getNameIt)

    def __getNameRm(self):
        return self.__nameRm
    nameRm = property(__getNameRm)

