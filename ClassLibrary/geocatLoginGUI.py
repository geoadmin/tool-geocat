
import os
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import sys
import requests
import urllib3
from requests.auth import HTTPBasicAuth
import geocatConstants as const

root = tk.Tk()  

class loginGUI(tk.Frame):
    """GUI to define somme attribute and the login"""
    def __init__(self, master=root):
        super(loginGUI, self).__init__(master)

        # window
        root.geometry('860x450')  
        root.title('geocat.ch login data')

        # frames
        self.loginFrame = tk.LabelFrame(root, text="Login")
        self.loginFrame.grid(row=0, column=1, padx=5, pady=5, sticky='sw')

        self.buttonFrame = tk.LabelFrame(self.loginFrame)
        self.buttonFrame.grid(row=2, column=1, padx=5, pady=5, sticky='e')

        self.selectFrame = tk.LabelFrame(root, text="Selection")
        self.selectFrame.grid(row=0, column=0, padx=5, pady=5)

        self.rbEditFrame = tk.LabelFrame(self.selectFrame, text="Select Batchediting")
        self.rbEditFrame.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        self.rbEnvFrame = tk.LabelFrame(self.selectFrame, text="Select Environment")
        self.rbEnvFrame.grid(row=0, column=1, padx=5, pady=5, sticky='nw')

        self.rbDataSrcFrame = tk.LabelFrame(self.selectFrame, text="Select Datasource")
        self.rbDataSrcFrame.grid(row=1, column=0, padx=5, pady=5, sticky='nw')

        self.cbSearchArgFrame = tk.LabelFrame(self.selectFrame, text="Select Searcharguments")
        self.cbSearchArgFrame.grid(row=0, column=2, padx=5, pady=5, sticky='nw')

        self.fileDialogFrame = tk.LabelFrame(root, text="Select Input File")
        self.fileDialogFrame.grid(row=1, column=0, padx=5, pady=5, sticky='w')

        #username label and text entry box
        self.usernameLabel = tk.Label(self.loginFrame, text="Benutzername:").grid(row=0, column=0)
        self.username = tk.StringVar()
        self.username.trace_add("write", self.textChanged)
        self.usernameEntry = tk.Entry(self.loginFrame, textvariable=self.username)
        self.usernameEntry.grid(row=0, column=1)
        self.usernameEntry.focus()

        # password label and password entry box
        self.passwordLabel = tk.Label(self.loginFrame, text="Passwort:").grid(row=1, column=0, sticky='w')  
        self.password = tk.StringVar()
        self.password.trace_add("write", self.textChanged)
        self.passwordEntry = tk.Entry(self.loginFrame, textvariable=self.password, show='*')
        self.passwordEntry.grid(row=1, column=1)
        self.passwordEntry.bind("<Return>", self.close)

        # select inputFile label and select inputFile entry box
        self.inputFilenameLabel = tk.Label(self.fileDialogFrame, text="Input Filename").grid(row=0, column=0, padx=5, pady=5, sticky='ne')
        self.inputFilename = tk.StringVar()
        self.inputFilenameEntry = tk.Entry(self.fileDialogFrame, textvariable=self.inputFilename, state='disabled', width=51)
        self.inputFilenameEntry.grid(row=0, column=1, padx=5, pady=5, sticky='ne')

        # cancel button
        self.cancelButton = tk.Button(self.buttonFrame, text="Cancel", command=self.cancel)
        self.cancelButton.grid(row=0, column=0, padx=5, pady=5, sticky='e')

        # login button
        self.loginButton = tk.Button(self.buttonFrame, text="Login", command=self.close)
        self.loginButton.grid(row=0, column=1, padx=5, pady=5, sticky='e')
        self.loginButton["state"] = "disabled"

        # selectFile button
        self.selectFileButton = tk.Button(self.fileDialogFrame, text="...", command=self.selectInputFile)
        self.selectFileButton.grid(row=0, column=2, padx=5, pady=5, sticky='ne')

        # environment - "INT" or "PROD" - depending on where you want to modify your MD
        self.environment = tk.StringVar()
        self.environment.set("INT")
        self._urlPrefix = const.environmentDict[self.environment.get()]
        for env in const.environmentList:
            rbEnvironment = tk.Radiobutton(self.rbEnvFrame, text=env, value=env, variable=self.environment, command=self.rbEnvHandler)
            rbEnvironment.pack(anchor="w")

        # dataSource - "API3" or "BMD" - depending on where you get the information about the techLayerName
        self.dataSource = tk.StringVar()
        self.dataSource.set("API3")
        for dataSource in const.dataSourceList:
            rbDataSource = tk.Radiobutton(self.rbDataSrcFrame, text=dataSource, value=dataSource, variable=self.dataSource, command=self.rbDataSrcHandler)
            rbDataSource.pack(anchor="w")

        # batcheditMode
        self.editMode = tk.StringVar()
        self.editMode.set("ADD")
        self._batchEditMode = const.batchEditModeDict[self.editMode.get()]
        for edit in const.batchEditModeList:
            rbBatchEditMode = tk.Radiobutton(self.rbEditFrame, text=edit, value=edit, variable=self.editMode, command=self.rbEditHandler)
            rbBatchEditMode.pack(anchor="w")

        # keywords
        self.keywordLabel = tk.Label(self.cbSearchArgFrame, text="Keyword:").grid(row=0, column=0, sticky='nw')
        self.keyword = tk.StringVar()
        self.keyword.set(const.keywordsList[0])
        self.keywordCombo = ttk.Combobox(self.cbSearchArgFrame, values=const.keywordsList, textvariable=self.keyword, width=51)
        self.keywordCombo.current(0)
        self.keywordCombo.bind("<Button-1>", self.comboKeywordHandler)
        self.keywordCombo.grid(row=1, column=0, sticky='nw')

        # protocol
        self.protocolLabel = tk.Label(self.cbSearchArgFrame, text="Protocol:").grid(row=3, column=0, sticky='nw')
        self.protocol = tk.StringVar()
        self.protocol.set(const.protocolsList[0])
        self.protocolCombo = ttk.Combobox(self.cbSearchArgFrame, values=const.protocolsList, textvariable=self.protocol, width=30)
        self.protocolCombo.current(0)
        self.protocolCombo.bind("<Button-1>", self.comboProtocolHandler)
        self.protocolCombo.grid(row=4, column=0, sticky='nw')

        # backup
        self.isBackup = tk.BooleanVar()
        self.isBackup.set(True)
        self.backupCheck = tk.Checkbutton(root, text="Backup erforderlich?", var=self.isBackup)
        self.backupCheck.grid(row=1, column=1, sticky='ne')

    def selectInputFile(self):
        _filePath = filedialog.askopenfilename()
        self.inputFilename.set(_filePath)
        pass

    def rbEnvHandler(self):
        self._urlPrefix = const.environmentDict[self.environment.get()]

    def rbDataSrcHandler(self):
        pass

    def rbEditHandler(self):
        self._batchEditMode = const.batchEditModeDict[self.editMode.get()]

    def comboKeywordHandler(self, event):
        if int(event.type) is 4:
            w = event.widget
            w.event_generate('<Down>', when='head')

    def comboProtocolHandler(self, event):
        if int(event.type) is 4:
            w = event.widget
            w.event_generate('<Down>', when='head')

    def close(self, *event):
        if self.checkCredentials():
            root.destroy()
        else:
            self.password.set("")
            self.passwordEntry.focus()

    def cancel(self, *args):
        sys.exit()

    def textChanged(self, *args):
        if self.username.get() and self.password.get():
            self.loginButton["state"] = "normal"
        else:
            self.loginButton["state"] = "disabled"

    def checkCredentials(self, *args):
        self.requestUrl = self.urlPrefix + "ger/q?from=1&to=20"
        self.response = requests.get(self.requestUrl, proxies=const.proxyDict, verify=False, auth=HTTPBasicAuth(self.username.get(), self.password.get()))
        if self.response.status_code == 200:
            return True
        else:
            return False

    def getUrlPrefix(self):
        return self._urlPrefix

    def getBatchEditMode(self):
        return self._batchEditMode

    urlPrefix = property(getUrlPrefix)

    batchEditMode = property(getBatchEditMode)
