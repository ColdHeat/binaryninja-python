import sys
import os
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *
from PySide.QtNetwork import *
from View import *

HTML = """
<!DOCTYPE html>
<html>

<head>
    <style>
        html,
        body {
            margin: 0;
            padding: 0;
            font-family: 'Consolas'
        }

        pre.ace_editor {
            font-family: 'Consolas'
        }

        #editor {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            margin: 0;
        }
    </style>
    <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.1.9/ace.js"></script>
</head>

<body>
    <pre id="editor">

</pre>
    <script type="text/javascript">
        var e = ace.edit("editor");
        e.setTheme("ace/theme/monokai");
        e.getSession().setMode("ace/mode/python");
        e.setValue(editor.content());
        console.log(editor.content())
    </script>
</body>

</html>
"""

class Editor(QObject):
    def __init__(self, filePath ,parent=None):
        super(Editor,self).__init__(parent)
        self.filePath = filePath
        if self.filePath:
            fileInfo = QFileInfo(self.filePath)
            inFile = QFile(self.filePath)
            if inFile.open(QFile.ReadOnly | QFile.Text):
                text = str(inFile.readAll())
                print text
            ab_path = fileInfo.absoluteFilePath()
            filename = fileInfo.fileName()
            print ab_path
        else:
            filename = "New File"
            text = ""
        self.text = text
        self.filename = filename
    @Slot(result=str)
    def content(self):
        return self.text


class TextEditor(QWebView):
    def __init__(self, data, filename, view, parent):
        super(TextEditor, self).__init__(parent)

        self.filename = filename
        self.data = data
        self.view = view
        self.settings().setAttribute(QWebSettings.WebAttribute.DeveloperExtrasEnabled, True)

        # Set contents
        editor = Editor(self.filename)
        frame = self.page().mainFrame()
        frame.addToJavaScriptWindowObject('editor', editor)
        self.inspect = QWebInspector()
        self.inspect.setPage(self.page())
        self.setHtml(HTML)

    def closeRequest(self):
        return True

    def getPriority(data, filename):
        ext = os.path.splitext(filename)[1].lower()
        if data.read(0, 2) == '#!':
            # Shell script
            return 25
        elif os.path.basename(filename) == 'Makefile':
            return 25
        elif ext == '.py':
            return 25
        return 0
    getPriority = staticmethod(getPriority)


    def getViewName():
        return "Text Editor"
    getViewName = staticmethod(getViewName)


    def getShortViewName():
        return "Text"
    getShortViewName = staticmethod(getShortViewName)

ViewTypes += [TextEditor]
