""" High Contrast Theme """

NAME = "High Contrast"

QSS = """#Kevinbot3_RemoteUI {
    background-image: url("res/bg/HC.png");
    background-repeat: no-repeat;
}

#Kevinbot3_RemoteUI_Group {
    color: #ffffff;
    font-weight: bold;
    border: 12px solid rgba(255, 255, 255, 0);
    margin-top: 10px;
}


#Kevinbot3_RemoteUI_Button {
    border: 1px solid #ffffff;
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    border-radius: 20px;
    font-family: Roboto;
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

EFFECTS = "shadow:b35:c353535"
