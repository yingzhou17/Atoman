
"""
The output tab for the main toolbar

@author: Chris Scott

"""

import os
import sys
import shutil
import subprocess

import numpy as np
from PyQt4 import QtGui, QtCore

from ..visutils import utilities
from ..visutils.utilities import iconPath
from . import dialogs
from . import genericForm
from ..visclibs import output_c
from ..visclibs_ctypes import rdf as rdf_c
from . import plotDialog

try:
    from .. import resources
except ImportError:
    print "ERROR: could not import resources: ensure setup.py ran correctly"
    sys.exit(36)


################################################################################
class OutputDialog(QtGui.QDialog):
    def __init__(self, parent, mainWindow, width, index):
        super(OutputDialog, self).__init__(parent)
        
        self.parent = parent
        self.rendererWindow = parent
        self.mainToolbar = parent
        self.mainWindow = mainWindow
        self.width = width
        
        self.setWindowTitle("Output - Render window %d" % index)
        self.setModal(0)
        
        # layout
        outputTabLayout = QtGui.QVBoxLayout(self)
        outputTabLayout.setContentsMargins(0, 0, 0, 0)
        outputTabLayout.setSpacing(0)
        outputTabLayout.setAlignment(QtCore.Qt.AlignTop)
        
        # add tab bar
        self.outputTypeTabBar = QtGui.QTabWidget(self)
        self.outputTypeTabBar.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.connect(self.outputTypeTabBar, QtCore.SIGNAL('currentChanged(int)'), self.outputTypeTabBarChanged)
        
        # add tabs to tab bar
        
        # image tab
        imageTabWidget = QtGui.QWidget()
        imageTabLayout = QtGui.QVBoxLayout(imageTabWidget)
        imageTabLayout.setContentsMargins(0, 0, 0, 0)
        
        self.imageTab = ImageTab(self, self.mainWindow, self.width)
        imageTabLayout.addWidget(self.imageTab)
        
        self.outputTypeTabBar.addTab(imageTabWidget, "Image")
        
        # file tab
        fileTabWidget = QtGui.QWidget()
        fileTabLayout = QtGui.QVBoxLayout(fileTabWidget)
        fileTabLayout.setContentsMargins(0, 0, 0, 0)
        
        self.fileTab = FileTab(self, self.mainWindow, self.width)
        fileTabLayout.addWidget(self.fileTab)
        
        self.outputTypeTabBar.addTab(fileTabWidget, "File")
        
        # rdf tab
        rdfTabWidget = QtGui.QWidget()
        rdfTabLayout = QtGui.QVBoxLayout(rdfTabWidget)
        rdfTabLayout.setContentsMargins(0, 0, 0, 0)
        
        self.rdfTab = RDFTab(self, self.mainWindow, self.width)
        rdfTabLayout.addWidget(self.rdfTab)
        
        self.outputTypeTabBar.addTab(rdfTabWidget, "Plot")
        
        # add tab bar to layout
        outputTabLayout.addWidget(self.outputTypeTabBar)
        
        
    def outputTypeTabBarChanged(self):
        pass

################################################################################

