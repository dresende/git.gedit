import gtk
import os
import subprocess
import gedit

toolbar_ui_str = """<ui>
  <toolbar name="ToolBar">
    <separator/>
    <toolitem name="GitAdd" action="GitAdd"/>
    <toolitem name="GitAddActive" action="GitAddActive"/>
    <toolitem name="GitCommit" action="GitCommit"/>
  </toolbar>
</ui>
"""

class GitGeditWindowHelper:
	def __init__(self, plugin, window):
		#print "Plugin created for", window
		self._window = window
		self._plugin = plugin
		self._insert_toolbar()

	def deactivate(self):
		#print "Plugin stopped for", self._window
		self._remove_toolbar()
		self._window = None
		self._plugin = None
	
	def _insert_toolbar(self):
		manager = self._window.get_ui_manager()
		
		# Create a new action group
		self._action_group = gtk.ActionGroup("GitGeditPluginActions")
		self._action_group.add_actions([("GitAdd", gtk.STOCK_ADD, _("Git Add"), None, _("Add file to staged items"), self._toolbar_git_add)])
		self._action_group.add_actions([("GitAddActive", gtk.STOCK_ADD, _("Git Add Active"), None, _("Add active files to staged items"), self._toolbar_git_add_active)])
		self._action_group.add_actions([("GitCommit", gtk.STOCK_SAVE, _("Git Commit"), None, _("Commit staged items"), self._toolbar_git_commit)])

		# Insert the action group
		manager.insert_action_group(self._action_group, -1)
		
		self._toolbar_ui = manager.add_ui_from_string(toolbar_ui_str)
	
	def _remove_toolbar(self):
		manager = self._window.get_ui_manager()
		manager.remove_ui(self._toolbar_ui)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	def update_ui(self):
		pass
	
	def _toolbar_git_add(self, action):
		document = self._window.get_active_tab().get_document()
		
		self._git_add_file(document.get_uri())

	def _toolbar_git_add_active(self, action):
		documents = self._window.get_documents()
		
		for document in documents:
			self._git_add_file(document.get_uri())

	def _toolbar_git_commit(self, action):
		pass
	
	def _git_add_file(self, path):
		if path == None:
			self._alert("No document is active")
			return

		if path[0:7] != "file://":
			self._alert("For now, the plugin only works with local files")
			return
		subprocess.Popen([ '/usr/bin/git', 'add', path[7:] ])
	
	def _alert(self, message):
		print message

class GitGeditPlugin(gedit.Plugin):
	def __init__(self):
		gedit.Plugin.__init__(self)
		self._instances = {}

	def activate(self, window):
		self._instances[window] = GitGeditWindowHelper(self, window)

	def deactivate(self, window):
		self._instances[window].deactivate()
		del self._instances[window]

	def update_ui(self, window):
		self._instances[window].update_ui()
