"""
JSON Syntax Highlighter
By: Kevin Ahr
Based on: https://github.com/art1415926535/PyQt5-syntax-highlighting
"""

from qtpy.QtCore import QRegularExpression
from qtpy.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from qtpy.QtWidgets import QApplication, QPlainTextEdit


def color_format(color, style=''):
    """
    Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    if type(color) is not str:
        _color.setRgb(color[0], color[1], color[2])
    else:
        _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Weight.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages

STYLE_1 = {
    'keyword': color_format([198, 120, 221], 'bold'),
    'brace': color_format([241, 115, 71]),
    'string': color_format([136, 192, 91]),
    'numbers': color_format([208, 149, 82])
}
STYLE_1_QSS = "QPlainTextEdit{ " \
              "font-family:monospace; " \
              "color: #ccc; " \
              "background-color: #23272e; " \
              "font-size: 13px; }"


class JsonHighlighter(QSyntaxHighlighter):
    """ Syntax highlighter for JSON """

    def __init__(self, document, style=None):
        QSyntaxHighlighter.__init__(self, document)

        if style is None:
            style = STYLE_1

        self.rules = []

        # All other rules
        self.rules += [

            # string
            (r'"[^"\\]*(\\.[^"\\]*)*"', style['string']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', style['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', style['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', style['numbers']),

            # Keywords
            (r'true|false|null', style["keyword"]),
        ]

    def highlightBlock(self, text):
        for rule_pair in self.rules:
            expression = QRegularExpression(rule_pair[0])
            i = expression.globalMatch(text)
            while i.hasNext():
                match = i.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), rule_pair[1])


if __name__ == '__main__':
    app = QApplication([])
    editor = QPlainTextEdit()
    editor.setStyleSheet(STYLE_1_QSS)

    highlight = JsonHighlighter(editor.document(), STYLE_1)
    editor.show()

    infile = open('settings.json', 'r')
    editor.setPlainText(infile.read())

    app.exec()