class RDFTab(QtGui.QWidget):
    """
    RDF output tab.
    
    """
    def __init__(self, parent, mainWindow, tabWidth):
        super(RDFTab, self).__init__(parent)
        
        self.parent = parent
        self.mainWindow = mainWindow
        self.tabWidth = tabWidth
        self.rendererWindow = self.parent.rendererWindow
        
        # defaults
        self.spec1 = "ALL"
        self.spec2 = "ALL"
        self.binMin = 2.0
        self.binMax = 10.0
        self.NBins = 100
        
        # layout
        formLayout = QtGui.QVBoxLayout(self)
        formLayout.setAlignment(QtCore.Qt.AlignTop)
        
        # form
        rdfForm = genericForm.GenericForm(self, 0, "RDF plot options")
        rdfForm.show()
        
        # bond type
        label = QtGui.QLabel("Bond type:")
        row = rdfForm.newRow()
        row.addWidget(label)
        
        self.spec1Combo = QtGui.QComboBox()
        self.spec1Combo.addItem("ALL")
        self.spec1Combo.currentIndexChanged[QtCore.QString].connect(self.spec1Changed)
        row.addWidget(self.spec1Combo)
        
        label = QtGui.QLabel(" - ")
        row.addWidget(label)
        
        self.spec2Combo = QtGui.QComboBox()
        self.spec2Combo.addItem("ALL")
        self.spec2Combo.currentIndexChanged[QtCore.QString].connect(self.spec2Changed)
        row.addWidget(self.spec2Combo)
        
        # bin range
        label = QtGui.QLabel("Bin range:")
        row = rdfForm.newRow()
        row.addWidget(label)
        
        binMinSpin = QtGui.QDoubleSpinBox()
        binMinSpin.setMinimum(0.0)
        binMinSpin.setMaximum(500.0)
        binMinSpin.setSingleStep(0.01)
        binMinSpin.setValue(self.binMin)
        binMinSpin.valueChanged.connect(self.binMinChanged)
        row.addWidget(binMinSpin)
        
        label = QtGui.QLabel(" - ")
        row.addWidget(label)
        
        binMaxSpin = QtGui.QDoubleSpinBox()
        binMaxSpin.setMinimum(0.0)
        binMaxSpin.setMaximum(500.0)
        binMaxSpin.setSingleStep(0.01)
        binMaxSpin.setValue(self.binMax)
        binMaxSpin.valueChanged.connect(self.binMaxChanged)
        row.addWidget(binMaxSpin)
        
        # num bins
        label = QtGui.QLabel("Number of bins:")
        row = rdfForm.newRow()
        row.addWidget(label)
        
        numBinsSpin = QtGui.QSpinBox()
        numBinsSpin.setMinimum(2)
        numBinsSpin.setMaximum(100000)
        numBinsSpin.setSingleStep(1)
        numBinsSpin.setValue(self.NBins)
        numBinsSpin.valueChanged.connect(self.numBinsChanged)
        row.addWidget(numBinsSpin)
        
        # plot button
        plotButton = QtGui.QPushButton(QtGui.QIcon(iconPath("Plotter.png")), "Plot")
        plotButton.clicked.connect(self.plotRDF)
        row = rdfForm.newRow()
        row.addWidget(plotButton)
        
        formLayout.addWidget(rdfForm)
    
    def refresh(self):
        """
        Should be called whenver a new input is loaded.
        
        Refreshes the combo boxes with input specie list.
        
        """
        # lattice
        specieList = self.mainWindow.inputState.specieList
        
        # store current so can try to reselect
        spec1CurrentText = str(self.spec1Combo.currentText())
        spec2CurrentText = str(self.spec2Combo.currentText())
        
        # clear and rebuild combo box
        self.spec1Combo.clear()
        self.spec2Combo.clear()
        
        self.spec1Combo.addItem("ALL")
        self.spec2Combo.addItem("ALL")
        
        count = 1
        match1 = False
        match2 = False
        for sym in specieList:
            self.spec1Combo.addItem(sym)
            self.spec2Combo.addItem(sym)
            
            if sym == spec1CurrentText:
                self.spec1Combo.setCurrentIndex(count)
                match1 = True
            
            if sym == spec2CurrentText:
                self.spec2Combo.setCurrentIndex(count)
                match2 = True
            
            count += 1
        
        if not match1:
            self.spec1Combo.setCurrentIndex(0)
        
        if not match2:
            self.spec2Combo.setCurrentIndex(0)
    
    def plotRDF(self):
        """
        Plot RDF.
        
        """
        # first gather vis atoms
        visibleAtoms = self.rendererWindow.gatherVisibleAtoms()
                    
        if not len(visibleAtoms):
            self.mainWindow.displayWarning("No visible atoms: cannot calculate RDF")
            return
        
        # then determine species
        inputLattice = self.mainWindow.inputState
        specieList = inputLattice.specieList
        
        if self.spec1 == "ALL":
            spec1Index = -1
        else:
            spec1Index = int(np.where(specieList == self.spec1)[0][0])
        
        if self.spec2 == "ALL":
            spec2Index = -1
        else:
            spec2Index = int(np.where(specieList == self.spec2)[0][0])
        
        # prelims
        rdfArray = np.zeros(self.NBins, np.float64)
        
        # then calculate
        rdf_c.calculateRDF(visibleAtoms, inputLattice.specie, inputLattice.pos, spec1Index, spec2Index, inputLattice.minPos,
                           inputLattice.maxPos, inputLattice.cellDims, self.mainWindow.PBC, self.binMin, self.binMax, self.NBins,
                           rdfArray)
                
        # then plot
        interval = (self.binMax - self.binMin) / float(self.NBins)
        xn = np.arange(self.binMin + interval / 2.0, self.binMax, interval, dtype=np.float64)
        
        #TODO: option to write to file?
        
        # prepare to plot
        settingsDict = {}
        settingsDict["title"] = "Radial distribution function"
        settingsDict["xlabel"] = "Bond length (A)"
        settingsDict["ylabel"] = "%s - %s G(r)" % (self.spec1, self.spec2)
        
        # show plot dialog
        dialog = plotDialog.PlotDialog(self, self.mainWindow, "Radial distribution function ", 
                                       "plot", (xn, rdfArray), {"linewidth": 2, "label": None},
                                       settingsDict=settingsDict)
        dialog.show()
    
    def numBinsChanged(self, val):
        """
        Num bins changed.
        
        """
        self.NBins = val
    
    def binMinChanged(self, val):
        """
        Bin min changed.
        
        """
        self.binMin = val
    
    def binMaxChanged(self, val):
        """
        Bin max changed.
        
        """
        self.binMax = val
    
    def spec1Changed(self, text):
        """
        Spec 1 changed.
        
        """
        self.spec1 = str(text)
    
    def spec2Changed(self, text):
        """
        Spec 2 changed.
        
        """
        self.spec2 = str(text)
    

################################################################################

class FileTab(QtGui.QWidget):
    """
    File output tab.
    
    """
    def __init__(self, parent, mainWindow, width):
        super(FileTab, self).__init__(parent)
        
        self.parent = parent
        self.rendererWindow = parent
        self.mainWindow = mainWindow
        self.width = width
        
        # initial values
        self.outputFileType = "LATTICE"
        
        # layout
        mainLayout = QtGui.QVBoxLayout(self)
        mainLayout.setAlignment(QtCore.Qt.AlignTop)
        
        # name group
        fileNameGroup = genericForm.GenericForm(self, 0, "Output file options")
        fileNameGroup.show()
        
        # file type
        outputTypeCombo = QtGui.QComboBox()
        outputTypeCombo.addItem("LATTICE")
