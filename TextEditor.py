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
		e.$blockScrolling = Infinity
		e.setTheme("ace/theme/monokai");
		e.getSession().setMode("ace/mode/python");
		e.setValue(editor.content());
		console.log(editor.content())
		e.on('change', function(change){editor.change(e.getValue())});
	</script>
</body>

</html>
"""

EXTENSIONS = ['.py', '.c', '.cpp', '.js', '.txt', '.md', '.rb', '.ruby', '.sh', '.html', '.css', '.php', '.json',
			  '.yaml', '.yml', '.bat']

class Editor(QObject):
	def __init__(self, data, filePath ,parent=None):
		super(Editor,self).__init__(parent)
		self.filePath = filePath
		self.data = data
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
			text = self.data
		self.text = text
		self.filename = filename

	@Slot(result=str)
	def content(self):
		return self.text

	@Slot(str)
	def change(self, text):
		if text != self.data.data:
			self.data.data = text
			self.data.modified = True


class TextEditor(QWebView):
	def __init__(self, data, filename, view, parent):
		super(TextEditor, self).__init__(parent)

		self.filename = filename
		self.data = data
		self.view = view
		self.settings().setAttribute(QWebSettings.WebAttribute.DeveloperExtrasEnabled, True)
		self.status = "Cursor: Line %d, Col %d, Offset 0x%.8x" % (1, 1, self.data.start())

		# Set contents
		self.editor = Editor(self.data, self.filename)
		self.frame = self.page().mainFrame()
		self.frame.addToJavaScriptWindowObject('editor', self.editor)

		self.inspect = QWebInspector()
		self.inspect.setPage(self.page())
		self.setHtml(HTML)

	def eval_js(self, code):
		return self.frame.evaluateJavaScript(code)

	def getText(self):
		return self.eval_js('e.getValue();')

	def closeRequest(self):
		return True

	def get_cursor_pos(self):
		return self.eval_js('e.getCursorPosition();')

	def getPriority(data, filename):
		ext = os.path.splitext(filename)[1].lower()
		if data.read(0, 2) == '#!':
			# Shell script
			return 25
		elif os.path.basename(filename) in ('Makefile', 'README', 'README.txt'):
			return 25
		elif ext in EXTENSIONS:
			return 25
		return 0
	getPriority = staticmethod(getPriority)

	def format_binary_string(self, data):
		return data

	@staticmethod
	def write_to_clipboard(data):
		clipboard = QApplication.clipboard()
		clipboard.clear()
		mime = QMimeData()
		mime.setText(data)
		clipboard.setMimeData(mime)
		return True

	def undo(self):
		self.eval_js('e.undo();')

	def redo(self):
		self.eval_js('e.redo();')

	def selectAll(self):
		self.eval_js("e.selectAll();")

	def selectNone(self):
		self.eval_js("e.navigateFileEnd();")

	def cut(self):
		self.write_to_clipboard(self.eval_js('e.getCopyText();'))
		self.eval_js('e.insert("");')

	def copy(self):
		self.write_to_clipboard(self.eval_js('e.getCopyText();'))

	def paste(self):
		# Get clipboard contents
		clipboard = QApplication.clipboard()
		mime = clipboard.mimeData()
		binary = False
		if mime.hasFormat("application/octet-stream"):
			data = mime.data("application/octet-stream").data()
			binary = True
		elif mime.hasText():
			data = mime.text().encode("utf8")
		else:
			QMessageBox.critical(self, "Error", "Clipboard is empty or does not have valid contents")
			return

		if binary:
			data = self.format_binary_string(data)
		# TODO: Try to make this better somehow
		self.eval_js("e.insert(" + repr(data) + ");")

	def find(self):
		self.eval_js('e.execCommand("find");')

	def getViewName():
		return "Text Editor"
	getViewName = staticmethod(getViewName)


	def getShortViewName():
		return "Text"
	getShortViewName = staticmethod(getShortViewName)

ViewTypes += [TextEditor]
