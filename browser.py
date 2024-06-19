#!/usr/bin/python

from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import *
from qtpy.QtWebEngineWidgets import *
from QCustomWidgets import KBMainWindow
import qtawesome as qta

import sys
import json
import platform
from utils import load_theme, detect_dark

START_FULL_SCREEN = False
EMULATE_REAL_REMOTE = True

# load settings from file
with open("settings.json", "r") as f:
    settings = json.load(f)

# if windows
if platform.system() == "Windows":
    import ctypes

    # show icon in the taskbar
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Kevinbot3 Remote")


class MainWindow(KBMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.setFixedSize(800, 480)

        try:
            load_theme(
                self,
                settings["window_properties"]["theme"],
                settings["window_properties"]["theme_colors"],
            )
        except NameError:
            load_theme(self, settings["window_properties"]["theme"])

        self.ensurePolished()
        if detect_dark(
            (
                QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                QColor(self.palette().color(QPalette.Window)).getRgb()[1],
                QColor(self.palette().color(QPalette.Window)).getRgb()[2],
            )
        ):
            self.fg_color = Qt.GlobalColor.white
        else:
            self.fg_color = Qt.GlobalColor.black

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

        back_btn = QAction(
            qta.icon("fa5s.chevron-left", color=self.fg_color), "Back", self
        )
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        navtb.addAction(back_btn)

        next_btn = QAction(
            qta.icon("fa5s.chevron-right", color=self.fg_color), "Forward", self
        )
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navtb.addAction(next_btn)

        reload_btn = QAction(qta.icon("fa5s.redo", color=self.fg_color), "Reload", self)
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        navtb.addAction(reload_btn)

        home_btn = QAction(qta.icon("fa5s.home", color=self.fg_color), "Home", self)
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        navtb.addSeparator()

        self.httpsicon = QLabel()
        self.httpsicon.setPixmap(
            qta.icon("fa5s.unlock", color=self.fg_color).pixmap(32, 32)
        )
        self.httpsicon.setScaledContents(True)
        self.httpsicon.setFixedSize(22, 22)
        navtb.addWidget(self.httpsicon)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.urlbar.setObjectName("Kevinbot3_Remote_UI_URLBar")
        navtb.addWidget(self.urlbar)

        self.new_button = QAction(
            qta.icon("fa5s.plus-circle", color=self.fg_color), "Close", self
        )
        self.new_button.triggered.connect(lambda: self.add_new_tab("Blank"))
        navtb.addAction(self.new_button)

        self.close_button = QAction(
            qta.icon("fa5s.window-close", color=self.fg_color), "Close", self
        )
        self.close_button.triggered.connect(self.close)
        navtb.addAction(self.close_button)

        self.add_new_tab()

        self.setWindowTitle("Kevinbot Browser")
        self.setWindowIcon(QIcon("icons/browser.svg"))
        self.setObjectName("Kevinbot3_RemoteUI")

        if settings["dev_mode"]:
            self.createDevTools()

        if START_FULL_SCREEN:
            self.showFullScreen()
        else:
            self.show()

    def add_new_tab(self, label="Blank"):
        try:
            qurl = QUrl(settings["homepage"])
        except KeyError:
            # support for older settings
            qurl = QUrl("https://www.google.com")

        browser = QWebEngineView()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)

        self.tabs.setCurrentIndex(i)

        # More difficult! We only want to update the url when it's from the
        # correct tab
        # noinspection PyUnresolvedReferences
        browser.urlChanged.connect(
            lambda qurl, browser=browser: self.update_urlbar(qurl, browser)
        )

        # noinspection PyUnresolvedReferences
        browser.loadFinished.connect(
            lambda _, i=i, browser=browser: self.tabs.setTabText(
                i, browser.page().title()
            )
        )

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

        if q.scheme() == "https":
            # Secure padlock icon
            self.httpsicon.setPixmap(
                qta.icon("fa5s.lock", color=self.fg_color).pixmap(32, 32)
            )

        else:
            # Insecure padlock icon
            self.httpsicon.setPixmap(
                qta.icon("fa5s.unlock", color=self.fg_color).pixmap(32, 32)
            )

        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot Browser")
    window = MainWindow()
    sys.exit(app.exec_())