#         outputTypeCombo.addItem("LBOMD REF")
#         outputTypeCombo.addItem("LBOMD XYZ")
#         outputTypeCombo.addItem("LBOMD FAILSAFE")
        outputTypeCombo.currentIndexChanged[QtCore.QString].connect(self.outputTypeChanged)
        
        label = QtGui.QLabel("File type: ")
        
        row = fileNameGroup.newRow()
        row.addWidget(label)
        row.addWidget(outputTypeCombo)
        
        # file name, save image button
        row = fileNameGroup.newRow()
        
        label = QtGui.QLabel("File name: ")
        self.outputFileName = QtGui.QLineEdit("lattice.dat")
        self.outputFileName.setFixedWidth(120)
        saveFileButton = QtGui.QPushButton(QtGui.QIcon(iconPath("image-x-generic.svg")), "")
        saveFileButton.setStatusTip("Save to file")
        saveFileButton.clicked.connect(self.saveToFile)
        
        row.addWidget(label)
        row.addWidget(self.outputFileName)
        row.addWidget(saveFileButton)
        
        # dialog
        row = fileNameGroup.newRow()
        
        saveFileDialogButton = QtGui.QPushButton(QtGui.QIcon(iconPath('document-open.svg')), "Save to file")
        saveFileDialogButton.setStatusTip("Save to file")
        saveFileDialogButton.setCheckable(0)
        saveFileDialogButton.setFixedWidth(150)
        saveFileDialogButton.clicked.connect(self.saveToFileDialog)
        
        row.addWidget(saveFileDialogButton)
        
        # overwrite
        self.overwriteCheck = QtGui.QCheckBox("Overwrite")
        
        row = fileNameGroup.newRow()
        row.addWidget(self.overwriteCheck)
        
        mainLayout.addWidget(fileNameGroup)
    
    def saveToFile(self):
        """
        Save current system to file.
        
        """
        filename = str(self.outputFileName.text())
        
        if not len(filename):
            return
        
        if os.path.exists(filename) and not self.overwriteCheck.isChecked():
            self.mainWindow.displayWarning("File already exists: not overwriting")
            return
        
        # lattice object
        lattice = self.mainWindow.inputState
        
        # gather vis atoms
        visibleAtoms = self.rendererWindow.gatherVisibleAtoms()
        
        #TODO: this should write visible atoms only, not whole lattice!
        
        output_c.writeLattice(filename, visibleAtoms, lattice.cellDims[0], lattice.cellDims[1], lattice.cellDims[2],
                              lattice.specieList, lattice.specie, lattice.pos, lattice.charge)
    
    def saveToFileDialog(self):
        """
        Open dialog.
        
        """
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '.')
        
        if len(filename):
            self.outputFileName.setText(str(filename))
            self.saveToFile()
    
    def outputTypeChanged(self, fileType):
        """
        Output type changed.
        
        """
        self.outputFileType = str(fileType)


################################################################################

class ImageTab(QtGui.QWidget):
    def __init__(self, parent, mainWindow, width):
        super(ImageTab, self).__init__(parent)
        
        self.parent = parent
        self.mainWindow = mainWindow
        self.width = width
        self.rendererWindow = self.parent.rendererWindow
        
        # initial values
        self.renderType = "VTK"
        self.imageFormat = "jpg"
#        self.overlayImage = False
        
        # check ffmpeg/povray installed
        self.ffmpeg = utilities.checkForExe("ffmpeg")
        self.povray = utilities.checkForExe("povray")
        
        if self.ffmpeg:
            self.mainWindow.console.write("'ffmpeg' executable located at: %s" % (self.ffmpeg,))
        
        if self.povray:
            self.mainWindow.console.write("'povray' executable located at: %s" % (self.povray,))
        
        imageTabLayout = QtGui.QVBoxLayout(self)
