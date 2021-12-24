import os
import tkinter.messagebox as tkmsg
from modules.BaseController import BaseController
from modules.login.loginView import LoginForm
from modules.seleniumIDE.autoSeleController import AutoSeleController
from modules.seleniumIDE.autoSeleView import AutoSeleView

class LoginController(BaseController):
    def __init__(self) -> None:
        self.view = None

    def bind(self, view: LoginForm):
        self.view = view
        self.view.initView(None)
        self.view.close()
        autoController = AutoSeleController()
        autoController.bind(AutoSeleView(self.view.getRootView()))

