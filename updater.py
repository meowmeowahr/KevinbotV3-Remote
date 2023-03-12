#!/usr/bin/python

# Update program for Kevinbot v3 Remote
# Shows drives mounted in /media/$USER
# Makes a backup of ~/Kbot3Remote/ to ~/Kbot3Remote.bak/
# Lets you pick an update file in the drive (.zip or .tar.gz)
# copies the update file to ~/Kbot3Remote/ (overwrites existing files)
# asks for confirmation to reboot


# Uses PyQt5 for the GUI

from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from QCustomWidgets import KBMainWindow
import qtawesome as qta
from utils import detect_dark, load_theme
import platform
import sys
import json
import os
import datetime
import tarfile
import shutil
import subprocess

EMULATE_REAL_REMOTE = True
FULLSCREEN = False

# windows support
if platform.system() == "Windows":
    import ctypes

    myappid = 'kevinbot.kevinbot.updater._'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

settings = json.load(open("settings.json", "r"))

version = None


class Worker(QObject):
    finished = Signal()
    progress = Signal(int)

    def set_prog(self, prog):
        self.progress.emit(prog)

    def run(self):
        global version
        # make a backup of the current files
        # create a backup directory if it doesn't exist
        if not os.path.exists(settings["backup_dir"].replace("$USER", os.getenv("USER"))):
            os.makedirs(settings["backup_dir"].replace("$USER", os.getenv("USER")))

        self.set_prog(12)

        # make a zip file of the current files
        shutil.make_archive(os.path.join(settings["backup_dir"].replace("$USER", os.getenv("USER")),
                                         "Kevinbot3_Backup_{}".format(datetime.datetime.now()
                                                                      .strftime("%Y-%m-%d_%H-%M-%S"))),
                            "zip", os.path.join(settings["data_dir"].replace("$USER", os.getenv("USER"))))

        self.set_prog(25)

        backups = []

        # if there are more than two backups, delete the oldest one
        if len(os.listdir(settings["backup_dir"].replace("$USER", os.getenv("USER")))) > 2:
            # make a list of the files in the backup directory
            for file in os.listdir(settings["backup_dir"].replace("$USER", os.getenv("USER"))):
                if file.endswith(".zip"):
                    backups.append(file)

        backups.sort()
        backups.reverse()
        backups = backups[2:]

        # remove the files
        for file in backups:
            os.remove(os.path.join(settings["backup_dir"].replace("$USER", os.getenv("USER")), file))

        self.set_prog(37)

        # create a temporary directory in /tmp/Kevinbot3_Temp
        if not os.path.exists("/tmp/Kevinbot3_Temp"):
            os.makedirs("/tmp/Kevinbot3_Temp")

        self.set_prog(50)

        # extract the file to the temporary directory
        with tarfile.open(os.path.join(settings["media_dir"].replace("$USER", os.getenv("USER")),
                                       window.drive_combo.currentText(), window.file_combo.currentText()),
                          "r:gz") as tar:
            tar.extractall(path="/tmp/Kevinbot3_Temp")

        requirements = None
        manifest = None

        # copy the files to the data directory and overwrite any existing files
        for file in os.listdir("/tmp/Kevinbot3_Temp"):
            if os.path.isfile(os.path.join("/tmp/Kevinbot3_Temp", file)):
                # see if the file is settings.json
                if file == "settings.json":
                    # if the dont_copy_settings checkbox is checked, don't copy the file
                    if window.dont_copy_settings.isChecked():
                        continue
                    # if the dont_copy_settings checkbox is not checked, copy the file
                    else:
                        shutil.copy(os.path.join("/tmp/Kevinbot3_Temp", file), os.path.join(settings["data_dir"]
                                                                                            .replace("$USER",
                                                                                                     os.getenv("USER")),
                                                                                            file))

                elif file == "requirements.txt":
                    requirements = os.path.join("/tmp/Kevinbot3_Temp", file)
                elif file == "update_manifest.json":
                    manifest = json.loads(open(os.path.join("/tmp/Kevinbot3_Temp", file), "r").read())
                    version = manifest["version"]

                else:
                    shutil.copy(os.path.join("/tmp/Kevinbot3_Temp", file), os.path.join(settings["data_dir"]
                                                                                        .replace("$USER",
                                                                                                 os.getenv("USER")),
                                                                                        file))

        # copy the folders to the data directory and overwrite any existing files
        for folder in os.listdir("/tmp/Kevinbot3_Temp"):
            if os.path.isdir(os.path.join("/tmp/Kevinbot3_Temp", folder)):
                try:
                    shutil.rmtree(os.path.join(settings["data_dir"].replace("$USER", os.getenv("USER")), folder))
                except FileNotFoundError:
                    pass

                shutil.copytree(os.path.join("/tmp/Kevinbot3_Temp", folder), os.path.join(settings["data_dir"]
                                                                                          .replace("$USER",
                                                                                                   os.getenv("USER")),
                                                                                          folder))
        if manifest:
            for filename in manifest["removed_files"]:
                try:
                    os.remove(os.path.join(settings["data_dir"].replace("$USER", os.getenv("USER")), filename))
                except FileNotFoundError:
                    pass

        self.set_prog(62)

        # Install dependencies
        subprocess.call(["pip", "install", "-r", requirements])

        # remove the temporary directory
        shutil.rmtree("/tmp/Kevinbot3_Temp")

        self.set_prog(75)

        self.set_prog(100)
        print("Update complete!")
        self.finished.emit()


