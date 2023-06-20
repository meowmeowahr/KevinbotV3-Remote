# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:/Files/Code/repos/pyqt-colorpicker-main_widget/colorpicker/ui_main.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ColorPicker(object):
    def setupUi(self, ColorPicker):
        ColorPicker.setObjectName("ColorPicker")
        ColorPicker.resize(360, 200)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ColorPicker.sizePolicy().hasHeightForWidth())
        ColorPicker.setSizePolicy(sizePolicy)
        ColorPicker.setMinimumSize(QtCore.QSize(0, 0))
        ColorPicker.setMaximumSize(QtCore.QSize(360, 200))
        ColorPicker.setStyleSheet("QWidget{background-color: none;}\nQLineEdit{background-color:#111114;}")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(ColorPicker)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.color_view = QtWidgets.QFrame(ColorPicker)
        self.color_view.setMinimumSize(QtCore.QSize(200, 200))
        self.color_view.setMaximumSize(QtCore.QSize(5000, 5000))
        self.color_view.setStyleSheet("/* ALL CHANGES HERE WILL BE OVERWRITTEN */;\n"
"background-color: qlineargradient(x1:1, x2:0, stop:0 hsl(0%,100%,50%), stop:1 rgba(255, 255, 255, 255));\n"
"\n"
"")
        self.color_view.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.color_view.setFrameShadow(QtWidgets.QFrame.Raised)
        self.color_view.setObjectName("color_view")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.color_view)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.black_overlay = QtWidgets.QFrame(self.color_view)
        self.black_overlay.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 0, 0, 0), stop:1 rgba(0, 0, 0, 255));\n"
"border-radius: 4px;\n"
"\n"
"")
        self.black_overlay.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.black_overlay.setFrameShadow(QtWidgets.QFrame.Raised)
        self.black_overlay.setObjectName("black_overlay")
        self.selector = QtWidgets.QFrame(self.black_overlay)
        self.selector.setGeometry(QtCore.QRect(-6, 194, 12, 12))
        self.selector.setMinimumSize(QtCore.QSize(12, 12))
        self.selector.setMaximumSize(QtCore.QSize(12, 12))
        self.selector.setStyleSheet("background-color:none;\n"
"border: 1px solid white;\n"
"border-radius: 5px;")
        self.selector.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.selector.setFrameShadow(QtWidgets.QFrame.Raised)
        self.selector.setObjectName("selector")
        self.black_ring = QtWidgets.QLabel(self.selector)
        self.black_ring.setGeometry(QtCore.QRect(1, 1, 10, 10))
        self.black_ring.setMinimumSize(QtCore.QSize(10, 10))
        self.black_ring.setMaximumSize(QtCore.QSize(10, 10))
        self.black_ring.setBaseSize(QtCore.QSize(10, 10))
        self.black_ring.setStyleSheet("background-color: none;\n"
"border: 1px solid black;\n"
"border-radius: 5px;")
        self.black_ring.setText("")
        self.black_ring.setObjectName("black_ring")
        self.verticalLayout_2.addWidget(self.black_overlay)
        self.horizontalLayout_2.addWidget(self.color_view)
        self.hue_frame = QtWidgets.QFrame(ColorPicker)
        self.hue_frame.setMinimumSize(QtCore.QSize(30, 0))
        self.hue_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.hue_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.hue_frame.setObjectName("hue_frame")
        self.hue_bg = QtWidgets.QFrame(self.hue_frame)
        self.hue_bg.setGeometry(QtCore.QRect(10, 0, 20, 200))
        self.hue_bg.setMinimumSize(QtCore.QSize(20, 200))
        self.hue_bg.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(255, 0, 0, 255), stop:0.166 rgba(255, 255, 0, 255), stop:0.333 rgba(0, 255, 0, 255), stop:0.5 rgba(0, 255, 255, 255), stop:0.666 rgba(0, 0, 255, 255), stop:0.833 rgba(255, 0, 255, 255), stop:1 rgba(255, 0, 0, 255));\n"
