
import time
import requests
from requests.auth import HTTPBasicAuth
import json
import geocatConstants as const

class GeocatSession():
    """
    With this class it is easier to call the REST API 
    urlPrefix: the current environment, INT or PROOD defined in geocatConstants
    urlValue: use to get cookies
    user: username of the current user
    password: current password from user
    """

    def __init__(self, urlPrefix :str, urlValue :str, user :str, password :str):
        self.__urlPrefix = urlPrefix
        self.__proxyDict = const.proxyDict
        self.__user = user
        self.__password = password
        self.__session = requests.Session()
        self.sendPostRequest(urlValue)
        self.__cookies = self.__getCookies()
        self.__token = self.__cookies["XSRF-TOKEN"]
        self.__headers = {}
        self.setApplicationInHeadersTo("json")

    def __retry(myRequest, *args):
        _retries = 1
        _success = False
        while not _success or _retries > 5:
            try:
                _response = myRequest
                _success = True
            except Exception as e:
                wait = _retries * 30
                print("Error! Waiting " + wait + " secs and re-trying...")
                time.sleep(wait)
                _retries += 1
        return _response

    def __getCookies(self):
        return self.__session.cookies.get_dict()
    cookies = property(__getCookies)

    def sendPostRequest(self, urlValue :str, data=""):
        """ send post request to get the cookies and its token """
        url = self.__urlPrefix + urlValue
        if not data:
            return self.__session.post(url, proxies=self.__proxyDict, verify=False, auth=HTTPBasicAuth(self.__user, self.__password))
        else:
            # using to upload an attachment
            files = {'file': open(data, 'rb')}
            return self.__session.post(url, files=files, proxies=self.__proxyDict, verify=False, auth=HTTPBasicAuth(self.__user, self.__password), headers=self.__headers, cookies=self.__cookies)

    def sendGetRequest(self, urlValue :str):
        """ Get the response of an api get request
        :urlValue: is need to complete the url with the urlPrefix (current environment INT or PROD)
        :return: the MD recorde as response of te getRequest
        """
        if urlValue.startswith("http"):
            url = urlValue
        else:
            url = self.__urlPrefix + urlValue
        try:
            response = self.__session.get(url, proxies=self.__proxyDict, verify=False, auth=HTTPBasicAuth(self.__user, self.__password), headers=self.__headers, cookies=self.__cookies)
        except Exception as e:
            response = self.__retry(self.__session.get(url, proxies=self.__proxyDict, verify=False, auth=HTTPBasicAuth(self.__user, self.__password), headers=self.__headers, cookies=self.__cookies))
        return response

    def sendPutRequest(self, urlValue :str, value, xpath :str):
        """
        Edit the MD with batchedit
        :urlValue: is need to add to the urlPrefix (current environment INT or PROD)
        :value: the batchedit value data
        :xpath: select the xmlNode(s) which you edit
        :return: the response of the putRequest
        """
        if xpath:
            jsonInput = {"value": value, "xpath": xpath}
            payload = r"[" + json.dumps(jsonInput) + "]"
        else:
            payload = value
        url = self.__urlPrefix + urlValue
        try:
            response = self.__session.put(url, data=payload, proxies=self.__proxyDict, verify=False, auth=HTTPBasicAuth(self.__user, self.__password), headers=self.__headers, cookies=self.__cookies)
        except :
            response = self.__retry(self.__session.put(url, data=payload, proxies=self.__proxyDict, verify=False, auth=HTTPBasicAuth(self.__user, self.__password), headers=self.__headers, cookies=self.__cookies))
        return response

    def setApplicationInHeadersTo(self, appValue :str):
        """ Set the accept and Content-Type to --application/json-- or --application/xml--
        Default value is json
        :appValue: possible values are: json or xml
        """
        def setContentTypeInHeadersTo(contValue :str):
            """ Set the accept and Content-Type to --application/json-- or --application/xml--
            Default value is json
            :appValue: possible values are: json or xml
            """
            if contValue == "json" or contValue == "xml":
                value = appValue
                self.__headers['Content-Type'] = "application/" + value
        
        if appValue == "json" or appValue == "xml":
            value = appValue
            self.__headers['accept'] = "application/" + value
            setContentTypeInHeadersTo(appValue)
        else:
            value = "json"
            self.__headers['accept'] = "application/" + value
            setContentTypeInHeadersTo(value)
        self.__headers['X-XSRF-TOKEN'] = self.token

    def getToken(self):
        """ Get the token of the current cookie """
        return self.__token
    token = property(getToken)


class GeocatRequests():
    """ 
    :urlPrefix: the current environment, INT or PROOD defined in geocatConstants
    :user: username of the current user
    :password: current password from user
    """
    def __init__(self, urlPrefix :str, user :str, password :str):
        self.__urlPrefix = urlPrefix
        self.__user = user
        self.__password = password

    def sendGetRequest(self, urlValue :str):
        _retries = 1
        _isSuccess = False
        if urlValue.startswith("http"):
            url = urlValue
        else:
            url = self.__urlPrefix + urlValue
        while not _isSuccess or _retries > 5:
            try:
                response = requests.get(url, proxies=const.devProxyDict, verify=False, auth=HTTPBasicAuth(self.__user, self.__password))
                _isSuccess = True
            except Exception as e:
                wait = _retries * 30
                print("Error! Waiting " + str(wait) + " secs and re-trying...")
                time.sleep(wait)
                _retries += 1
                response = requests.get(url, proxies=const.proxyDict, verify=False, auth=HTTPBasicAuth(self.__user, self.__password))
        return response

