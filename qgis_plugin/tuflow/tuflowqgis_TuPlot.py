
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui
from qgis.core import *
import sys
import os
import csv
import matplotlib
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from matplotlib.patches import Polygon
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
import numpy
import TUFLOW_results2013
import TUFLOW_results2016
import TUFLOW_XS
import math
from collections import OrderedDict

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")
from ui_tuflowqgis_TuPlot import Ui_tuflowqgis_TuPlot


class TuPlot(QDockWidget, Ui_tuflowqgis_TuPlot):
    
	def __init__(self, iface):
        
		QDockWidget.__init__(self)
		self.wdg = Ui_tuflowqgis_TuPlot.__init__(self)
		self.setupUi(self)
		self.iface = iface
		self.canvas = self.iface.mapCanvas()
		self.handler = None
		self.selected_layer = None
		self.IDs = []
		self.res = []
		self.idx = -1 #initial
		self.showIt()		
		self.cLayer = None
		self.GeomType = None
		self.connected = False
		self.ts_types_P = []
		self.ts_types_L = []
		self.ts_types_P = []
		self.ax2_exists = True
		self.dockOpened = True
		self.is_xs = False
		self.XS=TUFLOW_XS.XS()
		self.geom_type = None
		#self.setAttribute(Qt.WA_DeleteOnClose, True)
		
		#colour stuff
		self.qred = QtGui.QColor(int(255), int(0), int(0))
		self.qgrey = QtGui.QColor(int(192), int(192), int(192))
		self.qblue = QtGui.QColor(int(0), int(0), int(255))
		self.qgreen = QtGui.QColor(int(0), int(153), int(0))
		self.qblack = QtGui.QColor(int(0), int(0), int(0))
		
		self.qgis_connect()
		QObject.connect(self.cbDeactivate, SIGNAL("stateChanged(int)"), self.deactivate_changed) #this is seperate so multiple connections aren't created
		
	def __del__(self):
		# Disconnect signals and slots
		self.qgis_disconnect()
		#QMessageBox.information(self.iface.mainWindow(), "DEBUG", "__del__")
		#opened = False
    
	def closeEvent(self,event):
		#self.saveSettings()
		#QDialog.closeEvent(self,event)
		#QMessageBox.information(self.iface.mainWindow(), "DEBUG", "closeEvent")
		self.dockOpened = False
		self.__del__()
		
	def qgis_connect(self): #2015-04-AA
		if not self.connected:
			self.lwStatus.insertItem(0,'Creating QGIS connections')
			self.lwStatus.item(0).setTextColor(self.qgreen)
			QObject.connect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer *)"), self.layerChanged)
			QObject.connect(self.locationDrop, SIGNAL("currentIndexChanged(int)"), self.loc_changed)       
			QObject.connect(self.ResTypeList, SIGNAL("currentRowChanged(int)"), self.res_type_changed) 
			QObject.connect(self.AddRes, SIGNAL("clicked()"), self.add_res)
			QObject.connect(self.pbAddRes_GIS, SIGNAL("clicked()"), self.add_res_gis)
			QObject.connect(self.CloseRes, SIGNAL("clicked()"), self.close_res)
			QObject.connect(self.pbAnimateLP, SIGNAL("clicked()"), self.animate_LP)
			QObject.connect(self, SIGNAL("visibilityChanged(bool)"), self.visChanged)
			QObject.connect(self.listTime, SIGNAL("currentRowChanged(int)"), self.timeChanged) 
			QObject.connect(self.pbClearStatus, SIGNAL("clicked()"), self.clear_status)
			QObject.connect(self.pbUpdate, SIGNAL("clicked()"), self.update_pressed)
			QObject.connect(self.pbHelp, SIGNAL("clicked()"), self.help_pressed)
			QObject.connect(self.cbForceXS, SIGNAL("stateChanged(int)"), self.changed_forcexs)
			QObject.connect(self.cbForceRes, SIGNAL("stateChanged(int)"), self.changed_forceres)
			#QMessageBox.information(self.iface.mainWindow(), "DEBUG", "connecting")
			#QObject.connect(self, SIGNAL( "destroyed(PyQt_PyObject)" ), self.closeup)
			#try:
			#	QObject.connect(self, SIGNAL( "closeEvent(QCloseEvent)" ), self.closeup)
			#except:
			#	QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Cant connect to closeEvent'")
			#QMessageBox.information(self.iface.mainWindow(), "DEBUG", "connected?")
			#QObject.connect(exitButton,SIGNAL("clicked()"),self.closeup)
			self.lwStatus.insertItem(0,'Connections created.')
			self.lwStatus.item(0).setTextColor(self.qgreen)
			self.connected = True
	
	def qgis_disconnect(self): #2015-04-AA
		if self.connected:
			self.lwStatus.insertItem(0,'Removing QGIS connections')
			self.lwStatus.item(0).setTextColor(self.qgreen)
			QObject.disconnect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer *)"), self.layerChanged)
			QObject.disconnect(self.locationDrop, SIGNAL("currentIndexChanged(int)"), self.loc_changed)       
			QObject.disconnect(self.ResTypeList, SIGNAL("currentRowChanged(int)"), self.res_type_changed) 
			QObject.disconnect(self.AddRes, SIGNAL("clicked()"), self.add_res)
			QObject.disconnect(self.pbAddRes_GIS, SIGNAL("clicked()"), self.add_res_gis)
			QObject.disconnect(self.CloseRes, SIGNAL("clicked()"), self.close_res)
			QObject.disconnect(self.pbAnimateLP, SIGNAL("clicked()"), self.animate_LP)
			QObject.disconnect(self, SIGNAL("visibilityChanged(bool)"), self.visChanged)
			QObject.disconnect(self.listTime, SIGNAL("currentRowChanged(int)"), self.timeChanged) 
			QObject.disconnect(self.pbClearStatus, SIGNAL("clicked()"), self.clear_status)
			QObject.disconnect(self.pbUpdate, SIGNAL("clicked()"), self.update_pressed)
			QObject.disconnect(self.cbForceXS, SIGNAL("stateChanged(int)"), self.changed_forcexs)
			QObject.disconnect(self.cbForceRes, SIGNAL("stateChanged(int)"), self.changed_forceres)
			#QObject.disconnect(self.cbDeactivate, SIGNAL("stateChanged(int)"), self.deactivate_changed)
			self.lwStatus.insertItem(0,'Disconnected.')
			self.lwStatus.item(0).setTextColor(self.qgreen)
		self.connected = False
	
	def help_pressed(self):
		message = 'This TuPlot utility is designed to view timeseries and long profile data from TUFLOW models.\n'
		message = message+'For some functionality, this utitlity relies on the new output formats available in the 2016 version of TUFLOW.  Some of the functioanlity is available for the 2013 version of TUFLOW.\n'
		message = message+'For more information on using this please see http://wiki.tuflow.com/index.php?title=TuPlot'
		QMessageBox.information(self.iface.mainWindow(), "TuPlot Information", message)
	def clear_status(self):
		"""
			Clears the status list wdiget
		"""
		self.lwStatus.clear()
		self.lwStatus.insertItem(0,'Status cleared')
		self.lwStatus.item(0).setTextColor(self.qgreen)
		
	def visChanged(self, vis):
		#QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Vis is " + str(vis))
		#if vis:
		#	QMessageBox.information(self.iface.mainWindow(), "DEBUG", "Vis true")
		if not vis:
			#QMessageBox.information(self.iface.mainWindow(), "Information", "Dock visibility turned off - deactivating dock.")
			#self.deactivate()
			
			#QMessageBox.information(self.iface.mainWindow(), "Information", "Exiting")
			#self.lwStatus.insertItem(0,'Visibility Changed')
			#self.qgis_disconnect()
			return
		#else:
		#	self.qgis_connect()


	def deactivate_changed(self):
		"""
			Deactivate checkbox has changed status
		"""
		
		if (self.cbDeactivate.isChecked()):
			self.lwStatus.insertItem(0,'Viewer deactivated')
			self.lwStatus.item(0).setTextColor(self.qgreen)
			self.qgis_disconnect()
		else:
			self.lwStatus.insertItem(0,'Viewer re-activated')
			self.lwStatus.item(0).setTextColor(self.qgreen)

			self.qgis_connect()
			if self.cLayer:
				self.layerChanged()
				
	def refresh(self):
		"""
			Refresh is usually called when the selected layer changes in the legend
			Refresh clears and repopulates the dock widgets, restoring them to their correct values
		"""
		#self.lwStatus.insertItem(0,'Refreshing')
		self.cLayer = self.canvas.currentLayer()
		self.select_changed()

	def closeup(self):
		"""
			Close up and remove the dock
		"""
		QMessageBox.information(self.iface.mainWindow(), "Information", "Closing and removing dock")
		
	
	def changed_forcexs(self):
		"""
			The Check button Force XS has been changed
		"""
		if self.cbForceXS.isChecked():
			if self.cbForceRes.isChecked(): # force res already checked
				self.cbForceRes.setChecked(False)

	def changed_forceres(self):
		"""
			The Check button Force RES has been changed
		"""
		if self.cbForceRes.isChecked():
			if self.cbForceXS.isChecked():  # force xs already checked
				self.cbForceXS.setChecked(False)
				
	def add_res(self):
		"""
			Add results file
		"""
		# Retrieve the last place we looked if stored
		settings = QSettings()
		lastFolder = str(settings.value("TUFLOW_Res_Dock/lastFolder", os.sep))
		if (len(lastFolder)>0): # use last folder if stored
			fpath = lastFolder
		else:
			cLayer = self.canvas.currentLayer()
			if cLayer: # if layer selected use the path to this
				dp = cLayer.dataProvider()
				ds = dp.dataSourceUri()
				fpath = os.path.dirname(unicode(ds))
			else: # final resort to current working directory
				fpath = os.getcwd()
		# Get the file name
		inFileName = QFileDialog.getOpenFileName(self.iface.mainWindow(), 'Open TUFLOW results file', fpath, "TUFLOW 1D Results (*.info *.tpc)")
		inFileName = str(inFileName)
		if len(inFileName) == 0: # If the length is 0 the user pressed cancel 
			return
		# Store the path we just looked in
		#head, tail = os.path.split(inFileName)
		fpath, fname = os.path.split(inFileName)
		if fpath <> os.sep and fpath.lower() <> 'c:\\' and fpath <> '':
			settings.setValue("TUFLOW_Res_Dock/lastFolder", fpath)
		self.lwStatus.insertItem(0,'Opening File: '+fname)
		self.lwStatus.item(0).setTextColor(self.qgreen)
		root, ext = os.path.splitext(inFileName)
		if ext.upper()=='.INFO':
			self.lwStatus.insertItem(0,'.INFO file detected - using TUFLOW_Results2013.')
			self.lwStatus.item(0).setTextColor(self.qgreen)
			#self.lwStatus.insertItem(0,'Loading...')
			try:
				res=TUFLOW_results2013.ResData(inFileName)
				self.res.append(res)
				#self.lwStatus.insertItem(0,'Done')
			except:
				self.lwStatus.insertItem(0,'ERROR - Loading Results')
				self.lwStatus.item(0).setTextColor(self.qred)
			
		elif ext.upper()=='.TPC':
			self.lwStatus.insertItem(0,'.TPC file detected - using TUFLOW_results2016')
			self.lwStatus.item(0).setTextColor(self.qgreen)
			try:
				#self.lwStatus.insertItem(0,'Loading...')
				res=TUFLOW_results2016.ResData()
				error, message = res.Load(inFileName)
				if error:
					self.lwStatus.insertItem(0,message)
				else:
					self.res.append(res)
					#self.lwStatus.insertItem(0,'Done')
			except:
				self.lwStatus.insertItem(0,'ERROR - Loading Results')
				self.lwStatus.item(0).setTextColor(self.qred)
		
		#QMessageBox.information(self.iface.mainWindow(), "Opened", "Successfully Opened - "+myres.displayname)
		
		self.update_reslist()

	def add_res_gis(self):
		"""
			Add results file and loads the GIS layers into the project
		"""
		# Retrieve the last place we looked if stored
		settings = QSettings()
		lastFolder = str(settings.value("TUFLOW_Res_Dock/lastFolder", os.sep))
		if (len(lastFolder)>0): # use last folder if stored
			fpath = lastFolder
		else:
			cLayer = self.canvas.currentLayer()
			if cLayer: # if layer selected use the path to this
				dp = cLayer.dataProvider()
				ds = dp.dataSourceUri()
				fpath = os.path.dirname(unicode(ds))
			else: # final resort to current working directory
				fpath = os.getcwd()
		# Get the file name
		inFileName = QFileDialog.getOpenFileName(self.iface.mainWindow(), 'Open TUFLOW results file (must be 2015 or newer)', fpath, "TUFLOW Results (*.tpc)")
		inFileName = str(inFileName)
		if len(inFileName) == 0: # If the length is 0 the user pressed cancel 
			return
		# Store the path we just looked in
		fpath, fname = os.path.split(inFileName)
		if fpath <> os.sep and fpath.lower() <> 'c:\\' and fpath <> '':
			settings.setValue("TUFLOW_Res_Dock/lastFolder", fpath)
		#self.lwStatus.insertItem(0,'Opening File: '+fname)
		root, ext = os.path.splitext(inFileName)
		if ext.upper()=='.INFO':
			self.lwStatus.insertItem(0,'ERROR - .INFO file detected must be 2015 or newer TUFLOW')
			self.lwStatus.item(0).setTextColor(self.qgreen)
			#self.lwStatus.insertItem(0,'Not loading.')
			
		elif ext.upper()=='.TPC':
			self.lwStatus.insertItem(0,'.TPC file detected - using TUFLOW_results2016')
			self.lwStatus.item(0).setTextColor(self.qgreen)
			try:
				#self.lwStatus.insertItem(0,'Loading...')
				res=TUFLOW_results2016.ResData()
				error, message = res.Load(inFileName)
				if error:
					self.lwStatus.insertItem(0,message)
				self.res.append(res)
				#self.lwStatus.insertItem(0,'Done')
			except:
				self.lwStatus.insertItem(0,'ERROR - Loading Results')
				self.lwStatus.item(0).setTextColor(self.qred)
		
		self.update_reslist()
		
		#loaad the GIS layers
		if res.GIS.P:
			fullfile = os.path.join(fpath,res.GIS.P)
			try:
				self.iface.addVectorLayer(fullfile, os.path.basename(fullfile), "ogr")
			except:
				self.lwStatus.insertItem(0,'Failed to load GIS layer')
				self.lwStatus.item(0).setTextColor(self.qblue)
		if res.GIS.L:
			fullfile = os.path.join(fpath,res.GIS.L)
			try:
				self.iface.addVectorLayer(fullfile, os.path.basename(fullfile), "ogr")
			except:
				self.lwStatus.insertItem(0,'Failed to load GIS layer')
				self.lwStatus.item(0).setTextColor(self.qblue)
		if res.GIS.R:
			fullfile = os.path.join(fpath,res.GIS.R)
			try:
				self.iface.addVectorLayer(fullfile, os.path.basename(fullfile), "ogr")
			except:
				self.lwStatus.insertItem(0,'Failed to load GIS layer')
				self.lwStatus.item(0).setTextColor(self.qblue)
		if res.GIS.RL_P:
			#self.lwStatus.insertItem(0,'Loading GIS RL point layer:')
			fullfile = os.path.join(fpath,res.GIS.RL_P)
			#self.lwStatus.insertItem(0,'Debug - fullfile: '+fullfile)
			try:
				self.iface.addVectorLayer(fullfile, os.path.basename(fullfile), "ogr")
			except:
				self.lwStatus.insertItem(0,'Failed to load GIS layer')
		if res.GIS.RL_L:
			#self.lwStatus.insertItem(0,'Loading GIS RL line layer:')
			fullfile = os.path.join(fpath,res.GIS.RL_L)
			try:
				self.iface.addVectorLayer(fullfile, os.path.basename(fullfile), "ogr")
			except:
				self.lwStatus.insertItem(0,'Failed to load GIS layer')
				self.lwStatus.item(0).setTextColor(self.qblue)

	def update_reslist(self):
		#self.lwStatus.insertItem(0,'Updating results list')
		self.ResList.clear()
		for res in self.res:
			self.ResList.addItem(res.displayname)
			
		#set the items as selected:
		for x in range(0, self.ResList.count()):
			list_item = self.ResList.item(x)
			self.ResList.setItemSelected(list_item, True)

		#also update the types of results that are available
		self.ts_types_P = []
		self.ts_types_L = []
		self.ts_types_R = []
		tmp_list = []
		for res in self.res:
			for restype in res.Types:
				#self.lwStatus.insertItem(0,'debug: res: '+res.displayname+', type: '+restype)
				restype = restype.replace('1D ','')
				restype = restype.replace('2D ','')
				if restype.upper() == 'LINE FLOW':
					restype = 'Flows' #don't differentiate between 1D and 2D flows
				if restype.upper() == 'POINT WATER LEVEL':
					restype = 'Water Levels' #don't differentiate between 1D and 2D water levels
				tmp_list.append(restype)
			
			if res.Channels: #bug fix which would not load results with no 1D
				if res.Channels.nChan>0: #
					tmp_list.append('US Levels')
					tmp_list.append('DS Levels')
		
		#get unique
		unique_res = list(OrderedDict.fromkeys(tmp_list))
		for restype in unique_res:
			#self.lwStatus.insertItem(0,'Debug: '+restype)
			if restype.upper() in ('WATER LEVELS'):
				self.ts_types_P.append('Level')
			elif restype.upper() in ('ENERGY LEVELS'):
				self.ts_types_P.append('Energy Level')
			elif restype.upper() in ('POINT VELOCITY'):
				self.ts_types_P.append('Velocity')
			elif restype.upper() in ('POINT X-VEL'):
				self.ts_types_P.append('VX')
			elif restype.upper() in ('POINT Y-VEL'):
				self.ts_types_P.append('VY')
			elif restype.upper() in ('FLOWS'):
				self.ts_types_L.append('Flows')
			elif restype.upper() in ('VELOCITIES'):
				self.ts_types_L.append('Velocities')
			elif restype.upper() in ('LINE FLOW AREA'):
				self.ts_types_L.append('Flow Area')
			elif restype.upper() in ('LINE INTEGRAL FLOW'):
				self.ts_types_L.append('Flow Integral')
			elif restype.upper() in ('US LEVELS'):
				self.ts_types_L.append('US Levels')
			elif restype.upper() in ('DS LEVELS'):
				self.ts_types_L.append('DS Levels')
			elif restype.upper() in ('DS LEVELS'):
				self.ts_types_L.append('DS Levels')
			elif restype.upper() in ('LINE STRUCTURE FLOW'):
				self.ts_types_L.append('Structure Flows')
			elif restype.upper() in ('STRUCTURE LEVELS'):
				self.ts_types_L.append('Structure Levels')
			else:
				self.lwStatus.insertItem(0,'ERROR unhandled type: '+restype)
				self.lwStatus.item(0).setTextColor(self.qred)

	def close_res(self):
		"""
			Close results file
		"""
		for x in range(0, self.ResList.count()):
			list_item = self.ResList.item(x)
			if list_item.isSelected():
				res = self.res[x]
				self.res.remove(res)
				self.update_reslist()

	def layerChanged(self):
		self.geom_type = None #store geometry type for later use
		if self.cbForceXS.isChecked():
			xs_format = True
		elif self.cbForceRes.isChecked():
			xs_format = False
		else: #determine if xs or results
			#self.lwStatus.insertItem(0,'Checking vector geometry')
			self.cLayer = self.canvas.currentLayer()
			if self.cLayer and (self.cLayer.type() == QgsMapLayer.VectorLayer):
				valid = False
				dp = self.cLayer.dataProvider()
				GType = dp.geometryType()
				if (GType == QGis.WKBPoint):
					self.geom_type = 'P'
					valid = True
				if (GType == QGis.WKBLineString):
					self.geom_type = 'L'
					valid = True
				elif (GType == QGis.WKBPolygon):
					self.geom_type = 'R'
					message = "Not expecting polygon data"
				else:
					message = "Expecting points or lines for 1d_tab format"
			else:
				valid = False
				message = "Invalid layer or no layer selected"
				self.lwStatus.insertItem(0,'Message: '+message)
			
			xs_format = False
			if valid: # geometry is valid, check for correct attributes
				xs_format = True
				if (dp.fieldNameIndex('Source') != 0):
					xs_format = False
					#self.lwStatus.insertItem(0,'First field is not named "Source" Field')
				if (dp.fieldNameIndex('Type') != 1):
					xs_format = False
					#self.lwStatus.insertItem(0,'Second field is not named "Type" Field')
				if (dp.fieldNameIndex('Flags') != 2):
					xs_format = False
					#self.lwStatus.insertItem(0,'Third field is not named "Flags" Field')
			else:
				#QMessageBox.information(self.iface.mainWindow(), "1D XS Viewer", "Message: "+message)
				self.lwStatus.insertItem(0,'Message: '+message)
		
		if xs_format: # need to get sections
			self.is_xs = True
			self.lwStatus.insertItem(0,'The layer appears to be a 1d_tab layer.')
			self.lwStatus.item(0).setTextColor(self.qgreen)
			self.locationDrop.clear()
			self.IDs = []
			self.IDList.clear()
			self.locationDrop.addItem("Tabular Data (Section)")
			
		else: #it might be a result file
			self.is_xs = False
			self.locationDrop.clear()
			if len(self.res)==0:
				self.locationDrop.addItem('No Results Open / Not a TUFLOW layer')
				self.lwStatus.item(0).setTextColor(self.qblue)
				return
			self.cLayer = self.canvas.currentLayer()
			#self.sourcelayer.clear()
			self.locationDrop.clear()
			self.IDs = []
			self.IDList.clear()
			
			#determine latest version (if multiple results selected)
			version = 1
			for i in range(len(self.res)):
				#self.lwStatus.insertItem(0,'Results file '+str(i+1)+' has version: '+str(self.res[i].formatVersion))
				version = max(version,self.res[i].formatVersion)
				self.res_version = version
							
			if self.res_version>2:
				self.lwStatus.insertItem(0,'ERROR - Unxpected results version, expecting 1 or 2.')
				self.lwStatus.item(0).setTextColor(self.qred)
				self.qgis_disconnect()
					
			if self.cLayer and (self.cLayer.type() == QgsMapLayer.VectorLayer):
				GType = self.cLayer.dataProvider().geometryType()
				if (GType == QGis.WKBPoint):
					self.GeomType = "Point"
					if self.res_version == 1:
						self.locationDrop.addItem("Timeseries") #this triggers loc_changed which populates data fields
					elif self.res_version == 2:
						if (self.cLayer.name().find('_PLOT_')>-1):
							self.locationDrop.addItem("Timeseries") #this triggers loc_changed which populates data fields
						else:
							self.lwStatus.insertItem(0,'ERROR - Not a TUFLOW Layer Selected')
							self.lwStatus.item(0).setTextColor(self.qblue)
							self.locationDrop.addItem("Not a TUFLOW Layer Selected")
				elif (GType == QGis.WKBLineString):
					self.GeomType = "Line"
					if self.res_version == 1:
						self.locationDrop.addItem("Timeseries")
						self.locationDrop.addItem("Long Profile")				
					elif self.res_version == 2:
						if (self.cLayer.name().find('_PLOT_')>-1):
							self.locationDrop.addItem("Timeseries")
							self.locationDrop.addItem("Long Profile")
						else:
							self.lwStatus.insertItem(0,'ERROR - Not a TUFLOW Layer Selected')
							self.lwStatus.item(0).setTextColor(self.qblue)
							self.locationDrop.addItem("Not a TUFLOW Layer Selected")
				else:
					self.GeomType = None
					self.clear_figure()
				self.locationDrop.setCurrentIndex(0)
				
				#index to ID
				self.idx = self.cLayer.fieldNameIndex('ID')
				if (self.idx < 0):
					self.locationDrop.clear()
					self.locationDrop.addItem("Not a TUFLOW Layer Selected")
				

			else:
				self.locationDrop.addItem("Not a TUFLOW Layer Selected")
				self.clear_figure()
				
		if self.handler:
			QObject.disconnect(self.selected_layer, SIGNAL("selectionChanged()"),self.select_changed)
			self.handler = False
			self.selected_layer = None
		if self.cLayer is not None:
			if self.cLayer.isValid():
				QObject.connect(self.cLayer,SIGNAL("selectionChanged()"),self.select_changed)
				self.selected_layer = self.cLayer
		self.refresh()
		
	def select_changed(self):
		self.IDList.clear()
		available_types = []
		error = False 
		if self.is_xs: #dealing with tabular / section data
			if self.cLayer:
				dp = self.cLayer.dataProvider()
				ds = dp.dataSourceUri()
				fpath = os.path.dirname(unicode(ds))
				fields = self.cLayer.pendingFields()
				nselect = len(self.cLayer.selectedFeatures())
				if nselect<1:
					#self.lwStatus.insertItem(0,'No sections selected')
					error = True
				try:
					#self.lwStatus.insertItem(0,'clearing sections')
					self.XS.clear()
				except:
					self.lwStatus.insertItem(0,'problem clearing sections')
					return
					
				try:
					for feature in self.cLayer.selectedFeatures():
						#self.lwStatus.insertItem(0,'loading section')
						error, message = self.XS.addfromfeature(fpath, fields, feature)
						if error:
							self.lwStatus.insertItem(0,'ERROR - problem loading section: '+message)
						#else:
						#	self.lwStatus.insertItem(0,'np = '+str(self.XS.data[-1].np))
				except:
					self.lwStatus.insertItem(0,'broken  feaature in selected')
					error = True
				# poputalte results type list
				try:
					self.ResTypeList.clear()
					for xs_type in self.XS.all_types:
						self.ResTypeList.addItem(xs_type)
				except:
					self.lwStatus.insertItem(0,'Error updating results list')
					
				# populate the selected elements
				self.IDList.clear()
				try:
					for xs in self.XS.data:
						self.IDList.addItem(xs.source)
				except:
					self.lwStatus.insertItem(0,'Error updating xs source list')
		else: #dealing with results
			if len(self.res) == 0:
				self.lwStatus.insertItem(0,'No Results Open')
				self.lwStatus.item(0).setTextColor(self.qblue)
				return
			#self.lwStatus.insertItem(0,'Selection Changed')
			self.IDs = []
			self.Doms = []
			self.Source_Att = []
			self.IDList.clear()
			#self.lwStatus.insertItem(0,'Debug - GeomType: '+self.geom_type)
			if self.res_version == 1:
				#self.lwStatus.insertItem(0,'Debug - version 1')
				if self.idx >= 0:
					if self.cLayer:
						try:
							for feature in self.cLayer.selectedFeatures():
								try:
									fieldvalue=feature['ID']
									self.IDs.append(fieldvalue.strip())
									self.IDList.addItem(fieldvalue.strip())
								except:
									warning = True #suppress the warning below, most likely due to a "X" type channel or blank name
									
						except:
							error = True
			elif self.res_version == 2:
				if self.idx >= 0:
					if self.cLayer:
						try:
							for feature in self.cLayer.selectedFeatures():
								try: # get ID data
									fieldvalue=feature['ID']
									self.IDs.append(fieldvalue.strip())
									self.IDList.addItem(fieldvalue.strip())
								except:
									warning = True #suppress the warning below, most likely due to a "X" type channel or blank name
								try: # get Type (1D, 2D or RL)
									fieldvalue=feature['Type']
									dom = fieldvalue.strip().upper()
									if (dom.find('NODE') >= 0):
										dom = '1D'
									elif (dom.find('CHAN') >= 0):
										dom = '1D'
									self.Doms.append(dom)
									type_str = dom+'|'
								except:
									self.lwStatus.insertItem(0,'ERROR - Processing "Type" attribute '+str(fieldvalue))
									error = True
								try: # get Source
									fieldvalue=feature['Source']
									Source_Att = fieldvalue.strip().upper()
									
									if dom == 'RL': # ignore source attribute for RL as this contains information on the 
										if self.geom_type == 'P':
											Source_Att = 'H'
										elif self.geom_type == 'L':
											Source_Att = 'Q'
									self.Source_Att.append(Source_Att)
									type_str = type_str+Source_Att
									
									if available_types.count(type_str)<1:
										available_types.append(type_str)
									
								except:
									error = True
						except:
							error = True
			
			if self.locationDrop.currentText() == "Long Profile":
				for res in self.res:
					res.LP.connected = False
					res.LP.static = False
					if (len(self.IDs)==0):
						error = True
						message = 'No features selected - skipping'
					elif (len(self.IDs)==1):
						if self.res_version == 1: #2013 version only supports 1D
							self.Doms.append('1D')
						if self.Doms[0]=='1D':
							error, message = res.LP_getConnectivity(self.IDs[0],None)
						else:
							error = True
							message = 'Selected object is not 1D channel - type: '+self.Doms[0]
					elif (len(self.IDs)==2):
						if self.res_version == 1: #2013 version only supports 1D
							self.Doms.append('1D')
							self.Doms.append('1D')
						if self.Doms[0]=='1D' and self.Doms[1]=='1D':
							error, message = res.LP_getConnectivity(self.IDs[0],self.IDs[1])
						else:
							error = True
							message = 'Selected objects are not 1D channels - types: '+self.Doms[0]+' and '+self.Doms[0]
					else:
						self.lwStatus.insertItem(0,'WARNING - More than 2 objects selected.  Using only 2.')
						self.lwStatus.item(0).setTextColor(self.qblue)
						error, message = res.LP_getConnectivity(self.IDs[0],self.IDs[1])
					if error:
						self.lwStatus.insertItem(0,message)
						self.lwStatus.insertItem(0,'ERROR - Getting LP connectivity')
						self.lwStatus.item(0).setTextColor(self.qred)
					else:
						error, message = res.LP_getStaticData()
						if error:
							self.lwStatus.insertItem(0,message)
						if res.formatVersion > 1:
							if res.LP.adverseH.nLocs > 0 or res.LP.adverseE.nLocs > 0:
								self.lwStatus.insertItem(0,'WARNING - Adverse gradients detected along profile')
								self.lwStatus.item(0).setTextColor(self.qred)
		
		if ((not self.is_xs) and (self.locationDrop.currentText() == "Timeseries")):
			#grey out the types that are not in the current selection
			#self.lwStatus.insertItem(0,'Debug shading restypes')

			cleaned_types = []
			for type_str in available_types:
				dom, type = type_str.split('|')
				if dom == '2D':
					if type.find('QI')>=0:
						type.replace('QI','')
						if cleaned_types.count('Flow Integral')<1:
							cleaned_types.append('Flow Integral')
					if type.find('QA')>=0:
						type.replace('QA','')
						if cleaned_types.count('Flow Area')<1:
							cleaned_types.append('Flow Area')
					if type.find('QS')>=0:
						type.replace('QS','')
						if cleaned_types.count('Structure Flows')<1:
							cleaned_types.append('Structure Flows')
					if type.find('HU')>=0:
						type.replace('HU','')
						if cleaned_types.count('Structure Levels')<1:
							cleaned_types.append('Structure Levels')
					if type.find('HD')>=0:
						type.replace('HD','')
						if cleaned_types.count('Structure Levels')<1:
							cleaned_types.append('Structure Levels')
					if type.find('Q')>=0:
						type.replace('Q','')
						if cleaned_types.count('Flows')<1:
							cleaned_types.append('Flows')
				elif dom == 'RL':
					if self.geom_type=='P':
						if cleaned_types.count('Level')<1:
							cleaned_types.append('Level')
					elif self.geom_type=='L':
						if cleaned_types.count('Flows')<1:
							cleaned_types.append('Flows')
				elif dom == '1D':
					if self.geom_type=='P':
						if type.find('H')>=0:
							type.replace('H','')
							if cleaned_types.count('Level')<1:
								cleaned_types.append('Level')
					elif self.geom_type=='L':
						if type.find('Q_')>=0:
							type.replace('Q_','')
							if cleaned_types.count('Flows')<1:
								cleaned_types.append('Flows')
						if type.find('V_')>=0:
							type.replace('V_','')
							if cleaned_types.count('Velocities')<1:
								cleaned_types.append('Velocities')
						if cleaned_types.count('Flow Area')<1: #'QA' not coming through to GIS
							cleaned_types.append('Flow Area')
			#loop through all entries and colour as appropriate
			for x in range(0,self.ResTypeList.count()):
				list_item = self.ResTypeList.item(x)
				type_str = list_item.text()
				if cleaned_types.count(type_str) > 0:
					self.ResTypeList.item(x).setTextColor(self.qblack)
				else:
					self.ResTypeList.item(x).setTextColor(self.qgrey)
			
		if not error:
			self.start_draw()
	def timeChanged(self):
		self.start_draw()
	def res_type_changed(self):
		self.lwStatus.insertItem(0,'Result type changed - use Update Plot to Update')
		self.lwStatus.item(0).setTextColor(self.qgrey)

	def update_pressed(self):
		self.start_draw()
		
	def loc_changed(self):
		loc = self.locationDrop.currentText()
		self.ResTypeList.clear()
		self.ResTypeList_ax2.clear()
		if (loc == "Timeseries"):
			self.listTime.clear()
			if (self.GeomType == "Point"):
				for restype in self.ts_types_P:
					self.ResTypeList.addItem(restype)
					self.ResTypeList_ax2.addItem(restype)
			elif (self.GeomType == "Line"):
				for restype in self.ts_types_L:
					self.ResTypeList.addItem(restype)
					self.ResTypeList_ax2.addItem(restype)
			else:
				self.lwStatus.insertItem(0,'ERROR should not be here loc_changed_ts_A')
				self.lwStatus.item(0).setTextColor(self.qblue)
		elif (loc == "Long Profile"):
			self.ResTypeList.clear()
			self.ResTypeList.addItem("Max Water Level")
			self.ResTypeList.addItem("Max Energy Level")
			self.ResTypeList.addItem("Water Level at Time")
			self.ResTypeList.addItem("Energy Level at Time")
			self.ResTypeList.addItem("Bed Level")
			self.ResTypeList.addItem("Left Bank Obvert")
			self.ResTypeList.addItem("Right Bank Obvert")
			self.ResTypeList.addItem("Pit Ground Levels (if any)")
			self.ResTypeList.addItem("Adverse Gradients (if any)")
			self.ResTypeList_ax2.addItem("Time Hmax")
			
			# add times
			try:
				times = self.res[0].times
				self.listTime.clear()
				for time in times:
					self.listTime.addItem("%.4f" % time)
				item = self.listTime.item(0)
				self.listTime.setItemSelected(item, True)
			except:
				self.lwStatus.insertItem(0,'WARNING - Unable to populate times, check results loaded.')
				self.lwStatus.item(0).setTextColor(self.qblue)
		else:
			self.ResTypeList.clear()
		item = self.ResTypeList.item(0) # select 1st item by default
		self.ResTypeList.setItemSelected(item, True)
		self.start_draw()

	def animate_LP(self):
		start = True
		
		# check if long profile type is selected
		loc = self.locationDrop.currentText()
		if (loc!="Long Profile"): # LP
			self.lwStatus.insertItem(0,'ERROR - Please choose Long Profile type before animating.')
			self.lwStatus.item(0).setTextColor(self.qblue)
			start = False
			return
		
		# check for valid selection
		if len (self.IDs) == 0:
			self.lwStatus.insertItem(0,'ERROR - No elements selected.')
			start = False
			return
		elif len (self.IDs) > 2:
			self.lwStatus.insertItem(0,"ERROR - More than 2 ID's selected.")
			start = False
			return
		
		# Compile of output types (bed level, max wse)
		restype = []
		for x in range(0, self.ResTypeList.count()):
			list_item = self.ResTypeList.item(x)
			if list_item.isSelected():
				restype.append(list_item.text())
		if restype.count('Water Level at Time')==0:
			self.lwStatus.insertItem(0,"ERROR - Water level at time not selected!")
			start = False
			return
		
		# results:
		ResIndexs = []
		if self.ResList.count() == 0:
			self.lwStatus.insertItem(0,'ERROR - No results open...')
			start = False
			return
		else:
			for x in range(0, self.ResList.count()):
				list_item = self.ResList.item(x)
				if list_item.isSelected():
					ResIndexs.append(x)
		# times
		if self.listTime.count() == 0:
			self.lwStatus.insertItem(0,'ERROR - No output times detected.')
			start = False
			return
		
		nWidth = 5
		if self.listTime.count() < 11:
			nWidth = 1
		elif self.listTime.count() < 101:
			nWidth = 2
		elif self.listTime.count() < 1001:
			nWidth = 3
		elif self.listTime.count() < 10001:
			nWidth = 4
		if start:
			try:
				QMessageBox.information(self.iface.mainWindow(), "Information", "Saving images to: "+self.res[0].fpath+"\nAfter selecting ok, please wait while the images are created.\nYou will be notified when this has finished.")
				
				for x in range(0, self.listTime.count()):
					item = self.listTime.item(x)
					self.listTime.setItemSelected(item, True)
					self.draw_figure()
					filenum = str(x+1)
					filenum = filenum.zfill(nWidth)
					fname = 'QGIS_LP_'+filenum+'.pdf'
					fullpath = os.path.join(self.res[0].fpath,fname)
					self.plotWdg.figure.savefig(fullpath)
					self.listTime.setItemSelected(item, False)
				QMessageBox.information(self.iface.mainWindow(), "Information", "Processing Complete")
			except:
				QMessageBox.critical(self.iface.mainWindow(), "ERROR", "An error occurred processing long profile")
			
	def start_draw(self):
		self.clear_figure()
		if self.is_xs: #dealing with tabular / section data
			if self.XS.nXS>0:
				draw = True
			else:
				draw = False
		else:
			loc = self.locationDrop.currentText()
			type = []
			
			# Compile of output types
			#self.lwStatus.insertItem(0,'Current Items are : ', self.ResTypeList.selectedItems())
			items = self.ResTypeList.selectedItems()
			for x in range(0, self.ResTypeList.count()):
				list_item = self.ResTypeList.item(x)
				if list_item.isSelected():
					type.append(list_item.text())
			draw = True
			if len(type) == 0:
				draw = False
			if len (self.IDs) == 0:
				draw = False
		
		if (draw):
			#self.lwStatus.insertItem(0,'call draw_figure()')
			self.draw_figure()
	def showIt(self):
		self.layout = self.frame_for_plot.layout()
		minsize = self.minimumSize()
		maxsize = self.maximumSize()
		self.setMinimumSize(minsize)
		self.setMaximumSize(maxsize)

		self.iface.mapCanvas().setRenderFlag(True)
		
		self.artists = []
		labels = []
		
		self.fig = Figure( (1.0, 1.0), linewidth=0.0, subplotpars = matplotlib.figure.SubplotParams(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0, hspace=0))
			
		font = {'family' : 'arial', 'weight' : 'normal', 'size'   : 12}
		
		rect = self.fig.patch
		rect.set_facecolor((0.9,0.9,0.9))
		self.subplot = self.fig.add_axes((0.10, 0.15, 0.85,0.82))
		self.subplot.set_xbound(0,1000)
		self.subplot.set_ybound(0,1000)			
		self.manageMatplotlibAxe(self.subplot)
		canvas = FigureCanvasQTAgg(self.fig)
		sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		canvas.setSizePolicy(sizePolicy)
		self.plotWdg = canvas
		
		self.gridLayout.addWidget(self.plotWdg)
		if matplotlib.__version__ < 1.5 :
			mpltoolbar = matplotlib.backends.backend_qt4agg.NavigationToolbar2QTAgg(self.plotWdg, self.frame_for_toolbar)
		else:
			mpltoolbar = matplotlib.backends.backend_qt4agg.NavigationToolbar2QT(self.plotWdg, self.frame_for_toolbar)
		lstActions = mpltoolbar.actions()
		mpltoolbar.removeAction( lstActions[ 7 ] ) #remove customise subplot
			
		#create curve
		label = "test"
		x=numpy.linspace(-numpy.pi, numpy.pi, 201)
		y=numpy.sin(x)
		a, = self.subplot.plot(x, y)
		self.artists.append(a)
		labels.append(label)
		self.subplot.hold(True)
		self.plotWdg.draw()
	
	def manageMatplotlibAxe(self, axe1):
		axe1.grid()
		axe1.tick_params(axis = "both", which = "major", direction= "out", length=10, width=1, bottom = True, top = False, left = True, right = False)
		axe1.minorticks_on()
		axe1.tick_params(axis = "both", which = "minor", direction= "out", length=5, width=1, bottom = True, top = False, left = True, right = False)
	
	def clear_figure(self):
		self.subplot.cla() #clear axis
		try:
			self.axis2.cla()
		except:
			self.ax2_exists = False

	def draw_figure(self):
		self.clear_figure()
		
		#dual axis stuff
		if (self.cb2ndAxis.isChecked() or self.cbXSRoughness.isChecked()): # if not checked not dual axis needed
			self.lwStatus.insertItem(0,'dual axis needed')
			if self.ax2_exists == False:
				self.axis2 = self.subplot.twinx()
				self.ax2_exists = True
		else:
			if self.ax2_exists:
				try:
					self.fig.delaxes(self.axis2)
					self.ax2_exists = False
				except:
					QMessageBox.critical(self.iface.mainWindow(), "ERROR", "Error deleting axis2\n Please contact support@tuflow.com")
		self.artists = []
		labels = []
		
		#ititialise limits
		xmin = 999999.
		xmax = -999999.
		ymin = 999999.
		ymax = -999999.
		mmin = 0
		mmax = 1
		
		
		
		if self.is_xs: # drawing section
			for xs in self.XS.data:
				xmin=round(min(xs.x), 0) - 1
				xmax=round(max(xs.x), 0) + 1
				ymin=round(min(xs.z), 0) - 1
				ymax=round(max(xs.z), 0) + 1
				label = xs.source+" - "+xs.type
				self.subplot.set_xbound(lower=xmin, upper=xmax)
				self.subplot.set_ybound(lower=ymin, upper=ymax)
				a, = self.subplot.plot(xs.x, xs.z)
				self.artists.append(a)
				labels.append(label)
				self.subplot.hold(True)
				try:
					if self.ax2_exists:
						self.axis2.set_xbound(lower=xmin, upper=xmax)
					if self.cbXSRoughness.isChecked() and xs.has_mat:
						if (len(xs.x)==len(xs.mat)):
							a2, = self.axis2.plot(xs.x, xs.mat, '--')
							self.artists.append(a2)
							mmin=round(min(xs.mat), 0) - 1
							mmax=round(max(xs.mat), 0) + 1
							self.axis2.set_ybound(lower=mmin, upper=mmax)
							self.axis2.set_ylabel('Material or Roughness')
				except:
					self.lwStatus.insertItem(0,'Issues adding roughness to plot')
			# set axis labels (routine in TUFLOW_XS)
			try:
				error, msg, x_title, y_title = self.XS.set_axis_titles(self.res[0].units)
			except: # res not loaded units not know
				error, msg, x_title, y_title = self.XS.set_axis_titles(None)
			self.subplot.set_xlabel(x_title)
			self.subplot.set_ylabel(y_title)
			
			if self.cbShowLegend.isChecked():
				self.subplot.legend(self.artists, labels, bbox_to_anchor=(0, 0, 1, 1))
			self.subplot.hold(False)
			self.subplot.grid(True)
			self.plotWdg.draw()
		
		else: #results
			#self.lwStatus.insertItem(0,'drawing results')
			loc = self.locationDrop.currentText()
			ydataids = self.IDs
			typeids = []
			typenames = []
			for x in range(0,self.ResTypeList.count()):
				list_item = self.ResTypeList.item(x)
				if list_item.isSelected():
					typeids.append(x)
					typenames.append(list_item.text())
			
			typenames2 = []
			for x in range(0,self.ResTypeList_ax2.count()):
				list_item = self.ResTypeList_ax2.item(x)
				if list_item.isSelected():
					#typeids.append(x)
					typenames2.append(list_item.text())

			# Compile Selected Results Files
			reslist = []
			resnames = []
			for x in range(0, self.ResList.count()):
				list_item = self.ResList.item(x)
				if list_item.isSelected():
					reslist.append(x)
					resnames.append(list_item.text())
			nRes = len(reslist)
			#self.lwStatus.insertItem(0,'nRes = '+str(nRes))
			
			
			for resno in reslist:
				res = self.res[resno]
				name = res.displayname
				#Long Profiles___________________________________________________________________
				if (loc=="Long Profile"): # LP
					plot = True
					
					# if LP data has been processed (should both always be True)
					if res.LP.connected and res.LP.static:
						#update limits
						xmin = 0.0 # should always start at 0
						tmp_xmax=max(res.LP.dist_nodes)
						xmax = max(xmax,tmp_xmax)
						tmp_ymin=min(res.LP.node_bed)
						ymin = min(ymin, tmp_ymin)
						#tmp_ymax=max(res.LP.Hmax)
						#tmp_ymax2=max(res.LP.Emax)
						#ymax = max(ymax,tmp_ymax,tmp_ymax2)
						
						
						# plot max water level
						if typenames.count('Max Water Level')<>0:
							a, = self.subplot.plot(res.LP.dist_nodes, res.LP.Hmax)
							self.artists.append(a)
							label = 'Max Water Level'
							if nRes > 1:
								labels.append(label +" - "+name)
							else:
								labels.append(label)
							self.subplot.hold(True)
							ymax = max(ymax,max(res.LP.Hmax))

						# plot max energy level
						if typenames.count('Max Energy Level')<>0:
							if res.formatVersion == 1:
								self.lwStatus.insertItem(0,'Energy output only available in 2015 or newer results')
							else:
								if res.LP.Emax:
									a, = self.subplot.plot(res.LP.dist_nodes, res.LP.Emax)
									self.artists.append(a)
									label = 'Max Energy Level'
									if nRes > 1:
										labels.append(label +" - "+name)
									else:
										labels.append(label)
									self.subplot.hold(True)
									ymax = max(ymax,max(res.LP.Emax))
								else:
									self.lwStatus.insertItem(0,'Warning - No Maximum Energy Levels stored for '+name)

						#plot bed
						if typenames.count('Bed Level')<>0:
							a, = self.subplot.plot(res.LP.dist_chan_inverts, res.LP.chan_inv)
							self.artists.append(a)
							label = 'Bed Level'
							if nRes > 1:
								labels.append(label +" - "+name)
							else:
								labels.append(label)
							self.subplot.hold(True)
							ymax = max(ymax,max(res.LP.chan_inv))
							
							#tag on culverts if bed is shown (2015 or later)
							if res.formatVersion >= 2: #2015
								for verts in res.LP.culv_verts:
									if verts:
										poly = Polygon(verts, facecolor='0.9', edgecolor='0.5')
										self.subplot.add_patch(poly)


						#plot LB
						if typenames.count('Left Bank Obvert')<>0:
							a, = self.subplot.plot(res.LP.dist_chan_inverts, res.LP.chan_LB)
							self.artists.append(a)
							label = 'Left Bank'
							if nRes > 1:
								labels.append(label +" - "+name)
							else:
								labels.append(label)
							self.subplot.hold(True)
							ymax = max(ymax,max(res.LP.chan_LB))

						#plot RB
						if typenames.count('Right Bank Obvert')<>0:
							a, = self.subplot.plot(res.LP.dist_chan_inverts, res.LP.chan_RB)
							self.artists.append(a)
							label = 'Right Bank'
							if nRes > 1:
								labels.append(label +" - "+name)
							else:
								labels.append(label)
							self.subplot.hold(True)
							ymax = max(ymax,max(res.LP.chan_RB))
							
						#plot LP water level at time
						if typenames.count('Water Level at Time')<>0:
							for x in range(0, self.listTime.count()):
								list_item = self.listTime.item(x)
								if list_item.isSelected():
									timeInd = x
									timeStr = list_item.text()
									time = res.times[x]
									#self.lwStatus.insertItem(0,'timeStr = '+timeStr)
							error, message = res.LP_getData('Head',time,0.01)
							if error:
								self.lwStatus.insertItem(0,'ERROR - Extracting temporal data for LP')
								self.lwStatus.insertItem(0,message)
							else:
								a, = self.subplot.plot(res.LP.dist_nodes, res.LP.Hdata)
								self.artists.append(a)
								label = 'Water Level at '+timeStr
								if nRes > 1:
									labels.append(label +" - "+name)
								else:
									labels.append(label)
								self.subplot.hold(True)
								ymax = max(ymax,max(res.LP.Hdata))

						#plot LP energy at time
						if typenames.count('Energy Level at Time')<>0:
							if res.formatVersion == 1:
								self.lwStatus.insertItem(0,'Energy output only available in 2015 or newer results')
							else:
								for x in range(0, self.listTime.count()):
									list_item = self.listTime.item(x)
									if list_item.isSelected():
										timeInd = x
										timeStr = list_item.text()
										time = res.times[x]
										#self.lwStatus.insertItem(0,'timeStr = '+timeStr)
								error, message = res.LP_getData('Energy',time,0.01)
								if error:
									self.lwStatus.insertItem(0,'ERROR - Extracting temporal data for LP')
									self.lwStatus.insertItem(0,message)
								else:
									a, = self.subplot.plot(res.LP.dist_nodes, res.LP.Edata)
									self.artists.append(a)
									label = 'Energy Level at '+timeStr
									if nRes > 1:
										labels.append(label +" - "+name)
									else:
										labels.append(label)
									self.subplot.hold(True)
									ymax = max(ymax,max(res.LP.Edata))

						#plot pits
						if typenames.count('Pit Ground Levels (if any)')<>0:
							if res.LP.npits > 0:
								a, = self.subplot.plot(res.LP.pit_dist, res.LP.pit_z, marker='o', linestyle='None', color='r')
								self.artists.append(a)
								labels.append("Pit Invert (grate) levels")
							else:
								self.lwStatus.insertItem(0,'No Pit objects to plot')
						

						#plot adverse sections
						if typenames.count('Adverse Gradients (if any)')<>0:
							if res.formatVersion == 1:
								self.lwStatus.insertItem(0,'Adverse gradient plots not available Pre-2016')
							else:
								if res.LP.adverseH.nLocs > 0:
									a, = self.subplot.plot(res.LP.adverseH.chainage, res.LP.adverseH.elevation, marker='o', linestyle='None', color='r')
									self.artists.append(a)
									labels.append("Adverse Water Level")
									#self.lwStatus.insertItem(0,'WARNING - Adverse gradients detected along profile')
									if self.cbShowLegend.isChecked():
										for i in range(res.LP.adverseH.nLocs):
											self.subplot.text(res.LP.adverseH.chainage[i],res.LP.adverseH.elevation[i]+0.25,res.LP.adverseH.node[i],rotation=90,verticalalignment='bottom',fontsize=12)
									else:
										self.lwStatus.insertItem(0,'Turn on legend to get more information about adverse grades')
								if res.LP.adverseE.nLocs > 0:
									a, = self.subplot.plot(res.LP.adverseE.chainage, res.LP.adverseE.elevation, marker='o', linestyle='None', color='y')
									self.artists.append(a)
									labels.append("Adverse Energy Level")
									#self.lwStatus.insertItem(0,'WARNING - Adverse gradients detected along profile')
									if self.cbShowLegend.isChecked():
										for i in range(res.LP.adverseE.nLocs):
											self.subplot.text(res.LP.adverseE.chainage[i],res.LP.adverseE.elevation[i]+0.25,res.LP.adverseE.node[i],rotation=90,verticalalignment='bottom',fontsize=12)
									else:
										self.lwStatus.insertItem(0,'Turn on legend to get more information about adverse grades')

						if (self.cb2ndAxis.isChecked()): # if not checked not dual axis needed
							if typenames2.count('Time Hmax')<>0:
								if res.formatVersion == 1: #2013
									message = "Time of H Max not available for Pre 2016 TUFLOW"
									self.lwStatus.insertItem(0,message)
									self.lwStatus.item(0).setTextColor(self.qred)
								else:
									a2, = self.axis2.plot(res.LP.dist_nodes, res.LP.tHmax)
									self.artists.append(a2)
									label = 'Time H Max'
									if nRes > 1:
										labels.append(label +" - "+name)
									else:
										labels.append(label)
									self.axis2.hold(True)
									#ymax = max(ymax,max(res.LP.chan_inv))						
									self.axis2.set_ylabel("Time of Peak Level")
				#Timeseries______________________________________________________________________
				elif (loc=="Timeseries"):
					# AXIS 1
					#xdata = res.getXData()
					
					breakloop = False
					for i, ydataid in enumerate(self.IDs):
						if ydataid:
							for typename in typenames:
								found = False
								message = 'ERROR - Unable to extract data'
								if not breakloop:
									if res.formatVersion == 1: #2013
										found, ydata, message = res.getTSData(ydataid,typename)
										xdata = res.times
									elif res.formatVersion == 2: #2015
										dom = self.Doms[i]
										source = self.Source_Att[i].upper()
										if (dom == '2D'):
											if typename.upper().find('STRUCTURE FLOWS')>= 0 and source=='QS':
												typename = 'QS'
											elif typename.upper().find('STRUCTURE LEVELS')>= 0 and source=='HU':
												typename = 'HU'
											elif typename.upper().find('STRUCTURE LEVELS')>= 0 and source=='HD':
												typename = 'HD'
										try:
											found, ydata, message = res.getTSData(ydataid,dom,typename, 'Geom')
											xdata = res.times
										except:
											self.lwStatus.insertItem(0,'ERROR - Extracting results')
											self.lwStatus.insertItem(0,'res = '+res.displayname)
											self.lwStatus.insertItem(0,'ID: '+ydataid)
											self.lwStatus.insertItem(0,'i: '+str(i))
									else:
										found = False
										message = 'Unexpected Format Version:'+str(res.formatVersion)
									if not found:
										self.lwStatus.insertItem(0,message)
										if res.formatVersion == 1:
											message = "No data for "+ydataid + " (1D) - " + typename
										else:
											message = "No data for "+ydataid + " ("+dom+") - " + typename
										self.lwStatus.insertItem(0,message)
									else:
										if res.formatVersion == 1:
											if (len(reslist) > 1):
												label = res.displayname + ": " +ydataid + " (1D) - " + typename
											else:
												label = ydataid + " - " + typename
										else:
											if (len(reslist) > 1):
												label = res.displayname + ": " +ydataid + "("+dom+") - " + typename
											else:
												label = ydataid + " ("+dom+") - " + typename

										tmp_xmin=min(xdata)
										xmin = min(xmin,tmp_xmin)
										tmp_xmax=max(xdata)
										xmax = max(xmax,tmp_xmax)
										tmp_ymin=ydata.min()
										ymin = min(ymin,tmp_ymin)
										tmp_ymax=ydata.max()
										ymax = max(ymax,tmp_ymax)
										
										#self.subplot.set_xbound(lower=xmin, upper=xmax)
										#self.subplot.set_ybound(lower=ymin, upper=ymax)
										if len(xdata)==len(ydata):
											a, = self.subplot.plot(xdata, ydata)
											self.artists.append(a)
											labels.append(label)
											self.subplot.hold(True)
										else:
											self.lwStatus.insertItem(0,'ERROR - Size of x and y data doesnt match')
					# AXIS 2
					#xdata = res.getXData()
					if (self.cb2ndAxis.isChecked()): # if not checked not dual axis needed
						breakloop = False
						for i, ydataid in enumerate(self.IDs):
							if ydataid:
								for typename in typenames2:
									found = False
									message = 'ERROR - Unable to extract data'
									if not breakloop:
										if res.formatVersion == 1: #2013
											found, ydata, message = res.getTSData(ydataid,typename)
											xdata = res.times
										elif res.formatVersion == 2: #2015
											#self.lwStatus.insertItem(0,'domain: '+self.Doms[i])
											dom = self.Doms[i].upper()
											source = self.Source_Att[i].upper()
											if (dom == '2D'):
												if typename.upper().find('STRUCTURE FLOWS')>= 0 and source=='QS':
													typename = 'QS'
												elif typename.upper().find('STRUCTURE LEVELS')>= 0 and source=='HU':
													typename = 'HU'
												elif typename.upper().find('STRUCTURE LEVELS')>= 0 and source=='HD':
													typename = 'HD'
											try:
												found, ydata, message = res.getTSData(ydataid,dom,typename, 'Geom')
												xdata = res.times
											except:
												self.lwStatus.insertItem(0,'ERROR - Extracting results')
												self.lwStatus.insertItem(0,'res = '+res.displayname)
												self.lwStatus.insertItem(0,'ID: '+ydataid)
												self.lwStatus.insertItem(0,'i: '+str(i))
										else:
											found = False
											message = 'Unexpected Format Version:'+str(res.formatVersion)
										if not found:
											ydata = xdata * 0.0 # keep the same dimensions other the plot will fail
											self.lwStatus.insertItem(0,message)
											if res.formatVersion == 1:
												message = "No data for "+ydataid + " (1D) - " + typename
											else:
												message = "No data for "+ydataid + " ("+dom+") - " + typename
											self.lwStatus.insertItem(0,message)
										else:
											if res.formatVersion == 1:
												if (len(reslist) > 1):
													label = res.displayname + ": " + ydataid + " (1D) - " + typename +" (Axis 2)"
												else:
													label = ydataid + " (1D) - " + typename +" (Axis 2)"
											else:
												if (len(reslist) > 1):
													label = res.displayname + ": " + ydataid + " ("+dom+") - " + typename +" (Axis 2)"
												else:
													label = ydataid + " ("+dom+") - " + typename +" (Axis 2)"
											#tmp_xmin=min(xdata)
											#xmin = min(xmin,tmp_xmin)
											#tmp_xmax=max(xdata)
											#xmax = max(xmax,tmp_xmax)
											#tmp_ymin=min(ydata)
											#ymin = min(ymin,tmp_ymin)
											#tmp_ymax=max(ydata)
											#ymax = max(ymax,tmp_ymax)
											
											#self.subplot.set_xbound(lower=xmin, upper=xmax)
											#self.subplot.set_ybound(lower=ymin, upper=ymax)
											if len(xdata)==len(ydata):
												a2, = self.axis2.plot(xdata, ydata, marker='x')
												self.artists.append(a2)
												labels.append(label)
												self.axis2.hold(True)
											else:
												self.lwStatus.insertItem(0,'ERROR - Number of x and y data points doesnt match')

				#Set axis labels
				if (loc=="Long Profile"): # LP
					if (res.units == 'METRIC'):
						self.subplot.set_xlabel('Distance (m)')
					elif (res.units == 'ENGLISH'):
						self.subplot.set_xlabel('Distance (ft)')
					else:
						self.subplot.set_xlabel('Distance')
				else:
					self.subplot.set_xlabel('Time (hours)')

				if (len(typeids) == 1):
					self.subplot.set_ylabel(typenames[0])
				else:
					self.subplot.set_title("")
			
			if self.cbShowLegend.isChecked():
				self.subplot.legend(self.artists, labels, bbox_to_anchor=(0, 0, 1, 1))
				
			self.subplot.hold(False)
			self.subplot.grid(True)
			xmin = math.floor(xmin)
			xmax = math.ceil(xmax)
			ymin = math.floor(ymin)
			#ymax = math.ceil(ymax)
			#self.lwStatus.insertItem(0,'applying bounds')
			#be a bit smarter with limits
			if ymax < 10:
				yinc = 1
			elif ymax < 30:
				yinc = 5
			elif ymax < 100:
				yinc = 10
			elif ymax < 300:
				yinc = 50
			elif ymax < 1000:
				yinc = 100		
			elif ymax < 3000:
				yinc = 500
			elif ymax < 10000:
				yinc = 1000
			elif ymax < 30000:
				yinc = 5000
			elif ymax < 100000:
				yinc = 10000
			elif ymax < 300000:
				yinc = 50000
			elif ymax < 1000000:
				yinc = 100000
			#self.lwStatus.insertItem(0,'ymax = '+str(ymax))
			#self.lwStatus.insertItem(0,'yinc = '+str(yinc))
			ymax2 = ymax = math.ceil(ymax/yinc) * yinc #round upper to nearest xinc
			#self.lwStatus.insertItem(0,'ymax2 = '+str(ymax2))
			self.subplot.set_xbound(lower=xmin, upper=xmax)
			self.subplot.set_ybound(lower=ymin, upper=ymax2)
			self.plotWdg.draw()

