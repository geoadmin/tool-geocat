

class Authority():
    """executive- or legislative-Authority"""

    def __init__(self, authority :dict):
        self.__id = authority.get('id')
        self.__name = authority.get('name')
        self.__nameDe = authority.get('nameDe')
        self.__nameFr = authority.get('nameFr')
        self.__nameIt = authority.get('nameIt')
        self.__nameRm = authority.get('nameRm')
        self.__abbr = authority.get('abbr')
        self.__abbrDe = authority.get('abbrDe')
        self.__abbrFr = authority.get('abbrFr')
        self.__abbrIt = authority.get('abbrIt')
        self.__abbrRm = authority.get('abbrRm')
        self.__url = authority.get('url')
        self.__urlDe = authority.get('urlDe')
        self.__urlFr = authority.get('urlFr')
        self.__urlIt = authority.get('urlIt')
        self.__urlRm = authority.get('urlRm')

    def __getId(self):
        return self.__id
    id = property(__getId)

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

    def __getAbbr(self):
        return self.__abbr
    abbr = property(__getAbbr)

    def __getAbbrDe(self):
        return self.__abbrDe
    abbrDe = property(__getAbbrDe)

    def __getAbbrFr(self):
        return self.__abbrFr
    abbrFr = property(__getAbbrFr)

    def __getAbbrIt(self):
        return self.__abbrIt
    abbrIt = property(__getAbbrIt)

    def __getAbbrRm(self):
        return self.__abbrRm
    abbrRm = property(__getAbbrRm)

    def __getUrl(self):
        return self.__url
    url = property(__getUrl)

    def __getUrlDe(self):
        return self.__urlDe
    urlDe = property(__getUrlDe)

    def __getUrlFr(self):
        return self.__urlFr
    urlFr = property(__getUrlFr)

    def __getUrlIt(self):
        return self.__urlIt
    urlIt = property(__getUrlIt)

    def __getUrlRm(self):
        return self.__urlRm
    urlRm = property(__getUrlRm)