#        imageTabLayout.setContentsMargins(0, 0, 0, 0)
#        imageTabLayout.setSpacing(0)
        imageTabLayout.setAlignment(QtCore.Qt.AlignTop)
        
        # Add the generic image options at the top
        group = QtGui.QGroupBox("Image options")
        group.setAlignment(QtCore.Qt.AlignHCenter)
        
        groupLayout = QtGui.QVBoxLayout(group)
        groupLayout.setContentsMargins(0, 0, 0, 0)
        groupLayout.setSpacing(0)
        
        # render type (povray or vtk)
        renderTypeButtonGroup = QtGui.QButtonGroup(self)
        renderTypeButtonGroup.setExclusive(1)
        
        self.connect(renderTypeButtonGroup, QtCore.SIGNAL('buttonClicked(int)'), self.setRenderType)
        
        self.POVButton = QtGui.QPushButton(QtGui.QIcon(iconPath("pov-icon.svg")), "POV-Ray")
        self.POVButton.setCheckable(1)
        self.POVButton.setChecked(0)
        
        self.VTKButton = QtGui.QPushButton(QtGui.QIcon(iconPath("vtk-icon.svg")), "VTK")
        self.VTKButton.setCheckable(1)
        self.VTKButton.setChecked(1)
        
        renderTypeButtonGroup.addButton(self.VTKButton)
        renderTypeButtonGroup.addButton(self.POVButton)
        
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
        rowLayout.setAlignment(QtCore.Qt.AlignTop)
        rowLayout.addWidget(self.VTKButton)
        rowLayout.addWidget(self.POVButton)
        
        groupLayout.addWidget(row)
        
        # image format
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        imageFormatButtonGroup = QtGui.QButtonGroup(self)
        imageFormatButtonGroup.setExclusive(1)
        
        self.connect(imageFormatButtonGroup, QtCore.SIGNAL('buttonClicked(int)'), self.setImageFormat)
        
        self.JPEGCheck = QtGui.QCheckBox("JPEG")
        self.JPEGCheck.setChecked(1)
        self.PNGCheck = QtGui.QCheckBox("PNG")
        self.TIFFCheck = QtGui.QCheckBox("TIFF")
        
        imageFormatButtonGroup.addButton(self.JPEGCheck)
        imageFormatButtonGroup.addButton(self.PNGCheck)
        imageFormatButtonGroup.addButton(self.TIFFCheck)
        
        rowLayout.addWidget(self.JPEGCheck)
        rowLayout.addWidget(self.PNGCheck)
        rowLayout.addWidget(self.TIFFCheck)
        
        groupLayout.addWidget(row)
        
        # additional (POV-Ray) options
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        groupLayout.addWidget(row)
        
        imageTabLayout.addWidget(group)
        
        # tab bar for different types of image output
        self.imageTabBar = QtGui.QTabWidget(self)
        self.imageTabBar.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.connect(self.imageTabBar, QtCore.SIGNAL('currentChanged(int)'), self.imageTabBarChanged)
        
        # add tabs to tab bar
        singleImageTabWidget = QtGui.QWidget()
        singleImageTabLayout = QtGui.QVBoxLayout(singleImageTabWidget)
        singleImageTabLayout.setContentsMargins(0, 0, 0, 0)
        self.singleImageTab = SingleImageTab(self, self.mainWindow, self.width)
        singleImageTabLayout.addWidget(self.singleImageTab)
        self.imageTabBar.addTab(singleImageTabWidget, "Single")
        
        imageSequenceTabWidget = QtGui.QWidget()
        imageSequenceTabLayout = QtGui.QVBoxLayout(imageSequenceTabWidget)
        imageSequenceTabLayout.setContentsMargins(0, 0, 0, 0)
        self.imageSequenceTab = ImageSequenceTab(self, self.mainWindow, self.width)
        imageSequenceTabLayout.addWidget(self.imageSequenceTab)
        self.imageTabBar.addTab(imageSequenceTabWidget, "Sequence")
        
        imageRotateTabWidget = QtGui.QWidget()
        imageRotateTabLayout = QtGui.QVBoxLayout(imageRotateTabWidget)
        imageRotateTabLayout.setContentsMargins(0, 0, 0, 0)
        self.imageRotateTab = ImageRotateTab(self, self.mainWindow, self.width)
        imageRotateTabLayout.addWidget(self.imageRotateTab)
        self.imageTabBar.addTab(imageRotateTabWidget, "Rotate")
        
        imageTabLayout.addWidget(self.imageTabBar)
    
    def imageTabBarChanged(self, val):
        """
        
        
        """
        pass
    
    def setImageFormat(self, val):
        """
        Set the image format.
        
        """
        if self.JPEGCheck.isChecked():
            self.imageFormat = "jpg"
        
        elif self.PNGCheck.isChecked():
            self.imageFormat = "png"
        
        elif self.TIFFCheck.isChecked():
            self.imageFormat = "tif"
    
    def setRenderType(self, val):
        """
        Set current render type
        
        """
        if self.POVButton.isChecked():
            if not self.povray:
                self.POVButton.setChecked(0)
                self.VTKButton.setChecked(1)
                utilities.warnExeNotFound(self, "povray")
            
            else:
                self.renderType = "POV"
                self.imageFormat = "png"
                self.PNGCheck.setChecked(1)
        
        elif self.VTKButton.isChecked():
            self.renderType = "VTK"
            self.imageFormat = "jpg"
            self.JPEGCheck.setChecked(1)
    
    def createMovie(self, saveDir, saveText):
        """
        Create movie.
        
        """
        log = self.mainWindow.console.write
        
        CWD = os.getcwd()
        try:
            os.chdir(saveDir)
        except OSError:
            return 1
        
        try:
            # temporary (should be optional)
            settings = self.mainWindow.preferences.ffmpegForm
            framerate = settings.framerate
            bitrate = settings.bitrate
            outputprefix = settings.prefix
            outputsuffix = settings.suffix
            
            saveText = os.path.basename(saveText)
            
            command = "%s -r %d -y -i %s.%s -r %d -b %dk %s.%s" % (self.ffmpeg, framerate, saveText, 
                                                                  self.imageFormat, 25, bitrate, 
                                                                  outputprefix, outputsuffix)
            
            log("Creating movie file: %s.%s" % (outputprefix, outputsuffix))
            
            # change to QProcess
            process = subprocess.Popen(command, shell=True, executable="/bin/bash", stdin=subprocess.PIPE, 
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, stderr = process.communicate()
            status = process.poll()
            if status:
                log("FFMPEG FAILED")
                print stderr
        
        finally:
            os.chdir(CWD)
        

################################################################################
class SingleImageTab(QtGui.QWidget):
    def __init__(self, parent, mainWindow, width):
        super(SingleImageTab, self).__init__(parent)
        
        self.parent = parent
        self.mainWindow = mainWindow
        self.width = width
        self.rendererWindow = self.parent.rendererWindow
        
        # initial values
        self.overwriteImage = 0
        self.openImage = 1
        
        # layout
        mainLayout = QtGui.QVBoxLayout(self)
#        mainLayout.setContentsMargins(0, 0, 0, 0)
#        mainLayout.setSpacing(0)
        mainLayout.setAlignment(QtCore.Qt.AlignTop)
        
        # file name, save image button
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        
        label = QtGui.QLabel("File name")
        self.imageFileName = QtGui.QLineEdit("image")
        self.imageFileName.setFixedWidth(120)
        saveImageButton = QtGui.QPushButton(QtGui.QIcon(iconPath("image-x-generic.svg")), "")
        saveImageButton.setStatusTip("Save image")
        self.connect(saveImageButton, QtCore.SIGNAL('clicked()'), 
                     lambda showProgress=True: self.saveSingleImage(showProgress))
        
        rowLayout.addWidget(label)
        rowLayout.addWidget(self.imageFileName)
        rowLayout.addWidget(saveImageButton)
        
        mainLayout.addWidget(row)
        
        # dialog
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        
        saveImageDialogButton = QtGui.QPushButton(QtGui.QIcon(iconPath('document-open.svg')), "Save image")
        saveImageDialogButton.setStatusTip("Save image")
        saveImageDialogButton.setCheckable(0)
        saveImageDialogButton.setFixedWidth(150)
        self.connect(saveImageDialogButton, QtCore.SIGNAL('clicked()'), self.saveSingleImageDialog)
        
        rowLayout.addWidget(saveImageDialogButton)
        
        mainLayout.addWidget(row)
        
        # options
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        self.overwriteCheck = QtGui.QCheckBox("Overwrite")
        self.connect(self.overwriteCheck, QtCore.SIGNAL('stateChanged(int)'), self.overwriteCheckChanged)
        
        self.openImageCheck = QtGui.QCheckBox("Open image")
        self.openImageCheck.setChecked(True)
        self.connect(self.openImageCheck, QtCore.SIGNAL('stateChanged(int)'), self.openImageCheckChanged)
        
        rowLayout.addWidget(self.overwriteCheck)
        rowLayout.addWidget(self.openImageCheck)
        
        mainLayout.addWidget(row)
        
    def saveSingleImageDialog(self):
        """
        Open dialog to get save file name
        
        """
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '.')
        
        if len(filename):
            self.imageFileName.setText(str(filename))
            self.saveSingleImage(showProgress=True)
    
    def saveSingleImage(self, showProgress=False):
        """
        Screen capture.
        
        """
        filename = str(self.imageFileName.text())
        
        if not len(filename):
            return
        
        # check if in different dir
