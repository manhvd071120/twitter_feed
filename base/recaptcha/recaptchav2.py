# system libraries
import os
import sys
import urllib

# recaptcha libraries
import pydub
import speech_recognition as sr

# selenium libraries
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# custom patch libraries
from patch import download_latest_chromedriver, webdriver_folder_name
from base.seleniumManager import SeleniumManager
from base.model.ChromeProfile import ChromeProfile
from base.utils import Utils
from base.seleniumManager import SeleniumManager

def delay(waiting_time=5):
    driver.implicitly_wait(waiting_time)


if __name__ == "__main__":
    # main program
    # auto locate recaptcha frames
    chromeProfile = ChromeProfile()
    chromeProfile.chromePath = r"E:\100Captital\GoogleChromePortable64-v85\App\Chrome-bin\chrome.exe"
    chromeProfile.webRtcPath = ""
    chromeProfile.profilePath = "./AllProfiles"
    chromeProfile.ipaddress = ""
    chromeProfile.urlOpen = "https://www.google.com/recaptcha/api2/demo"
    driver = SeleniumManager.createNewChrome(chromeProfile)
    driver.get(chromeProfile.urlOpen)
    frames = SeleniumManager.findElementsByTagName(driver, "iframe")
    recaptcha_control_frame = None
    recaptcha_challenge_frame = None
    for index, frame in enumerate(frames):
        if frame.get_attribute("title") == "reCAPTCHA":
            recaptcha_control_frame = frame
        if frame.get_attribute("title") == "recaptcha challenge":
            recaptcha_challenge_frame = frame
    if not (recaptcha_control_frame and recaptcha_challenge_frame):
        print("[ERR] Unable to find recaptcha. Abort solver.")
        exit()
    # switch to recaptcha frame
    frames = SeleniumManager.findElementsByTagName(driver, "iframe")
    driver.switch_to.frame(recaptcha_control_frame)

    # click on checkbox to activate recaptcha
    btnRecaptcha = SeleniumManager.findElementByClass(driver, "recaptcha-checkbox-border")
    SeleniumManager.clickButton(btnRecaptcha)
    SeleniumManager.Sleep(1)
    # switch to recaptcha audio control frame
    driver.switch_to.default_content()
    frames = SeleniumManager.findElementsByTagName(driver, "iframe")
    driver.switch_to.frame(recaptcha_challenge_frame)

    # click on audio challenge
    SeleniumManager.Sleep(2)
    btnRecaptchaAudio = SeleniumManager.findElementById(driver, "recaptcha-audio-button")
    SeleniumManager.clickButton(btnRecaptchaAudio)

    # switch to recaptcha audio challenge frame
    driver.switch_to.default_content()
    frames = SeleniumManager.findElementsByTagName(driver, "iframe")
    driver.switch_to.frame(recaptcha_challenge_frame)

    # get the mp3 audio file
    src = SeleniumManager.findElementById(driver, "audio-source").get_attribute("src")
    print(f"[INFO] Audio src: {src}")

    path_to_mp3 = os.path.normpath(os.path.join(os.getcwd(), "zapper.mp3"))
    path_to_wav = os.path.normpath(os.path.join(os.getcwd(), "zapper.wav"))

    # download the mp3 audio file from the source
    urllib.request.urlretrieve(src, path_to_mp3)

    # load downloaded mp3 audio file as .wav
    try:
        sound = pydub.AudioSegment.from_mp3(path_to_mp3)
        sound.export(path_to_wav, format="wav")
        sample_audio = sr.AudioFile(path_to_wav)
    except Exception as ex:
        print(ex)
        sys.exit(
            "[ERR] Please run program as administrator or download ffmpeg manually, "
            "https://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/"
        )

    # translate audio to text with google voice recognition
    r = sr.Recognizer()
    with sample_audio as source:
        audio = r.record(source)
    key = r.recognize_google(audio)
    print(f"[INFO] Recaptcha Passcode: {key}")

    # key in results and submit
    driver.find_element_by_id("audio-response").send_keys(key.lower())
    driver.find_element_by_id("audio-response").send_keys(Keys.ENTER)
    driver.switch_to.default_content()
    driver.find_element_by_id("recaptcha-demo-submit").click()


    def openNewChrome(linkWeb, configInfo, wallInfo):
        chromeProfile = ChromeProfile()
        chromeProfile.chromePath = configInfo["chromePath"]
        chromeProfile.webRtcPath = configInfo["extensionPath"]
        chromeProfile.profilePath = configInfo["profilePath"] + wallInfo.get("Profile")
        chromeProfile.ipaddress = ""
        chromeProfile.urlOpen = linkWeb
        chromeDriver = SeleniumManager.createNewChrome(chromeProfile)
        try:
            SeleniumManager.waitLoadFinish(chromeDriver)
            SeleniumManager.waitOpenTab(chromeDriver)
            SeleniumManager.Sleep(2)
            if chromeDriver.title != "MetaMask":
                for chrome_window in chromeDriver.window_handles:
                    chromeDriver.switch_to.window(chrome_window)
                    if chromeDriver.title != 'MetaMask':
                        chromeDriver.close()
            current_window = chromeDriver.current_window_handle
            if chromeDriver.title != "MetaMask":
                for chrome_window in chromeDriver.window_handles:
                    chromeDriver.switch_to.window(chrome_window)
                    if chrome_window != current_window and chromeDriver.title == 'MetaMask':
                        break
            SeleniumManager.Sleep(1)
        except Exception as ex:
            Utils.writeError("Thong tin: " + str(wallInfo.get("Profile")))
            Utils.writeError(str(ex))
            try:
                for handle in chromeDriver.window_handles:
                    chromeDriver.switch_to.window(handle)
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