class Profile:
    stt = 0
    email = ""
    emailPass = ""
    fullName = ""
    profile = ""
    proxy = ""
    timeRun = ""

from base.utils import ExcelManager


class ProfileExcel(object):
    def __init__(self) -> None:
        self.listProfile = []

    def getListProfile(self, path: str, sheet: str):
        self.listProfile = []
        listData = ExcelManager.readFileExcel(path, sheet)
        listEmail = listData["Email"]
        listEmailPass = listData["Pass"]
        listFullName = listData["Full name"]
        listProfile = listData["Profile"]
        listProxy = listData["Proxy"]
        listTimeRun = listData["Time Run"]

        for index, item in enumerate(listEmail):
            profile = Profile()
            profile.email = listEmail[index]
            profile.emailPass = listEmailPass[index]
            profile.fullName = listFullName[index]
            profile.profile = listProfile[index]
            profile.proxy = listProxy[index]
            profile.timeRun = listTimeRun[index]
            self.listProfile.append(profile)
        return self.listProfile

    def getListDataExcel(self, path: str, sheet: str):
        listData = ExcelManager.readFileExcel(path, sheet)
        self.listProfile = listData.to_dict('records')
        return self.listProfile