#        head, tail = os.path.split(filename)
        
        # change to dir if required (for POV-Ray to work)
#        if len(head):
#            OWD = os.getcwd()
#            os.chdir(head)
#            filename = tail
        
        # show progress dialog
        if showProgress and self.parent.renderType == "POV":
            progress = QtGui.QProgressDialog(parent=self)
            progress.setWindowModality(QtCore.Qt.WindowModal)
            progress.setWindowTitle("Busy")
            progress.setLabelText("Running POV-Ray...")
            progress.setRange(0, 0)
            progress.setMinimumDuration(0)
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            progress.show()
        
        filename = self.rendererWindow.renderer.saveImage(self.parent.renderType, self.parent.imageFormat, 
                                                          filename, self.overwriteImage, povray=self.parent.povray)
        
        # hide progress dialog
        if showProgress and self.parent.renderType == "POV":
            QtGui.QApplication.restoreOverrideCursor()
            progress.cancel()
        
        # change back to original working dir
#        if len(head):
#            os.chdir(OWD)
#            filename = os.path.join(head, tail)
        
        if filename is None:
            print "SAVE IMAGE FAILED"
            return
        
        # open image viewer
        if self.openImage:
            dirname = os.path.dirname(filename)
            if not dirname:
                dirname = os.getcwd()
            
            self.mainWindow.imageViewer.changeDir(dirname)
            self.mainWindow.imageViewer.showImage(filename)
            self.mainWindow.imageViewer.hide()
            self.mainWindow.imageViewer.show()
    
    def openImageCheckChanged(self, val):
        """
        Open image
        
        """
        if self.openImageCheck.isChecked():
            self.openImage = 1
        
        else:
            self.openImage = 0
    
    def overwriteCheckChanged(self, val):
        """
        Overwrite file
        
        """
        if self.overwriteCheck.isChecked():
            self.overwriteImage = 1
        
        else:
            self.overwriteImage = 0
    

################################################################################
class ImageSequenceTab(QtGui.QWidget):
    def __init__(self, parent, mainWindow, width):
        super(ImageSequenceTab, self).__init__(parent)
        
        self.parent = parent
        self.mainWindow = mainWindow
        self.width = width
        self.rendererWindow = self.parent.rendererWindow
        
        # initial values
        self.numberFormat = "%04d"
        self.minIndex = 0
        self.maxIndex = 10
        self.interval = 1
        self.fileprefixText = "guess"
        self.overwrite = 0
        self.createMovie = 1
        
        # layout
        mainLayout = QtGui.QVBoxLayout(self)
