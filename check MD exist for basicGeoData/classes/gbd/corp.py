
"""
    In this modul is the definition of the class Corp, which is a representation
    of the corporation on the geobasisdaten platform.
"""

class Corp():
    """ Basic corporation class for inheritence
        
    Parameter:
      corporation (dict): the data of corporation 
    
    Attribute:
      _id: ID of corp as int
      _parent: ID of Parent corp as int (Nullable)
                The ID of the parent of the given corp. The only corp without parent is the federal government.

      _level: "federal" "canton" "community" "region" "county" "corp" (enum)
                This is used to represent the federalism.
      _bfsNumber: 

      _parentBfsNumber:

      _filterDisplay: The name of the corp as it is shown on the geobasisdaten website.
                        This is normally the name of the corp prefixed with the level. 
                        This is always returned in the requested language.
                        Example: Request for de: Kanton Bern, request for fr: Canton Berne

      _abbr:  The abbreviation of the corp. This is a short form for the name and used as prefix for corp specific catalogs.
      _name:  The default name of the given corp.
      _nameDe: The name of the given corp in de.
      _nameFr: The name of the given corp in fr.
      _nameIt: The name of the given corp in it.
      _nameRm: The name of the given corp in rm.
    """

    def __init__(self, corporation :dict):
        self.__id = corporation.get('id')
        self.__parent = corporation.get('parent')
        self.__level = corporation.get('level')
        self.__bfsNumber = corporation.get('bfsNumber')
        self.__parentBfsNumber = corporation.get('parentBfsNumber')
        self.__filterDisplay = corporation.get('filterDisplay')
        self.__abbr = corporation.get('abbr')
        self.__name = corporation.get('name')
        self.__nameDe = corporation.get('nameDe')
        self.__nameFr = corporation.get('nameFr')
        self.__nameIt = corporation.get('nameIt')
        self.__nameRm = corporation.get('nameRm')

    def __getCorporationID(self):
        """ ID of corporation as int """
        return self.__id
    corporationID = property(__getCorporationID)

    def __getGovernmentSystemLevel(self):
        """ ID of Parent corp as int (Nullable) \n\tThe ID of the parent of the given corporation. The only corporation without parent is the federal government. """
        return self.__level
    governmentSystemLevel = property(__getGovernmentSystemLevel)

    def __getFullCorporationName(self):
        """ The name of the corp as it is shown on the geobasisdaten website """
        return self.__filterDisplay
    filterDisplay = property(__getFullCorporationName)

    def __getAbbreviation(self):
        """ The abbreviation of the corp """
        return self.__abbr
    abbreviation = property(__getAbbreviation)

    def __getCorporationName(self):
        """ The default name of the given corp """
        return self.__name
    corporationName = property(__getCorporationName)

    def __getNameDe(self):
        """ The name of the given corp in de """
        return self.__nameDe
    nameDe = property(__getNameDe)

    def __getNameFr(self):
        """ The name of the given corp in fr """
        return self.__nameFr
    nameFr = property(__getNameFr)

    def __getNameIt(self):
        """ The name of the given corp in it """
        return self.__nameIt
    nameIt = property(__getNameIt)

    def __getNameRm(self):
        """ The name of the given corp in rm """
        return self.__nameRm
    nameRm = property(__getNameRm)
