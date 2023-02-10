""" Geometric Theme """

NAME = "Geometric"

QSS = """#Kevinbot3_RemoteUI {
    background-image: url("res/bg/GeoColors.png");
    background-repeat: no-repeat;
}

#Kevinbot3_RemoteUI_Group {
    color: #000000;
    font-weight: bold;
}


#Kevinbot3_RemoteUI_Button {
    background-color: rgba(51, 51, 72, 100);
    opacity: 127;
    color: #ffffff;
    font-weight: bold;
    font-size: 12px;
    border-radius: 24px;
}

#Kevinbot3_RemoteUI_Button:hover {
    background-color: rgba(51, 51, 72, 150);
    color: #ffffff;
    font-weight: bold;
}

#Kevinbot3_RemoteUI_Button:pressed {
    background-color: rgba(51, 51, 72, 127);
    color: #ffffff;
    font-weight: bold;
}

QToolBar {
    background-color: rgba(51, 51, 72, 100);
    border: 1px solid gray;
    border-radius: 4px;
}

QToolBar QToolButton:hover {
    background-color: rgba(51, 51, 72, 100);
    border: none;
}"""

EFFECTS = "shadow:b15:c555555"
