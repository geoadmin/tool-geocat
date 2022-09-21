
class LegalBase():
    """description of class"""

    def __init__(self, legalBase :dict):
        self.__id = legalBase.get('id')
        self.__legislativeEntryLegalBasisId = legalBase.get('legislativeEntryLegalBasisId')
        self.__corp = legalBase.get('corp')
        self.__startDate = legalBase.get('startDate')
        self.__endDate = legalBase.get('endDate')
        self.__name = legalBase.get('name')
        self.__abbr = legalBase.get('abbr')
        self.__url = legalBase.get('url')
        self.__code = legalBase.get('code')
        self.__example = legalBase.get('example')
        self.__exampleDe = legalBase.get('exampleDe')
        self.__exampleFr = legalBase.get('exampleFr')
        self.__exampleIt = legalBase.get('exampleIt')
        self.__exampleRm = legalBase.get('exampleRm')
    #

    def __getId(self):
        return self.__id
    id = property(__getId)

    def __getLegislativeEntryLegalBasisId(self):
        return self.__legislativeEntryLegalBasisId
    legislativeEntryLegalBasisId = property(__getLegislativeEntryLegalBasisId)

    def __getCorp(self):
        return self.__corp
    corp = property(__getCorp)

    def __getStartDate(self):
        return self.__startDate
    startDate = property(__getStartDate)

    def __getEndDate(self):
        return self.__endDate
    endDate = property(__getEndDate)

    def __getName(self):
        return self.__name
    name = property(__getName)

    def __getAbbr(self):
        return self.__abbr
    abbr = property(__getAbbr)

    def __getUrl(self):
        return self.__url
    url = property(__getUrl)

    def __getCode(self):
        return self.__code
    code = property(__getCode)

    def __getExample(self):
        return self.__example
    example = property(__getExample)

    def __getExampleDe(self):
        return self.__exampleDe
    exampleDe = property(__getExampleDe)

    def __getExampleFr(self):
        return self.__exampleFr
    exampleFr = property(__getExampleFr)

    def __getExampleIt(self):
        return self.__exampleIt
    exampleIt = property(__getExampleIt)

    def __getExampleRm(self):
        return self.__exampleRm
    exampleRm = property(__getExampleRm)

