import os
import sys
import threading
import tkinter as tk
import tkinter.messagebox as tkmsg
from modules.seleniumIDEConfig.configController import ConfigController
from modules.guide.guideController import GuideController
from modules.seleniumIDEConfig.configView import ConfigView
from modules.guide.guideView import GuideView
from time import sleep
from base.model.ChromeProfile import ChromeProfile
from base.seleniumManager import SeleniumManager
from base.utils import Utils
from modules.BaseController import BaseController
from modules.seleniumIDE.autoSeleView import AutoSeleView
from modules.seleniumIDEConfig.configModel import ProfileExcel
import urllib.request
import json
import pandas as pd

def getLinkChrome(posProfile, chromePath):
    listSub = os.listdir(chromePath)
    total = len(listSub)
    pos = posProfile % total
    # return chromePath + "/" + listSub[pos] + "/App/Chrome-bin/chrome.exe"
    return chromePath + "/" + listSub[pos] + "/app/brave.exe"

def openNewChrome(configInfo, profileInfo, proxy, numThreads, posThread):
    chromeProfile = ChromeProfile()
    linkChrome = getLinkChrome(int(profileInfo.get('STT')), configInfo["chromePath"])
    chromeProfile.chromePath = linkChrome
    # chromeProfile.chromePath = configInfo["chromePath"]
    chromeProfile.webRtcPath = configInfo["webRtcPath"]
    chromeProfile.profilePath = configInfo["profilePath"] + "/" + profileInfo.get("Profile")
    try:
        infoProxy = profileInfo.get('Proxy').split(':')
        chromeProfile.ipaddress = infoProxy[0] + ':' + infoProxy[1]
    except:
        pass
    chromeDriver = SeleniumManager.createNewChrome(chromeProfile, proxy, numThreads, posThread, configInfo)
    try:
        chromeDriver.switch_to.window(chromeDriver.current_window_handle)
    except Exception as ex:
        Utils.writeError("Thong tin: " + str(profileInfo))
        Utils.writeError(str(ex))
        try:
            chromeDriver.close()
        except:
            Utils.writeError("Error Close chrome")
        finally:
            try:
                chromeDriver.quit()
                return ""
            except:
                Utils.writeError("Error Exit chrome")
    return chromeDriver

def getValueFromKey(keyword, profileInfo, listKeywords):
    key = listKeywords.get(keyword)
    value = profileInfo.get(key)
    return str(value)

def runScript(configInfo, profileInfo, listKeywords, listLock, views, posThread, infoAPI, numThreads):
    isSuccess = True
    listStatusScript = list()
    listScript = Utils.readFileJson(configInfo["scriptPath"])
    if configInfo['modeNetwork'] == '4G':
        countTime = 0
        list4g = infoAPI.strip('\n')
        list4G = list4g.split(':')
        requestResetProxy = urllib.request.urlopen('http://' + list4G[0] + ':10000/reset?proxy=' + infoAPI).read()
        while True:
            if countTime == 300:
                break
            string = str(urllib.request.urlopen('http://' + list4G[0] + ':10000/status?proxy=' + infoAPI).read())
            dic = json.loads(string[string.rfind('{'):string.rfind('}') + 1])
            if dic['status'] == True:
                break
            countTime += 1
    else:
        infoProxy = profileInfo.get('Proxy').split(':')
    listLock.acquire()
    try:
        chromeDriver = openNewChrome(configInfo, profileInfo, infoAPI, numThreads, posThread)
        listChromeDriver.append(chromeDriver)
    except StopIteration:
        return
    finally:
        listLock.release()
    if chromeDriver == "":
        return
    try:
        for scriptInfo in listScript:
            valueSend = scriptInfo["value"]
            scriptResult = {
                "type": scriptInfo["command"],
                "code": scriptInfo["target"],
                "status": True
            }
            if scriptInfo["command"] == "open":
                SeleniumManager.goToWebsite(chromeDriver, scriptInfo["target"])
            elif scriptInfo["command"] == "twitter_feed":
                SeleniumManager.twitter_feed(chromeDriver,configInfo, profileInfo, listLock)
            else:
                element = SeleniumManager.findElementByInfo(chromeDriver, scriptInfo["target"])
                if element != "":
                    if scriptInfo["command"] == "click":
                        SeleniumManager.clickButton(element)
                    elif scriptInfo["command"] == "type":
                        valueInput = getValueFromKey(valueSend, profileInfo, listKeywords)
                        scriptResult["code"] = valueInput
                        SeleniumManager.setValueInput(element, valueInput)
                    elif scriptInfo["command"] == "moveTo":
                        SeleniumManager.moveToElement(chromeDriver, element)
                    else:
                        isSuccess = False
                        Utils.writeError(str(scriptInfo))
                    # Update list script
                    if len(listStatusScript) > views.getMaxLine():
                        listStatusScript.pop(0)
                    listStatusScript.append(scriptResult)
                else:
                    isSuccess = False
            # Update list script
            scriptResult["status"] = isSuccess
            if len(listStatusScript) > views.getMaxLine():
                listStatusScript.pop(0)
            listStatusScript.append(scriptResult)
            if isSuccess:
                pass
            else:
                break
            # End
    except Exception as ex:
        isSuccess = False
        scriptResult = {
            "type": "Exception",
            "code": str(ex),
            "status": False
        }
        if len(listStatusScript) > views.getMaxLine():
            listStatusScript.pop(0)
        listStatusScript.append(scriptResult)
        views.updateListResultStatus(posThread, listStatusScript)
        Utils.writeError(str(ex))
    finally:
        try:
            chromeDriver.close()
        except:
            Utils.writeError("Error Close chrome")
        finally:
            try:
                chromeDriver.quit()
            except:
                Utils.writeError("Error Exit chrome")
            finally:
                return isSuccess

