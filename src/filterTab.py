
"""
The filter tab for the main toolbar

@author: Chris Scott

"""

import os
import sys

from PyQt4 import QtGui, QtCore, Qt

from utilities import iconPath
from genericForm import GenericForm
import resources
import filtering        
        
        

################################################################################
class List(QtGui.QListWidget):
    def __init__(self, parent):
        super(List, self).__init__(parent)
        
        self.parent = parent
        
        self.setDragDropMode(self.InternalMove)
        self.installEventFilter(self)

    def eventFilter(self, sender, event):
        if event.type() == Qt.QEvent.ChildRemoved:
            self.on_order_changed()
        return False

    def on_order_changed(self):
        pass


################################################################################
class FilterList(QtGui.QWidget):
    def __init__(self, parent, mainToolbar, mainWindow, tab, width, height=150):
        super(FilterList, self).__init__(parent)
        
        self.filterTab = parent
        self.mainToolbar = mainToolbar
        self.mainWindow = mainWindow
        self.tab = tab
        self.tabWidth = width
        self.tabHeight = height
        
        # all available filters
        self.allFilters = ["Specie", "Displacement", "Crop"]
        
        # current selected filters
        self.currentFilters = []
        
        # settings (windows) for current filters
        self.currentSettings = []
        
        self.visible = 1
        
        # the filterer (does the filtering)
        self.filterer = filtering.Filterer(self)
        
        # layout
        self.filterListLayout = QtGui.QVBoxLayout(self)
        
        # add the top set of buttons
        
        # visibility of filter list
        self.visibleButton = QtGui.QPushButton(QtGui.QIcon(iconPath("eye-ava.svg")), "")
        self.visibleButton.setFixedWidth(35)
        self.visibleButton.setStatusTip("Visible")
        self.visibleButton.setCheckable(1)
        self.visibleButton.setChecked(0)
        self.connect(self.visibleButton, QtCore.SIGNAL('clicked()'), self.visibilityChanged)
        
        # trash the list
        trashButton = QtGui.QPushButton(QtGui.QIcon(iconPath("edit-delete.svg")), "")
        trashButton.setStatusTip("Delete filter list")
        trashButton.setFixedWidth(35)
        self.connect(trashButton, QtCore.SIGNAL('clicked()'), self.filterTab.removeFilterList)
        
        # show scalar bar
        #TODO: need to think about this - how to know which filter the scalar bar refers to etc
        self.scalarBarButton = QtGui.QPushButton(QtGui.QIcon(iconPath("preferences-desktop-locale.svg")), "")
        self.scalarBarButton.setFixedWidth(35)
        self.scalarBarButton.setStatusTip("Show scalar bar")
        self.scalarBarButton.setCheckable(1)
        self.scalarBarButton.setChecked(0)
        
        # set up the row of buttons
        row1 = QtGui.QWidget()
        rowLayout = QtGui.QHBoxLayout(row1)
        rowLayout.setAlignment(QtCore.Qt.AlignLeft)
        rowLayout.addWidget(self.visibleButton)
        rowLayout.addWidget(trashButton)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        
        row2 = QtGui.QWidget()
        rowLayout = QtGui.QHBoxLayout(row2)
        rowLayout.setAlignment(QtCore.Qt.AlignRight)
        rowLayout.addWidget(self.scalarBarButton)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        
        row3 = QtGui.QWidget()
        rowLayout = QtGui.QHBoxLayout(row3)
        rowLayout.addWidget(row1)
        rowLayout.addWidget(row2)
