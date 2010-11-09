import gtk
# perhaps I could use only 1 or 2 instead of the 3 :)
import os
import commands
import subprocess

import gedit

toolbar_ui_str = """<ui>
  <toolbar name="ToolBar">
    <separator/>
    <toolitem name="GitAdd" action="GitAdd"/>
    <toolitem name="GitAddActive" action="GitAddActive"/>
    <toolitem name="GitCommit" action="GitCommit"/>
    <toolitem name="GitPush" action="GitPush"/>
  </toolbar>
</ui>
"""

class GitGeditWindowHelper:
	def __init__(self, plugin, window):
		self._window = window
		self._plugin = plugin
		self.ui_insert()

	def deactivate(self):
		self.ui_remove()
		self._window = None
		self._plugin = None
	
	def _git_commit(self, widget, dialog, path):
		text = dialog.get_widget("commit_text").get_text()
		
		if len(text) == 0:
			return
		
		dialog.get_widget("commit_changes").set_sensitive(False)
		dialog.get_widget("commit_text").set_sensitive(False)
		dialog.get_widget("commit_button").set_sensitive(False)

		os.chdir(os.path.dirname(path))
		
		subprocess.Popen([ "git", "commit", "-m", text ])
		
		dialog.get_widget("commit_window").destroy()
	
	def _git_add_file(self, path):
		if path == None:
			self._alert("No document is active")
			return
		
		subprocess.Popen([ '/usr/bin/git', 'add', self._normalize_path(path) ])
	
	def _normalize_path(self, path):
		if path[0:7] == "file://":
			return path[7:]
		
		return path
	
	# UI STUFF
	def ui_insert(self):
		manager = self._window.get_ui_manager()

		self._action_group = gtk.ActionGroup("GitGeditPluginActions")
		self._action_group.add_actions([("GitAdd", gtk.STOCK_DND, _("Git Add"), None, _("Add file to staged items"), self.ui_toolbar_git_add)])
		self._action_group.add_actions([("GitAddActive", gtk.STOCK_DND_MULTIPLE, _("Git Add Active"), None, _("Add active files to staged items"), self.ui_toolbar_git_add_active)])
		self._action_group.add_actions([("GitCommit", gtk.STOCK_SAVE_AS, _("Git Commit"), None, _("Commit staged items"), self.ui_toolbar_git_commit)])
		self._action_group.add_actions([("GitPush", gtk.STOCK_GO_UP, _("Git Push"), None, _("Push commits from master to origin"), self.ui_toolbar_git_push)])

		manager.insert_action_group(self._action_group, -1)
		
		self._toolbar_ui = manager.add_ui_from_string(toolbar_ui_str)
	
	def ui_remove(self):
		manager = self._window.get_ui_manager()
		manager.remove_ui(self._toolbar_ui)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()
	
	def ui_toolbar_git_add(self, action):
		document = self._window.get_active_tab().get_document()
		
		self._git_add_file(document.get_uri())

	def ui_toolbar_git_add_active(self, action):
		documents = self._window.get_documents()
		
		for document in documents:
			self._git_add_file(document.get_uri())

	def ui_toolbar_git_commit(self, action):
		document = self._window.get_active_tab().get_document()
		
		path = document.get_uri()
		if path == None:
			self._alert("No document is active")
			return
		
		path = self._normalize_path(path)

		dialog = gtk.glade.XML("gitgedit.commit.glade", "commit_window")
		
		treeview = dialog.get_widget("commit_changes")
		
		column = gtk.TreeViewColumn("File", gtk.CellRendererText(), text=0)
		column.set_resizable(True)
		column.set_sort_column_id(0)
		treeview.append_column(column)
		
		changes_list = gtk.ListStore(str)
		treeview.set_model(changes_list)
		
		os.chdir(os.path.dirname(path))
		output = commands.getoutput("git status --porcelain")
		
		for line in output.splitlines():
			if line.startswith("?? "):
				continue
			changes_list.append([ line[3:] ])
		
		dialog.get_widget("commit_button").connect("clicked", self._git_commit, dialog, path)
		dialog.get_widget("commit_window").show()
	
	def ui_toolbar_git_push(self, action):
		pass

	def ui_update(self):
		active_tab = self._window.get_active_tab()
		if active_tab == None:
			self.ui_hide_git()
			return
		
		path = active_tab.get_document().get_uri()
		if path == None:
			self.ui_hide_git()
			return
		
		path = self._normalize_path(path)
		
		os.chdir(os.path.dirname(path))
		
		(status, output) = commands.getstatusoutput("git status")
		
		if status != 0:
			self.ui_hide_git()
			return
		
		self.ui_show_git()
	
	def ui_hide_git(self):
		self._action_group.set_visible(False)
	
	def ui_show_git(self):
		self._action_group.set_visible(True)
	
	# DEBUG STUFF
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
		self._instances[window].ui_update()

