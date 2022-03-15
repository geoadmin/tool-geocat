
import requests
from requests.auth import HTTPBasicAuth
import json
import geocatConstants as const

class geocatSession():
    """
    With this class it is easier to call the REST API 
    :urlPrefix: the current environment, INT or PROOD defined in geocatConstants
    :urlValue: use to get cookies
    :user: username of the current user
    :password: current password from user
    """

    def __init__(self, urlPrefix :str, urlValue :str, user :str, password :str):
        self._urlPrefix = urlPrefix
        self._proxyDict = const.proxyDict
        self._user = user
        self._password = password
        self._session = requests.Session()
        self.sendPostRequest(urlValue)
        self._cookies = self.getCookies()
        self._token = self._cookies["XSRF-TOKEN"]
        self._headers = {}
        self.setApplicationInHeadersTo("json")

    def getCookies(self) -> dict:
        return self._session.cookies.get_dict()

    def sendPostRequest(self, urlValue :str):
        """ send post request to get the cookies and its token """
        url = self._urlPrefix + urlValue
        self._session.post(url, proxies=self._proxyDict, verify=False, auth=HTTPBasicAuth(self._user, self._password))

    def sendGetRequest(self, urlValue :str) -> type:
        """ Get the response of an api get request
        :urlValue: is need to complete the url with the urlPrefix (current environment INT or PROD)
        :return: the MD recorde as response of te getRequest
        """
        url = self._urlPrefix + urlValue
        return self._session.get(url, proxies=self._proxyDict, verify=False, auth=HTTPBasicAuth(self._user, self._password), headers=self._headers, cookies=self._cookies)

    def sendPutRequest(self, urlValue :str, value :str, xpath :str) -> type:
        """
        Edit the MD with batchedit
        :urlValue: is need to add to the urlPrefix (current environment INT or PROD)
        :value: the batchedit value data
        :xpath: select the xmlNode(s) which you edit
        :return: the response of the putRequest
        """
        jsonInput = {"value": value, "xpath": xpath}
        payload = r"[" + json.dumps(jsonInput) + "]"
        url = self._urlPrefix + urlValue
        return self._session.put(url, data=payload, proxies=self._proxyDict, verify=False, auth=HTTPBasicAuth(self._user, self._password), headers=self._headers, cookies=self._cookies)

    def setApplicationInHeadersTo(self, appValue :str):
        """ Set the accept and Content-Type to --application/json-- or --application/xml--
        Default value is json
        :appValue: possible values are: json or xml
        """
        if appValue == "json" or appValue == "xml":
            value = appValue
        else:
            value = "json"
        self._headers['accept'] = "application/" + value
        self._headers['Content-Type'] = "application/" + value
        self._headers['X-XSRF-TOKEN'] = self.token

    def getToken(self) -> str:
        """ Get the token of the current cookie """
        return self._token

    token = property(getToken)


class geocatRequests():
    """ 
    :urlPrefix: the current environment, INT or PROOD defined in geocatConstants
    :user: username of the current user
    :password: current password from user
    """
    def __init__(self, urlPrefix :str, user :str, password :str):
        self._urlPrefix = urlPrefix
        self._user = user
        self._password = password

    def sendGetRequest(self, urlValue :str) -> type:
        if urlValue.startswith("http"):
            url = urlValue
        else:
            url = self._urlPrefix + urlValue
        return requests.get(url, proxies=const.proxyDict, verify=False, auth=HTTPBasicAuth(self._user, self._password))