#        mainLayout.setContentsMargins(0, 0, 0, 0)
#        mainLayout.setSpacing(0)
        mainLayout.setAlignment(QtCore.Qt.AlignTop)
        
        # output directory
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        label = QtGui.QLabel("Output folder")
        self.outputFolder = QtGui.QLineEdit("sequencer")
        self.outputFolder.setFixedWidth(120)
        
        rowLayout.addWidget(label)
        rowLayout.addWidget(self.outputFolder)
        
        mainLayout.addWidget(row)
        
        # file prefix
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        label = QtGui.QLabel("File prefix")
                
        self.fileprefix = QtGui.QLineEdit(self.fileprefixText)
        self.fileprefix.setFixedWidth(120)
        self.connect(self.fileprefix, QtCore.SIGNAL('textChanged(QString)'), self.fileprefixChanged)
        
        resetPrefixButton = QtGui.QPushButton(QtGui.QIcon(iconPath("edit-paste.svg")), "")
        resetPrefixButton.setStatusTip("Set prefix to input file")
        self.connect(resetPrefixButton, QtCore.SIGNAL("clicked()"), self.resetPrefix)
        
        rowLayout.addWidget(label)
        rowLayout.addWidget(self.fileprefix)
        rowLayout.addWidget(resetPrefixButton)
        
        mainLayout.addWidget(row)
        
        group = QtGui.QGroupBox("Numbering")
        group.setAlignment(QtCore.Qt.AlignHCenter)
        
        groupLayout = QtGui.QVBoxLayout(group)
        groupLayout.setContentsMargins(0, 0, 0, 0)
        groupLayout.setSpacing(0)
        
        
        
        # numbering format
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
#        label = QtGui.QLabel("Number format")
        self.numberFormatCombo = QtGui.QComboBox()
        self.numberFormatCombo.addItem("%04d")
        self.numberFormatCombo.addItem("%d")
        self.connect(self.numberFormatCombo, QtCore.SIGNAL("currentIndexChanged(QString)"), self.numberFormatChanged)
        