# noinspection PyArgumentList
class MainWindow(KBMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kevinbot Updater")
        self.setObjectName("Kevinbot3_RemoteUI")
        load_theme(self, settings["window_properties"]["theme"])

        if EMULATE_REAL_REMOTE:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setFixedSize(QSize(800, 480))

        self.ensurePolished()
        if detect_dark((QColor(self.palette().color(QPalette.Window)).getRgb()[0],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[1],
                        QColor(self.palette().color(QPalette.Window)).getRgb()[2])):
            self.fg_color = Qt.GlobalColor.white
        else:
            self.fg_color = Qt.GlobalColor.black

        widget = QGroupBox("Kevinbot Updater")
        widget.setObjectName("Kevinbot3_RemoteUI_Group")
        self.setCentralWidget(widget)

        self.layout = QVBoxLayout()
        widget.setLayout(self.layout)

        self.thread_manager = QThreadPool()

        # select a drive label
        self.drive_label = QLabel("Select a drive with an update file:")
        self.drive_label.setObjectName("Kevinbot3_RemoteUI_Label")
        self.drive_label.setFixedHeight(24)
        self.layout.addWidget(self.drive_label)

        self.drive_layout = QHBoxLayout()
        self.layout.addLayout(self.drive_layout)

        # combo box for drive selection
        self.drive_combo = QComboBox()
        self.drive_combo.setObjectName("Kevinbot3_RemoteUI_DriveCombo")
        self.drive_combo.currentIndexChanged.connect(self.refresh_files)
        self.drive_combo.setFixedHeight(36)
        self.drive_layout.addWidget(self.drive_combo)

        # button for drive selection
        self.drive_button = QPushButton("Refresh")
        self.drive_button.setObjectName("Kevinbot3_RemoteUI_DriveButton")
        self.drive_button.clicked.connect(self.refresh_drives)
        self.drive_button.setMaximumWidth(self.drive_button.sizeHint().width())
        self.drive_layout.addWidget(self.drive_button)

        # select a file label
        self.file_label = QLabel("Select an update file:")
        self.file_label.setObjectName("Kevinbot3_RemoteUI_Label")
        self.file_label.setFixedHeight(24)
        self.layout.addWidget(self.file_label)

        self.file_layout = QHBoxLayout()
        self.layout.addLayout(self.file_layout)

        # combo box for file selection
        self.file_combo = QComboBox()
        self.file_combo.setObjectName("Kevinbot3_RemoteUI_FileCombo")
        self.file_combo.setFixedHeight(36)
        self.file_layout.addWidget(self.file_combo)

        # button for file selection
        self.file_button = QPushButton("Refresh")
        self.file_button.setObjectName("Kevinbot3_RemoteUI_FileButton")
        self.file_button.clicked.connect(self.refresh_files)
        self.file_button.setMaximumWidth(self.file_button.sizeHint().width())
        self.file_layout.addWidget(self.file_button)

        # applying updates to ... label
        self.apply_label = QLabel("Applying updates to: {}".format(settings["data_dir"]))
        self.apply_label.setObjectName("Kevinbot3_RemoteUI_Label")
        self.apply_label.setFixedHeight(24)
        self.layout.addWidget(self.apply_label)

        # backing up to ... label
        self.backup_label = QLabel("Backing up to: {}".format(settings["backup_dir"]))
        self.backup_label.setObjectName("Kevinbot3_RemoteUI_Label")
        self.backup_label.setFixedHeight(24)
        self.layout.addWidget(self.backup_label)

        # options grid
        self.options_grid = QGridLayout()
        self.layout.addLayout(self.options_grid)

        # Don't Copy New Settings
        self.dont_copy_settings = QCheckBox("Don't update settings (not recommended)")
        self.dont_copy_settings.setObjectName("Kevinbot3_RemoteUI_CheckBox")
        self.dont_copy_settings.setChecked(False)
        self.options_grid.addWidget(self.dont_copy_settings, 0, 0)

        self.layout.addStretch()

        self.update_layout = QHBoxLayout()
        self.layout.addLayout(self.update_layout)

        # exit button
        self.exit_button = QPushButton()
        self.exit_button.setObjectName("Kevinbot3_RemoteUI_ExitButton")
        self.exit_button.setObjectName("Kevinbot3_RemoteUI_ShutdownButton")
        self.exit_button.setIcon(qta.icon("fa5s.window-close", color=self.fg_color))
        self.exit_button.setIconSize(QSize(32, 32))
        self.exit_button.clicked.connect(self.close)
        self.exit_button.setFixedSize(QSize(36, 36))
        self.update_layout.addWidget(self.exit_button)

        # Update Button
        self.update_button = QPushButton("Update")
        self.update_button.setObjectName("Kevinbot3_RemoteUI_UpdateButton")
        self.update_button.clicked.connect(self.run_update)
        self.update_layout.addWidget(self.update_button)

        self.refresh_drives()
        self.refresh_files()

        if settings["dev_mode"]:
            self.createDevTools()

        if FULLSCREEN:
            self.showFullScreen()
        else:
            self.show()

    def load_theme(self):
        # load theme from settings
        with open("theme.qss") as f:
            self.setStyleSheet(f.read())

    def refresh_drives(self):
        # clear drive combo
        self.drive_combo.clear()

        if not platform.system() == "Windows":
            # get drives
            drives = []
            for drive in os.listdir(settings["media_dir"].replace("$USER", os.getenv("USER"))):
                # if it has files in it
                if os.path.isdir(os.path.join(settings["media_dir"].replace("$USER", os.getenv("USER")), drive)):
                    drives.append(drive)

            # add drives to combo
            for drive in drives:
                self.drive_combo.addItem(drive)
        else:
            self.drive_combo.addItem("Windows is not Supported!")

    def refresh_files(self):
        # clear file combo
        self.file_combo.clear()

        if not platform.system() == "Windows":
            # get files
            files = []
            for file in os.listdir(os.path.join(settings["media_dir"].replace("$USER", os.getenv("USER")),
                                                self.drive_combo.currentText())):
                if file.endswith(".tar.gz"):
                    files.append(file)

            # add files to combo
            for file in files:
                self.file_combo.addItem(file)

            if len(files) == 0:
                self.update_button.setEnabled(False)
            else:
                self.update_button.setEnabled(True)
        else:
            self.drive_combo.addItem("Windows is not Supported!")
            self.update_button.setEnabled(False)

    def run_update(self):
        # noinspection PyAttributeOutsideInit
        self.progress_dialog = QProgressDialog("Updating...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setWindowTitle("Please Wait")
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        # noinspection PyAttributeOutsideInit
        self.upd_thread = QThread()
        # noinspection PyAttributeOutsideInit
        self.upd_worker = Worker()
        self.upd_worker.moveToThread(self.upd_thread)
        # noinspection PyUnresolvedReferences
        self.upd_thread.started.connect(self.upd_worker.run)
        self.upd_worker.finished.connect(self.upd_thread.quit)
        self.upd_worker.finished.connect(self.upd_worker.deleteLater)
        self.upd_worker.finished.connect(self.show_done)
        self.upd_thread.finished.connect(self.upd_thread.deleteLater)
        self.upd_worker.progress.connect(self.progress_dialog.setValue)
        self.upd_thread.start()

    @staticmethod
    def show_done():
        global version
        message = QMessageBox()
        message.setWindowTitle("Update Complete")
        message.setText(f"Successfully Updated to version {version}")
        message.setInformativeText("Please Reboot")
        message.setIcon(QMessageBox.Information)
        message.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot Updater")
    app.setApplicationVersion("1.0")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