timeRunSucess = []
timeTotalRun = 0
numberOfRuns = 0
listChromeDriver=[]
listNew = []

def checkExcel(profileInfo):
    df = pd.read_excel(profileInfo["proxyPath"], profileInfo["proxySheet"])
    listStauts = df['Status'].to_list()
    for i in listStauts:
        if str(i) == "nan" or str(i) == "" or str(i) == None or str(i) == 'running':
            return False
    return True

class RunSelenium(threading.Thread):
    def __init__(self, configInfo, listProfile, listLock, listKeywords, view, posThread, infoAPI, numThreads):
        threading.Thread.__init__(self)
        self._listKeywords = listKeywords
        self._configInfo = configInfo
        self._listProfile = listProfile
        self._list_lock = listLock
        self._view = view
        self._posThread = posThread
        self._infoAPI = infoAPI
        self._numThreads= numThreads
        self.checkerror = 0
        self.count = 0
        self.countTrue = 0

    def run(self):
        TotalRun = 0
        SuccessRun = 0
        # self._view.setValueForItemScript(self._posThread, "status", "Đang chạy", "green")

        while True:
            global timeTotalRun
            self._list_lock.acquire()
            try:
                while True:
                    profileInfo = next(self._listProfile)
                    if profileInfo.get("Status") == True or profileInfo.get("Status") == 'login' or profileInfo.get("Status") == 'True' or profileInfo.get("Status") == 'susspend':
                        timeRunSucess.append(1)
                        timeTotalRun += 1
                        self._view.resetRunResult(len(timeRunSucess), timeTotalRun, None, None)
                        continue
                    else:
                        break
            except StopIteration:
                return
            finally:
                # release the Lock, so other thread can gain the Lock to access list_num
                self._list_lock.release()
            TotalRun += 1
            # self._view.resetListResultStatus(self._posThread)
            isSuccess = runScript(self._configInfo, profileInfo, self._listKeywords, self._list_lock, self._view,self._posThread, self._infoAPI, self._numThreads)
            if isSuccess:
                SuccessRun += 1
                timeRunSucess.append(1)
            timeTotalRun += 1
            if len(SeleniumManager.ListTwitters) % 10 == 0:
                SeleniumManager.saveListTwtter(self._configInfo, SeleniumManager.ListTwitters)
            self._view.resetRunResult(len(timeRunSucess), timeTotalRun, None, None)
            # self._view.setValueForItemScript(self._posThread, "rate", str(SuccessRun) + "/" + str(TotalRun))


