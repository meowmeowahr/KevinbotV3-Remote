#!/usr/bin/python

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

import os
import sys
import json
import platform

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

# load settings from file
with open("settings.json", "r") as f:
    settings = json.load(f)

# if windows
if platform.system() == "Windows":
    import ctypes

    # show icon in taskbar
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Kevinbot3 Remote")


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.setFixedSize(800, 480)

        # load theme
        with open("theme.qss", 'r') as file:
            self.setStyleSheet(file.read())

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)

        self.setCentralWidget(self.tabs)

        navtb = QToolBar("Navigation")
        navtb.setMovable(False)
        navtb.setIconSize(QSize(24, 24))
        self.addToolBar(navtb)

        back_btn = QAction(QIcon(os.path.join('icons', 'back.svg')), "Back", self)
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        navtb.addAction(back_btn)

        next_btn = QAction(QIcon(os.path.join("icons", "next.svg")), "Forward", self)
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navtb.addAction(next_btn)

        reload_btn = QAction(QIcon(os.path.join('icons', 'refresh.svg')), "Reload", self)
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        navtb.addAction(reload_btn)

        home_btn = QAction(QIcon(os.path.join('icons', 'home.svg')), "Home", self)
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        navtb.addSeparator()

        self.httpsicon = QLabel()
        self.httpsicon.setPixmap(QPixmap(os.path.join('icons', 'lock-nossl.svg')))
        self.httpsicon.setScaledContents(True)
        self.httpsicon.setFixedSize(22, 22)
        navtb.addWidget(self.httpsicon)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.urlbar.setObjectName("Kevinbot3_Remote_UI_URLBar")
        navtb.addWidget(self.urlbar)

        self.close_button = QAction(QIcon(os.path.join('icons', 'window-close.svg')), "Close", self)
        self.close_button.triggered.connect(self.close)
        navtb.addAction(self.close_button)

        try:
            self.add_new_tab(QUrl(settings["homepage"]), "Home")
        except KeyError:
            # settings must and older version
            self.add_new_tab(QUrl('https://www.google.com'), 'Google')

        self.setWindowTitle("Kevinbot Browser")
        self.setWindowIcon(QIcon("icons/browser.svg"))
        self.setObjectName("Kevinbot3_RemoteUI")

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def add_new_tab(self, qurl=None, label="Blank"):

        if qurl is None:
            qurl = QUrl('')

        browser = QWebEngineView()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)

        self.tabs.setCurrentIndex(i)

        # More difficult! We only want to update the url when it's from the
        # correct tab
        browser.urlChanged.connect(lambda qurl, browser=browser:
                                   self.update_urlbar(qurl, browser))

        browser.loadFinished.connect(lambda _, i=i, browser=browser:
                                     self.tabs.setTabText(i, browser.page().title()))

    def tab_open_doubleclick(self, i):
        if i == -1:  # No tab under the click
            self.add_new_tab()

    def current_tab_changed(self, i):
        url = self.tabs.currentWidget().url()
        self.update_urlbar(url, self.tabs.currentWidget())

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            return

        self.tabs.removeTab(i)

    def navigate_home(self):
        self.tabs.currentWidget().setUrl(QUrl("http://www.google.com"))

    def navigate_to_url(self):  # Does not receive the Url
        q = QUrl(self.urlbar.text())
        if q.scheme() == "":
            q.setScheme("http")

        self.tabs.currentWidget().setUrl(q)

    def update_urlbar(self, q, browser=None):

        if browser != self.tabs.currentWidget():
            # If this signal is not from the current tab, ignore
            return

        if q.scheme() == 'https':
            # Secure padlock icon
            self.httpsicon.setPixmap(QPixmap(os.path.join('icons', 'lock-ssl.svg')))

        else:
            # Insecure padlock icon
            self.httpsicon.setPixmap(QPixmap(os.path.join('icons', 'lock-nossl.svg')))

        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot Browser")
    window = MainWindow()
    sys.exit(app.exec_())