#        rowLayout.addWidget(label)
        rowLayout.addWidget(self.numberFormatCombo)
        
        groupLayout.addWidget(row)
        
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        self.minIndexSpinBox = QtGui.QSpinBox()
        self.minIndexSpinBox.setMinimum(0)
        self.minIndexSpinBox.setMaximum(99999)
        self.minIndexSpinBox.setValue(self.minIndex)
        self.connect(self.minIndexSpinBox, QtCore.SIGNAL('valueChanged(int)'), self.minIndexChanged)
        
        label = QtGui.QLabel("to")
        
        self.maxIndexSpinBox = QtGui.QSpinBox()
        self.maxIndexSpinBox.setMinimum(1)
        self.maxIndexSpinBox.setMaximum(99999)
        self.maxIndexSpinBox.setValue(self.maxIndex)
        self.connect(self.maxIndexSpinBox, QtCore.SIGNAL('valueChanged(int)'), self.maxIndexChanged)
        
        label2 = QtGui.QLabel("by")
        
        self.intervalSpinBox = QtGui.QSpinBox()
        self.intervalSpinBox.setMinimum(1)
        self.intervalSpinBox.setMaximum(99999)
        self.intervalSpinBox.setValue(self.interval)
        self.connect(self.intervalSpinBox, QtCore.SIGNAL('valueChanged(int)'), self.intervalChanged)
        
        rowLayout.addWidget(self.minIndexSpinBox)
        rowLayout.addWidget(label)
        rowLayout.addWidget(self.maxIndexSpinBox)
        rowLayout.addWidget(label2)
        rowLayout.addWidget(self.intervalSpinBox)
        
        groupLayout.addWidget(row)
        
        mainLayout.addWidget(group)
        
        # first file
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        label = QtGui.QLabel("First file:")
        
        self.firstFileLabel = QtGui.QLabel("")
        self.setFirstFileLabel()
        
        rowLayout.addWidget(label)
        rowLayout.addWidget(self.firstFileLabel)
        
        mainLayout.addWidget(row)
        
        # overwrite check box
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        self.overwriteCheck = QtGui.QCheckBox("Overwrite")
        self.connect(self.overwriteCheck, QtCore.SIGNAL('stateChanged(int)'), self.overwriteCheckChanged)
        
        rowLayout.addWidget(self.overwriteCheck)
        
        mainLayout.addWidget(row)
        
        # create movie check box
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        self.createMovieCheck = QtGui.QCheckBox("Create movie")
        if self.parent.ffmpeg:
            self.createMovieCheck.setChecked(True)
            self.createMovie = True
        else:
            self.createMovieCheck.setChecked(False)
            self.createMovie = False
        self.connect(self.createMovieCheck, QtCore.SIGNAL('stateChanged(int)'), self.createMovieCheckChanged)
        
        rowLayout.addWidget(self.createMovieCheck)
        
        mainLayout.addWidget(row)
        
        # start button
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        startSequencerButton = QtGui.QPushButton(QtGui.QIcon(iconPath("loadandsave-icon.svg")), "START")
        startSequencerButton.setStatusTip("Start sequencer")
        self.connect(startSequencerButton, QtCore.SIGNAL('clicked()'), self.startSequencer)
        
        rowLayout.addWidget(startSequencerButton)
        
        mainLayout.addWidget(row)
        
    def createMovieCheckChanged(self, val):
        """
        Create movie?
        
        """
        if self.createMovieCheck.isChecked():
            if not self.parent.ffmpeg:
                utilities.warnExeNotFound(self.parent, "ffmpeg")
                self.createMovieCheck.setCheckState(0)
                return
            
            self.createMovie = True
        
        else:
            self.createMovie = False
    
    def resetPrefix(self):
        """
        Reset the prefix to the one from 
        the input page
        
        """
        filename = self.mainWindow.inputFile
        
        count = 0
        for i in xrange(len(filename)):
            if filename[i] == ".":
                break
            
            error = 0
            try:
                int(filename[i])
            except ValueError:
                error = 1
            
            if not error:
                break
            
            count += 1
        
        self.fileprefix.setText(filename[:count])
    
    def startSequencer(self):
        """
        Start the sequencer
        
        """
        self.runSequencer()
        
    def runSequencer(self):
        """
        Run the sequencer
        
        """
        self.setFirstFileLabel()
        
        # check first file exists
        firstFileExists = utilities.checkForFile(str(self.firstFileLabel.text()))
        if not firstFileExists:
            self.warnFirstFileNotPresent(str(self.firstFileLabel.text()))
            return
        
        # formatted string
        fileText = "%s%s.%s" % (str(self.fileprefix.text()), self.numberFormat, self.mainWindow.fileExtension)
        
        log = self.mainWindow.console.write
        log("Running sequencer", 0, 0)
        
        # directory
        saveDir = str(self.outputFolder.text())
        if os.path.exists(saveDir):
            if self.overwrite:
                shutil.rmtree(saveDir)
            
            else:
                count = 0
                while os.path.exists(saveDir):
                    count += 1
                    saveDir = "%s.%d" % (str(self.outputFolder.text()), count)
        
        os.mkdir(saveDir)
        
        saveText = os.path.join(saveDir, "%s%s" % (str(self.fileprefix.text()), self.numberFormat))
        
        # progress dialog
        NSteps = int((self.maxIndex - self.minIndex) / self.interval) + 1
        progDialog = QtGui.QProgressDialog("Running sequencer...", "Cancel", self.minIndex, NSteps)
        progDialog.setWindowModality(QtCore.Qt.WindowModal)
        progDialog.setWindowTitle("Progress")
        progDialog.setValue(self.minIndex)
        
        # loop over files
        try:
            count = 0
            for i in xrange(self.minIndex, self.maxIndex + self.interval, self.interval):
                currentFile = fileText % (i,)
                log("Current file: %s" % (currentFile,), 0, 1)
                
                # first open the file
                form = self.mainWindow.loadInputDialog.loadInputStack.widget(self.mainWindow.loadInputDialog.inputTypeCurrentIndex)
                status = form.openFile(filename=currentFile, rouletteIndex=i-1)
                
                # exit if cancelled
                if progDialog.wasCanceled():
                    return
                
                if status:
                    print "SEQUENCER ERROR"
                    return
                
                # now apply all filters
                pipelinePage = self.rendererWindow.getCurrentPipelinePage()
                pipelinePage.runAllFilterLists()
                
                # exit if cancelled
                if progDialog.wasCanceled():
                    return
                
                saveName = saveText % (count,)
                log("Saving image: %s" % (saveName,), 0, 2)
                
                # now save image
                filename = self.rendererWindow.renderer.saveImage(self.parent.renderType, self.parent.imageFormat, 
                                                                  saveName, 1, povray=self.parent.povray)
                
                count += 1
                
                # exit if cancelled
                if progDialog.wasCanceled():
                    return
                
                # update progress
                progDialog.setValue(count)
                
                QtGui.QApplication.processEvents()
        
        finally:
            # close progress dialog
            progDialog.close()
        
        # create movie
        if self.createMovie:
            # show wait cursor
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            
            
            try:
                self.parent.createMovie(saveDir, saveText)
            
            finally:
                # set cursor to normal
                QtGui.QApplication.restoreOverrideCursor()
    
    def warnFirstFileNotPresent(self, filename):
        """
        Warn the first file is not present.
        
        """
        QtGui.QMessageBox.warning(self, "Warning", "Could not locate first file in sequence: %s" % (filename,))
    
    def overwriteCheckChanged(self, val):
        """
        Overwrite check changed
        
        """
        if self.overwriteCheck.isChecked():
            self.overwrite = 1
        
        else:
            self.overwrite = 0
    
    def fileprefixChanged(self, text):
        """
        File prefix has changed
        
        """
        self.fileprefixText = str(text)
        
        self.setFirstFileLabel()
    
    def setFirstFileLabel(self):
        """
        Set the first file label
        
        """
        text = "%s%s.%s" % (self.fileprefix.text(), self.numberFormat, self.mainWindow.fileExtension)
        self.firstFileLabel.setText(text % (self.minIndex,))
    
    def minIndexChanged(self, val):
        """
        Minimum index changed
        
        """
        self.minIndex = val
        
        self.setFirstFileLabel()
    
    def maxIndexChanged(self, val):
        """
        Maximum index changed
        
        """
        self.maxIndex = val
    
    def intervalChanged(self, val):
        """
        Interval changed
        
        """
        self.interval = val
    
    def numberFormatChanged(self, text):
        """
        Change number format
        
        """
        self.numberFormat = str(text)
        
        self.setFirstFileLabel()