#        rowLayout.setSpacing(0)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        
        self.filterListLayout.addWidget(row3)
        
        # Now add the list widget
        self.listItems = List(self)
        self.listItems.setFixedHeight(self.tabHeight)
        
        self.connect(self.listItems, QtCore.SIGNAL('itemDoubleClicked(QListWidgetItem*)'), self.openFilterInfo)
        
        self.filterListLayout.addWidget(self.listItems)
        
        # add more buttons
        addFilter = QtGui.QPushButton(QtGui.QIcon(iconPath("list-add.svg")), "")
        addFilter.setStatusTip("Add new filter")
        self.connect(addFilter, QtCore.SIGNAL('clicked()'), self.addFilter)
        
        removeFilter = QtGui.QPushButton(QtGui.QIcon(iconPath("list-remove.svg")), "")
        removeFilter.setStatusTip("Remove filter")
        self.connect(removeFilter, QtCore.SIGNAL('clicked()'), self.removeFilter)
        
        moveUp = QtGui.QPushButton(QtGui.QIcon(iconPath("go-up.svg")), "")
        moveUp.setStatusTip("Move up")
        self.connect(moveUp, QtCore.SIGNAL('clicked()'), self.moveFilterUpInList)
        
        moveDown = QtGui.QPushButton(QtGui.QIcon(iconPath("go-down.svg")), "")
        moveDown.setStatusTip("Move down")
        self.connect(moveDown, QtCore.SIGNAL('clicked()'), self.moveFilterDownInList)
        
        clearList = QtGui.QPushButton(QtGui.QIcon(iconPath("edit-clear.svg")), "")
        clearList.setStatusTip("Clear current filter list")
        self.connect(clearList, QtCore.SIGNAL('clicked()'), self.clearList)
        
        applyList = QtGui.QPushButton(QtGui.QIcon(iconPath("view-refresh.svg")), "")
        applyList.setStatusTip("Apply current filter list")
        self.connect(applyList, QtCore.SIGNAL('clicked()'), self.applyList)
        
        buttonWidget = QtGui.QWidget()
        buttonLayout = QtGui.QHBoxLayout(buttonWidget)
        buttonLayout.setSpacing(0)
        buttonLayout.setContentsMargins(0, 0, 0, 0)
        buttonLayout.setAlignment(QtCore.Qt.AlignTop)
        
        buttonLayout.addWidget(addFilter)
        buttonLayout.addWidget(removeFilter)
        buttonLayout.addWidget(moveUp)
        buttonLayout.addWidget(moveDown)
        buttonLayout.addWidget(clearList)
        buttonLayout.addWidget(applyList)
        
        self.filterListLayout.addWidget(buttonWidget)
        
        
        # add other option like colour by height etc
        self.extraOptionsList = QtGui.QListWidget(self)
        self.connect(self.extraOptionsList, QtCore.SIGNAL('itemClicked(QListWidgetItem*)'), self.openOptionsWindow)
        self.extraOptionsList.setFixedHeight(100)
        self.extraOptionsList.addItem("Colouring: ...")
        self.extraOptionsList.addItem("Screen info: ...")
        
        self.filterListLayout.addWidget(self.extraOptionsList)
        
        
        
    def openFilterInfo(self):
        """
        Get info about filter
        
        """
        print "OPEN FILTER SETTING WINDOW"
    
    def openOptionsWindow(self):
        """
        Open additional options window
        
        """
        print "NOT IMPLEMENTED YET"
    
    def applyList(self):
        """
        Move filter down in list
        
        """
        # remove actors
        
        # apply filters
        
        # add actors
        
        # leave other lists the same!
        
        
        pass
    
    def clearList(self):
        """
        Move filter down in list
        
        """
        self.listItems.clear()
        
        while len(self.currentFilters):
            self.currentFilters.pop()
        
        while len(self.currentSettings):
            self.currentSettings.pop()
    
    def moveFilterDownInList(self):
        """
        Move filter down in list
        
        """
        print "MOVE UP"
    
    def moveFilterUpInList(self):
        """
        Move filter up in list
        
        """
        pass
    
    def addFilter(self):
        """
        Add new filter
        
        """
        # first determine what filter is to be added
        filter, ok = QtGui.QInputDialog.getItem(self, "Add filter", "Select filter:", self.allFilters, editable=False)
        
        if ok:
            print "SELECTED FILTER", filter
            
            if filter not in self.currentFilters:
                self.currentFilters.append(str(filter))
                self.listItems.addItem(filter)
                
                # select the newly added filter
                self.listItems.item(len(self.listItems)-1).setSelected(1)
                
                # create option form? like console window (but blocking?)? and open it
                
    
    def removeFilter(self):
        """
        Remove new filter
        
        """
        # find which one is selected
        row = self.listItems.currentRow()
        item = self.listItems.currentItem()
        
        # remove it from lists
        self.listItems.takeItem(row)
        self.currentFilters.pop(row)
    
    def visibilityChanged(self):
        """
        Update visibility of filter list
        
        """
        if self.visibleButton.isChecked():
            self.visibleButton.setIcon(QtGui.QIcon(iconPath("eye-close-ava.svg")))
            self.visible = 0
        else:
            self.visibleButton.setIcon(QtGui.QIcon(iconPath("eye-ava.svg")))
            self.visible = 1