"border-radius: 5px;")
        self.hue_bg.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.hue_bg.setFrameShadow(QtWidgets.QFrame.Raised)
        self.hue_bg.setObjectName("hue_bg")
        self.hue_selector = QtWidgets.QLabel(self.hue_frame)
        self.hue_selector.setGeometry(QtCore.QRect(7, 185, 26, 15))
        self.hue_selector.setMinimumSize(QtCore.QSize(26, 0))
        self.hue_selector.setStyleSheet("background-color: #ffffff;\n"
"")
        self.hue_selector.setText("")
        self.hue_selector.setObjectName("hue_selector")
        self.hue = QtWidgets.QFrame(self.hue_frame)
        self.hue.setMinimumSize(QtCore.QSize(20, 200))
        self.hue.setStyleSheet("")
        self.hue.setObjectName("hue")
        self.horizontalLayout_2.addWidget(self.hue_frame)
        self.editfields = QtWidgets.QFrame(ColorPicker)
        self.editfields.setMinimumSize(QtCore.QSize(120, 200))
        self.editfields.setMaximumSize(QtCore.QSize(120, 200))
        self.editfields.setStyleSheet("QLabel{\n"
"    font-family: Roboto;\n"
"font-weight: bold;\n"
"    font-size: 11pt;\n"
"    color: #aaaaaa;\n"
"    border-radius: 5px;\n"
"}\n"
"")
        self.editfields.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.editfields.setFrameShadow(QtWidgets.QFrame.Raised)
        self.editfields.setObjectName("editfields")
        self.formLayout = QtWidgets.QFormLayout(self.editfields)
        self.formLayout.setContentsMargins(5, 10, 15, 3)
        self.formLayout.setSpacing(5)
        self.formLayout.setObjectName("formLayout")
        self.color_vis = QtWidgets.QLabel(self.editfields)
        self.color_vis.setMinimumSize(QtCore.QSize(0, 50))
        self.color_vis.setMaximumSize(QtCore.QSize(16777215, 50))
        self.color_vis.setStyleSheet("/* ALL CHANGES HERE WILL BE OVERWRITTEN */;\n"
"background-color: #000;\n"
"")
        self.color_vis.setText("")
        self.color_vis.setObjectName("color_vis")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.color_vis)
        self.lbl_red = QtWidgets.QLabel(self.editfields)
        self.lbl_red.setObjectName("lbl_red")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.lbl_red)
        self.red = QtWidgets.QLineEdit(self.editfields)
        self.red.setAlignment(QtCore.Qt.AlignCenter)
        self.red.setClearButtonEnabled(False)
        self.red.setObjectName("red")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.red)
        self.lbl_green = QtWidgets.QLabel(self.editfields)
        self.lbl_green.setObjectName("lbl_green")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.lbl_green)
        self.green = QtWidgets.QLineEdit(self.editfields)
        self.green.setAlignment(QtCore.Qt.AlignCenter)
        self.green.setObjectName("green")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.green)
        self.lbl_blue = QtWidgets.QLabel(self.editfields)
        self.lbl_blue.setObjectName("lbl_blue")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.lbl_blue)
        self.blue = QtWidgets.QLineEdit(self.editfields)
        self.blue.setAlignment(QtCore.Qt.AlignCenter)
        self.blue.setObjectName("blue")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.blue)
        self.lbl_hex = QtWidgets.QLabel(self.editfields)
        self.lbl_hex.setStyleSheet("font-size: 14pt;")
        self.lbl_hex.setObjectName("lbl_hex")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.lbl_hex)
        self.hex = QtWidgets.QLineEdit(self.editfields)
        self.hex.setAlignment(QtCore.Qt.AlignCenter)
        self.hex.setObjectName("hex")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.hex)
        self.horizontalLayout_2.addWidget(self.editfields)
        self.lbl_red.setBuddy(self.red)
        self.lbl_green.setBuddy(self.green)
        self.lbl_blue.setBuddy(self.blue)
        self.lbl_hex.setBuddy(self.blue)

        self.retranslateUi(ColorPicker)
        QtCore.QMetaObject.connectSlotsByName(ColorPicker)
        ColorPicker.setTabOrder(self.red, self.green)
        ColorPicker.setTabOrder(self.green, self.blue)

    def retranslateUi(self, ColorPicker):
        _translate = QtCore.QCoreApplication.translate
        self.lbl_red.setText(_translate("ColorPicker", "R"))
        self.red.setText(_translate("ColorPicker", "255"))
        self.lbl_green.setText(_translate("ColorPicker", "G"))
        self.green.setText(_translate("ColorPicker", "255"))
        self.lbl_blue.setText(_translate("ColorPicker", "B"))
        self.blue.setText(_translate("ColorPicker", "255"))
        self.lbl_hex.setText(_translate("ColorPicker", "#"))
        self.hex.setText(_translate("ColorPicker", "ffffff"))
