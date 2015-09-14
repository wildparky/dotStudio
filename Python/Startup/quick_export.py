from PySide import QtGui, QtCore
import os.path
import foundry.ui
import hiero.core
import hiero.exporters
import hiero.ui

class QuickExportAction(QtGui.QAction):
  def __init__(self, presetName, preset=None):
      QtGui.QAction.__init__(self, presetName, None)
      self.exportPreset  = preset
      self.presetName  = presetName
      self.setText(self.presetName)
      self.triggered.connect(self.doit)

  class CustomItemWrapper:
    def __init__ (self, item):
      self._item = item
      
      if isinstance(self._item, hiero.core.BinItem):
        self._item = self._item.activeItem()
    
    def isNull (self):
      return self._item == None

    def binItem (self):
      if isinstance(self._item, hiero.core.BinItem):
        return self._item
      return None      
      
    def sequence (self):
      if isinstance(self._item, hiero.core.Sequence):
        return self._item
      return None

    def clip (self):
      if isinstance(self._item, hiero.core.Clip):
        return self._item
      return None
    
    def trackItem (self):
      if isinstance(self._item, hiero.core.TrackItem):
        return self._item
      return None
    
    def name (self):
      return self._item.name()

  def getInitialFilePath(self, item):
    """Returns an initial opening directory for a project item"""

    if not hasattr(item, 'project'):
      # A project item was not passed in somehow... bail.
      return

    browserPath = None

    projectRoot = item.project().projectRoot()
    if os.path.isdir(projectRoot):
      return projectRoot
    else:
      appSettings = hiero.core.ApplicationSettings()
      browserPath = appSettings.value("FileBrowser/directory")
      if os.path.isdir(browserPath):
        return browserPath

    # Finally just return the Desktop directory
    if not browserPath:
      return os.path.expanduser("~")
      
  def doit(self):
    """This raises a File browser to allow the user to pick an export root"""

    # Prepare list of selected items for export
    selection = [QuickExportAction.CustomItemWrapper(item) for item in hiero.ui.activeView().selection()]

    if len(selection) > 0:
      # Raise the dialog to set the Export Root:

      # Set the default file location to be the project root if it exists, else, look to uistate for last path
      browserPath = self.getInitialFilePath( selection[0] )

      exportRoot = foundry.ui.openFileBrowser(caption="Select Export Root", initialPath=browserPath, mode=2)

      if exportRoot:
        exportRoot = exportRoot[0]

        hiero.core.log.info("Attempting to set the export root to be: " + str(exportRoot))

        properties = self.exportPreset.properties()
        self.exportPreset._properties['exportRoot'] = exportRoot

        hiero.core.log.info("Preset to process is: " + str(self.exportPreset))

        hiero.core.log.info("executing preset: %s with selection %s" % (self.exportPreset, selection))
        hiero.core.taskRegistry.createAndExecuteProcessor(self.exportPreset, selection)

class ExportersMenu:

  def __init__(self):
    self.data = []
    self.registry = hiero.exporters.registry
    self.localPresets = self.registry.localPresets()

    self.rootMenu = QtGui.QMenu("Quick Export")

    self.binProcessorsMenu = QtGui.QMenu("Process as Clips")
    self.timelineProcessorsMenu = QtGui.QMenu("Process as Sequence")
    self.shotProcessorsMenu = QtGui.QMenu("Process as Shots")
    self.rootMenu.addMenu(self.timelineProcessorsMenu)
    self.rootMenu.addMenu(self.binProcessorsMenu)
    self.rootMenu.addMenu(self.shotProcessorsMenu)

    self.populateQuickExportMenus()


  def addActionToMenu(self, action, menu):
    menu.addAction(action)

  def populateQuickExportMenus(self):

    # Get Project presets - To-do update this on Project Load/Close
    projects = hiero.core.projects()
    self.projectPresets = []
    for proj in projects:
      self.projectPresets+=[self.reg.projectPresets(proj)]

    self.presets = self.projectPresets+self.localPresets

    for preset in self.presets:
      act = QuickExportAction(preset.name(), preset)
      hiero.ui.registerAction(act)

      if isinstance(preset,hiero.exporters.FnBinProcessor.BinProcessorPreset):
        self.binProcessorsMenu.addAction(act)
      elif isinstance(preset,hiero.exporters.FnTimelineProcessor.TimelineProcessorPreset):
        self.timelineProcessorsMenu.addAction(act)
      elif isinstance(preset,hiero.exporters.FnShotProcessor.ShotProcessorPreset):
        self.shotProcessorsMenu.addAction(act)

def addExportMenu(event):
  exportersMenu = ExportersMenu()
  fileMenu = hiero.ui.findMenuAction("foundry.menu.file")
  fileMenu.menu().addMenu(exportersMenu.rootMenu)

hiero.core.events.registerInterest('kStartup',addExportMenu)