################################################################################
class FilterTab(QtGui.QWidget):
    def __init__(self, parent, mainWindow, width):
        super(FilterTab, self).__init__(parent)
        
        self.mainToolbar = parent
        self.mainWindow = mainWindow
        self.toolbarWidth = width
        
        self.filterListCount = 1
        self.filterLists = []
        
        # layout
        filterTabLayout = QtGui.QVBoxLayout(self)
        filterTabLayout.setContentsMargins(0, 0, 0, 0)
        filterTabLayout.setSpacing(0)
        filterTabLayout.setAlignment(QtCore.Qt.AlignTop)
        
        row = QtGui.QWidget()
        rowLayout = QtGui.QHBoxLayout(row)
        rowLayout.setAlignment(QtCore.Qt.AlignTop)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setSpacing(0)
        
        #----- buttons for new/trash filter list
        runAll = QtGui.QPushButton(QtGui.QIcon(iconPath('view-refresh-all.svg')),'Apply lists')
        runAll.setStatusTip("Apply all filter lists")
        self.connect(runAll, QtCore.SIGNAL('clicked()'), self.runAllFilterLists)
        add = QtGui.QPushButton(QtGui.QIcon(iconPath('tab-new.svg')),'New list')
        add.setStatusTip("New filter list")
        self.connect(add, QtCore.SIGNAL('clicked()'), self.addFilterList)
        clear = QtGui.QPushButton(QtGui.QIcon(iconPath('edit-delete.svg')),'Clear lists')
        clear.setStatusTip("Clear all filter lists")
        self.connect(clear, QtCore.SIGNAL('clicked()'), self.clearAllFilterLists)
        
        rowLayout.addWidget(add)
        rowLayout.addWidget(clear)
        rowLayout.addWidget(runAll)
        
        filterTabLayout.addWidget(row)
        
        #----- add tab bar for filter lists
        self.filterTabBar = QtGui.QTabWidget(self)
        self.filterTabBar.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.connect(self.filterTabBar, QtCore.SIGNAL('currentChanged(int)'), self.filterTabBarChanged)
        filterTabLayout.addWidget(self.filterTabBar)
        
        # widget to hold filter list
        self.filterListWidget = QtGui.QWidget()
        self.filterListLayout = QtGui.QVBoxLayout(self.filterListWidget)
        self.filterListLayout.setContentsMargins(0, 0, 0, 0)
        
        # add list
        list1 = FilterList(self, self.mainToolbar, self.mainWindow, self.filterListCount, self.toolbarWidth)
        self.filterListLayout.addWidget(list1)
        self.filterLists.append(list1)
        
        # add to tab bar
        self.filterTabBar.addTab(self.filterListWidget, str(self.filterListCount))
        
    def runAllFilterLists(self):
        """
        Run all the filter lists.
        
        """
        print "RUNNING ALL FILTER LISTS"
        for filterList in self.filterLists:
            filterList.filterer.runFilter()
        
        self.mainWindow.renderer.render()
        

    def addFilterList(self):
        pass
    
    def clearAllFilterLists(self):
        pass

    def filterTabBarChanged(self, val):
        # guess need to handle addition and removal of tabs here
        pass
    
    def removeFilterList(self):
        pass



