import sys
import os
import string
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *
from PySide.QtNetwork import *
from View import *

EXTENSIONS = {'.py':'python', '.c':'clike', '.cpp':'clike', '.js':'javascript', '.txt':'none', '.md':'markdown',
			'.rb':'ruby', '.ruby':'ruby', '.sh':'shell', '.html':'htmlmixed', '.css':'css', '.php':'php'}

class Editor(QObject):
	def __init__(self, data, filePath, parent=None):
		super(Editor, self).__init__(parent)
		self.filename = filePath
		self.data = data

	@Slot(result=str)
	def content(self):
		for c in self.data.data:
			if c not in set(list(string.printable)):
				return ''.join([c if ord(c) else " " for c in self.data.data])
		else:
			return str(self.data.data)

	@Slot(str)
	def change(self, text):
		if text != self.data.data:
			self.data.data = text
			self.data.modified = True

	@Slot(result=str)
	def get_mode(self):
		ext = os.path.splitext(self.filename)[1].lower()
		return EXTENSIONS.get(ext)

	@Slot(result=str)
	def get_font(self):
		if sys.platform == 'darwin':
			font_list = "\"Monaco\", Monospace"
		elif sys.platform.find('linux') != -1:
			font_list = "Monospace"
		elif sys.platform.find('freebsd') != -1:
			font_list = "\"Bitstream Vera Sans Mono\", Monospace"
		else:
			font_list = "\"Consolas\", \"Lucida Console\", Monospace"
		return font_list

class BinjaWebPage(QWebPage):

	def __init__(self, parent=None):
		super(BinjaWebPage, self).__init__(parent)

	def userAgentForUrl(self, url):
		if sys.platform == 'darwin':
			return "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/534.34 (KHTML, like Gecko) Qt/4.8.4 Safari/534.34"
		elif sys.platform.find('linux') != -1:
			return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.34 (KHTML, like Gecko) Qt/4.8.4 Safari/534.34"
		elif sys.platform.find('freebsd') != -1:
			return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.34 (KHTML, like Gecko) Qt/4.8.4 Safari/534.34"
		else:
			return "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/534.34 (KHTML, like Gecko) Qt/4.8.5 Safari/534.34"

class TextEditor(QWebView):
	def __init__(self, data, filename, view, parent):
		super(TextEditor, self).__init__(parent)

		page = BinjaWebPage()
		self.setPage(page)

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

		self.load('codemirror/codemirror.html')

	def set_highlight_type(self, ext):
		mode = EXTENSIONS[ext]
		self.eval_js('set_mode("'+mode+'")')

	def eval_js(self, code):
		return self.frame.evaluateJavaScript(code)

	def getText(self):
		return self.eval_js('e.getValue();')

	def closeRequest(self):
		self.close()
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
		self.eval_js('e.execCommand("undo");')

	def redo(self):
		self.eval_js('e.execCommand("redo");')

	def selectAll(self):
		self.eval_js('e.execCommand("selectAll");')

	def selectNone(self):
		self.eval_js('e.execCommand("undoSelection")')

	def cut(self):
		self.copy()
		self.eval_js('e.replaceSelection("");')

	def copy(self):
		self.write_to_clipboard(self.eval_js('e.getSelection();'))

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
		self.eval_js("e.replaceSelection(" + repr(data) + ");")

	def find(self):
		self.eval_js('e.execCommand("find");')

	def getViewName():
		return "Text Editor"
	getViewName = staticmethod(getViewName)

	def getShortViewName():
		return "Text"
	getShortViewName = staticmethod(getShortViewName)

ViewTypes += [TextEditor]
