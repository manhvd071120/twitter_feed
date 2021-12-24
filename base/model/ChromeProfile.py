class ChromeProfile:
    chromePath = ""
    profilePath = "profiles"
    webRtcPath = "webrtcleak"
    ipaddress = ""
    posThread = 0
    maxThread = 5
    userAgent = ""
    language = "en"
    locale = "en"
    width = 400
    height = 800
    posX = 0
    posY = 0
    urlOpen = "https://browserleaks.com/ip"

    def __init__(self) -> None:
        super().__init__()

    # def __del__(self):
    #     print('Class Person được hủy')
    #     del self.profilePath, self.ipaddress, self.posThread, self.maxThread, self.userAgent, self.language, self.width, self.height