class AutoSeleController(BaseController):
    def __init__(self) -> None:
        self.view = None
        self.isRunning = False
        self.isRunningRetweet = False
        self.entriesConfigValues = None
        self.model = ProfileExcel()
        self.listProfile = iter([])
        self.ListKeywords = {}

    def bind(self, view: AutoSeleView):
        self.view = view
        self.view.initView(None)
        self.view.buttons["runAuto"].configure(command=self.btnRunAuto)
        self.view.buttons["resetExcel"].configure(command=self.btnResetExcel)
        self.view.buttons["killChrome"].configure(command=self.btnKillChrome)
        self.createMenu()

    def createMenu(self):
        root = self.view.getRootView()
        menubar = tk.Menu(root)
        salutations = tk.Menu(menubar, tearoff=False)
        salutations.add_command(label="Hướng dẫn", command=self.btnShowGuide)
        salutations.add_command(label="Cấu hình Auto", command=self.btnConfig)
        salutations.add_separator()
        salutations.add_command(label="Thoát", command=root.destroy)
        menubar.add_cascade(label="File", menu=salutations)
        root.config(menu=menubar)

    def btnConfig(self):
        configController = ConfigController()
        configController.bind(ConfigView(self.view.getRootView()))

    def btnShowGuide(self):
        guideController = GuideController()
        guideController.bind(GuideView(self.view.getRootView()))

    def btnResetExcel(self):
        if self.isRunning:
            tkmsg.showerror(title="Đợi Em Ơi", message=f"Chuong trinh dang chay!")
        else:
            self.confirmReserExcel()

    def confirmReserExcel(self):
        answer = tkmsg.askyesno(title='Question?', message=f"Bạn có chắc muốn reset?")
        if answer:
            self.isRunning = False
            self.ResetExcel()
            tkmsg.showinfo(title="Status", message=f"Reset thanh cong!")

    def btnKillChrome(self):
        if self.isRunning == False:
            tkmsg.showerror(title="Question?", message=f"Chuong trinh chưa chạy kill cái j!")
        else:
            self.confirmKillAllChrome()

    def confirmKillAllChrome(self):
        answer = tkmsg.askyesno(title='Question', message=f"Bạn có chắc muốn Kill all chrome?")
        if answer:
            self.KillAllChrome()
            tkmsg.showinfo(title="Status", message=f"Kill Done!")

    def validateEntries(self):
        isvalid = False
        if self.entriesConfigValues["profilePath"] == "" or self.entriesConfigValues["profilePath"] is None:
            tkmsg.showerror(
                title="Validation Error", message=f"Vui lòng nhập đường dẫn lưu Profile"
            )
        elif self.entriesConfigValues["proxyPath"] == "" or self.entriesConfigValues["proxyPath"] is None:
            tkmsg.showerror(
                title="Validation Error", message=f"Vui lòng nhập đường dẫn file Proxy"
            )
        elif self.entriesConfigValues["webRtcPath"] == "" or self.entriesConfigValues["webRtcPath"] is None:
            tkmsg.showerror(
                title="Validation Error", message=f"Vui lòng nhập đường dẫn thư mục Extension"
            )
        elif self.entriesConfigValues["proxySheet"] == "" or self.entriesConfigValues["proxySheet"] is None:
            tkmsg.showerror(
                title="Validation Error", message=f"Vui lòng nhập tên Sheet"
            )
        elif self.entriesConfigValues["scriptPath"] == "" or self.entriesConfigValues["scriptPath"] is None:
            tkmsg.showerror(
                title="Validation Error", message=f"Vui lòng nhập đường dẫn file Script"
            )
        elif self.entriesConfigValues["maxThread"] is None or int(self.entriesConfigValues["maxThread"]) <= 0:
            tkmsg.showerror(
                title="Validation Error", message=f"Vui lòng nhập số luồng"
            )
        elif self.entriesConfigValues["timeDelay"] is None or int(self.entriesConfigValues["timeDelay"]) <= 0:
            tkmsg.showerror(
                title="Validation Error", message=f"Vui lòng nhập thời gian chờ"
            )
        elif self.entriesConfigValues["file4G"] is None or self.entriesConfigValues["file4G"] == "":
            tkmsg.showerror(
                title="Validation Error", message=f"Vui lòng nhập đường dẫn file 4G!"
            )
        else:
            isvalid = True
        return isvalid

    def btnRunAuto(self):
            if self.isRunning:
                tkmsg.showerror(title="Đợi Em Ơi", message=f"Vui lòng đợi các luồng hoàn thành!")
            else:
                self.isRunning = True
                self.entriesConfigValues = Utils.readFileJson("./config.json")
                if self.validateEntries():
                    self.ListKeywords = Utils.readFileJson(self.entriesConfigValues["keyPath"])
                    self.listProfile = iter(self.model.getListDataExcel(self.entriesConfigValues["proxyPath"], self.entriesConfigValues["proxySheet"]))
                    thread = threading.Thread(target=self.startRunAuto)
                    thread.start()

    def ResetExcel(self):
        self.entriesConfigValues = Utils.readFileJson("./config.json")
        SeleniumManager.ResetFileExcel(self.entriesConfigValues["proxyPath"])

    def KillAllChrome(self):
        for i in listChromeDriver:
            i.quit()
        listChromeDriver.clear()

    def startRunAuto(self):
        # Validate number thread
        numThreads = int(self.entriesConfigValues["maxThread"])
        listLock = threading.Lock()
        threads = []
        if numThreads is None:
            try:
                numThreads = os.cpu_count()
            except AttributeError:
                numThreads = 5

        elif numThreads < 1:
            raise ValueError('num_threads must be > 0')
        # End
        # self.view.createItemScriptRun(numThreads)
        self.view.createItemScriptRun()
        if not self.view.running:
            self.view.labels['stopwatch_label'].after(1000)
            self.view.update()
            self.view.running = True
        # End
        global numberOfRuns
        numberOfRuns += 1
        self.view.resetRunResult(None, None, numberOfRuns, None)
        file4G = open(self.entriesConfigValues['file4G'])
        listAPItxt = file4G.readlines()
        file4G.close()
        # Run multi thread
        for i in range(numThreads):
            thread = RunSelenium(self.entriesConfigValues, self.listProfile, listLock, self.ListKeywords, self.view, i, listAPItxt[i], numThreads)
            threads.append(thread)
            thread.start()
        # End

        # Wait All Thread
        for thread in threads:
            thread.join()
            self.isRunning = False
        # End

        if SeleniumManager.ListTwitters != []:
            SeleniumManager.saveListTwtter(self.entriesConfigValues, SeleniumManager.ListTwitters)
            SeleniumManager.ListTwitters.clear()

        if not checkExcel(self.entriesConfigValues):
            timeRunSucess.clear()
            self.btnRunAuto()
        else:
            self.view.resetRunResult(None, None, None, "Successfully")
            if self.view.running:
                self.view.labels['stopwatch_label'].after_cancel(self.view.update_time)
                self.view.running = False