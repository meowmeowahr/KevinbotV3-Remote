"""
JSON Syntax Highlighter
By: Kevin Ahr
Based on: https://github.com/art1415926535/PyQt5-syntax-highlighting
"""

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from PyQt5.QtWidgets import QApplication, QPlainTextEdit


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
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages

STYLE_1 = {
    'keyword': color_format([198, 120, 221], 'bold'),
    'brace': color_format([196, 170, 51]),
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

    braces = ['{', '}', '(', ')', '[', ']']
    keywords = ['true', 'false', 'null']

    def __init__(self, document, style=None):
        QSyntaxHighlighter.__init__(self, document)

        if style is None:
            style = STYLE_1

        rules = []

        rules += [(r'\b%s\b' % w, 0, style['keyword'])
                  for w in JsonHighlighter.keywords]
        rules += [(r'%s' % b, 0, style['brace'])
                  for b in JsonHighlighter.braces]

        # All other rules
        rules += [

            # string
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, style['string']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, style['numbers'])
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """ Apply syntax highlighting to the given block of text """
        # Do other syntax formatting
        for expression, nth, fmt in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)


if __name__ == '__main__':
    app = QApplication([])
    editor = QPlainTextEdit()
    editor.setStyleSheet(STYLE_1_QSS)

    highlight = JsonHighlighter(editor.document(), STYLE_1)
    editor.show()

    infile = open('settings.json', 'r')
    editor.setPlainText(infile.read())

    app.exec_()