################################################################################
class ImageRotateTab(QtGui.QWidget):
    def __init__(self, parent, mainWindow, width):
        super(ImageRotateTab, self).__init__(parent)
        
        self.parent = parent
        self.mainWindow = mainWindow
        self.width = width
        self.rendererWindow = self.parent.rendererWindow
        
        # initial values
        self.fileprefixText = "rotate"
        self.overwrite = 0
        self.createMovie = 0
        self.degreesPerRotation = 5.0
        
        # layout
        mainLayout = QtGui.QVBoxLayout(self)
#        mainLayout.setContentsMargins(0, 0, 0, 0)
#        mainLayout.setSpacing(0)
        mainLayout.setAlignment(QtCore.Qt.AlignTop)
        
        # output directory
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        label = QtGui.QLabel("Output folder")
        self.outputFolder = QtGui.QLineEdit("rotate")
        self.outputFolder.setFixedWidth(120)
        
        rowLayout.addWidget(label)
        rowLayout.addWidget(self.outputFolder)
        
        mainLayout.addWidget(row)
        
        # file prefix
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        label = QtGui.QLabel("File prefix")
                
        self.fileprefix = QtGui.QLineEdit(self.fileprefixText)
        self.fileprefix.setFixedWidth(120)
        self.connect(self.fileprefix, QtCore.SIGNAL('textChanged(QString)'), self.fileprefixChanged)
        
        rowLayout.addWidget(label)
        rowLayout.addWidget(self.fileprefix)
        
        mainLayout.addWidget(row)
        
        # degrees per rotation
        label = QtGui.QLabel("Degrees per rotation")
        
        degPerRotSpinBox = QtGui.QSpinBox(self)
        degPerRotSpinBox.setMinimum(1)
        degPerRotSpinBox.setMaximum(360)
        degPerRotSpinBox.setValue(self.degreesPerRotation)
        degPerRotSpinBox.valueChanged.connect(self.degPerRotChanged)
        
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        rowLayout.addWidget(label)
        rowLayout.addWidget(degPerRotSpinBox)
        
        mainLayout.addWidget(row)
                
        # overwrite check box
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        self.overwriteCheck = QtGui.QCheckBox("Overwrite")
        self.connect(self.overwriteCheck, QtCore.SIGNAL('stateChanged(int)'), self.overwriteCheckChanged)
        
        rowLayout.addWidget(self.overwriteCheck)
        
        mainLayout.addWidget(row)
        
        # create movie check box
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        self.createMovieCheck = QtGui.QCheckBox("Create movie")
        if self.parent.ffmpeg:
            self.createMovieCheck.setChecked(True)
            self.createMovie = True
        else:
            self.createMovieCheck.setChecked(False)
            self.createMovie = False
        self.connect(self.createMovieCheck, QtCore.SIGNAL('stateChanged(int)'), self.createMovieCheckChanged)
        
        rowLayout.addWidget(self.createMovieCheck)
        
        mainLayout.addWidget(row)
        
        # start button
        row = QtGui.QWidget(self)
        rowLayout = QtGui.QHBoxLayout(row)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setAlignment(QtCore.Qt.AlignHCenter)
        
        startRotatorButton = QtGui.QPushButton(QtGui.QIcon(iconPath("loadandsave-icon.svg")), "START")
        startRotatorButton.setStatusTip("Start sequencer")
        startRotatorButton.clicked.connect(self.startRotator)
        
        rowLayout.addWidget(startRotatorButton)
        
        mainLayout.addWidget(row)
    
    def startRotator(self):
        """
        Start the rotator.
        
        """
        log = self.mainWindow.console.write
        log("Running rotator", 0, 0)
        
        # directory
        saveDir = str(self.outputFolder.text())
        if os.path.exists(saveDir):
            if self.overwrite:
                shutil.rmtree(saveDir)
            
            else:
                count = 0
                while os.path.exists(saveDir):
                    count += 1
                    saveDir = "%s.%d" % (str(self.outputFolder.text()), count)
        
        os.mkdir(saveDir)
        
        # file name prefix
        fileprefix = os.path.join(saveDir, str(self.fileprefix.text()))
        
        # send to renderer
        status = self.rendererWindow.renderer.rotateAndSaveImage(self.parent.renderType, self.parent.imageFormat, fileprefix, 
                                                                 1, self.degreesPerRotation, povray=self.parent.povray)
        
        # movie?
        if status:
            print "ERROR: rotate failed"
        
        else:
            # create movie
            if self.createMovie:
                # show wait cursor
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
                
                
                try:
                    saveText = os.path.join(saveDir, "%s%s" % (str(self.fileprefix.text()), "%d"))
                    self.parent.createMovie(saveDir, saveText)
                
                finally:
                    # set cursor to normal
                    QtGui.QApplication.restoreOverrideCursor()
    
    def degPerRotChanged(self, val):
        """
        Degrees per rotation changed.
        
        """
        self.degreesPerRotation = val
    
    def createMovieCheckChanged(self, val):
        """
        Create movie?
        
        """
        if self.createMovieCheck.isChecked():
            if not self.parent.ffmpeg:
                utilities.warnExeNotFound(self.parent, "ffmpeg")
                self.createMovieCheck.setCheckState(0)
                return
            
            self.createMovie = True
        
        else:
            self.createMovie = False

    def overwriteCheckChanged(self, val):
        """
        Overwrite check changed
        
        """
        if self.overwriteCheck.isChecked():
            self.overwrite = 1
        
        else:
            self.overwrite = 0

    def fileprefixChanged(self, text):
        """
        File prefix has changed
        
        """
        self.fileprefixText = str(text)
