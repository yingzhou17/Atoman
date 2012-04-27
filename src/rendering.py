
"""
Module for rendering

@author: Chris Scott

"""

import os
import sys
import math

import vtk


################################################################################
def setRes(num):
    #res = 15.84 * (0.99999**natoms)
    #if(LowResVar.get()=="LowResOff"):
    if(num==0):
        res = 100
    else:
        #if(ResVar.get()=="LowResOn"):
        #    
        #    res = -1.0361*math.log(num,e) + 14.051
        #    #res = round(res,0)
        #    #res = 176*(num**-0.36)
        #    res = int(res)
        #    
        #elif(ResVar.get()=="HighResOn"):
        #    
        #    res = -2.91*math.log(num,e) + 35
        #    res = round(res,0)
        #    res = 370*(num**-0.36)
        #    res = int(res)
        #    
        #else:
        
        res = -2.91*math.log(num,2.7) + 35
        res = round(res,0)
        res = 170*(num**-0.36)
        res = int(res)    
    
#    print "RES = ",res,num    
    return res


################################################################################
class CellOutline:
    def __init__(self, ren):
        
        self.ren = ren
        self.source = vtk.vtkOutlineSource()
        self.mapper = vtk.vtkPolyDataMapper()
        self.actor = vtk.vtkActor()
        self.visible = 0
    
    def add(self, a, b):
        """
        Add the lattice cell.
        
        """
        # first remove if already visible
        if self.visible:
            self.remove()
        
        # now add it
        self.source.SetBounds(a[0], b[0], a[1], b[1], a[2], b[2])
        
        self.mapper.SetInput(self.source.GetOutput())
        
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetColor(0, 0, 0)
        
        self.ren.AddActor(self.actor)
        
        self.visible = 1
    
    def remove(self):
        """
        Remove the cell outline.
        
        """
        self.ren.RemoveActor(self.actor)
        
        self.visible = 0


################################################################################
class Renderer:
    def __init__(self, mainWindow):
        
        self.mainWindow = mainWindow
        self.ren = self.mainWindow.VTKRen
        self.renWinInteract = self.mainWindow.VTKWidget
        
        self.log = self.mainWindow.console.write
        
        # is the interactor initialised
        self.init = 0
        
        # setup stuff
        self.camera = self.ren.GetActiveCamera()
        
        # lattice frame
        self.latticeFrame = CellOutline(self.ren)
        
        
    def reinit(self):
        """
        Reinitialise.
        
        """
        if self.init:
            self.renWinInteract.ReInitialize()
        else:
            self.renWinInteract.Initialize()
            self.init = 1
    
    def postRefRender(self):
        """
        Render post read reference file.
        
        """
        dims = self.mainWindow.refState.cellDims
        
        # add lattice frame
        self.latticeFrame.add([0, 0, 0], dims)
        
        # set camera to cell
        self.setCameraToCell()
        
        # reinitialise
        self.reinit()
    
    def setCameraToCell(self):
        """
        Point the camera at the centre of the cell.
        
        """
        dims = self.mainWindow.refState.cellDims
        
        # set camera to lattice
        campos = [0]*3
        if dims[1] > dims[2]:
            campos[0] = -3.0 * dims[1]
        else:
            campos[0] = -3.0 * dims[2]
        campos[1] = 0.5 * dims[1]
        campos[2] = 0.5 * dims[2]
        
        focpnt = [0]*3
        focpnt[0] = 0.5 * dims[0]
        focpnt[1] = 0.5 * dims[1]
        focpnt[2] = 0.5 * dims[2]
        
        self.camera.SetFocalPoint(focpnt)
        self.camera.SetPosition(campos)
    
    def setCameraToCOM(self):
        """
        Point the camera at the centre of mass.
        
        """
        pass
    
    def writeCameraSettings(self):
        """
        Write the camera settings to file.
        So can be loaded back in future
        OPTION TO WRITE TO TMPDIR IF WANT!!!
        
        """
        pass
        
    def addAxes(self):
        """
        Add the axis label
        
        """
        pass
    
    def removeAxes(self):
        """
        Remove the axis label
        
        """
        pass
    
    def removeAllActors(self):
        """
        Remove all actors
        
        """
        filterLists = self.getFilterLists()
        
        for filterList in filterLists:
            filterList.filterer.removeActors()

    def removeActor(self, actor):
        """
        Remove actor
        
        """
        self.ren.RemoveActor(actor)
        
    def removeActorList(self, actorList):
        """
        Remove list of actors
        
        """
        pass
    
    def getFilterLists(self):
        """
        Return filter lists
        
        """
        return self.mainWindow.mainToolbar.filterPage.filterLists
    
    def render(self):
        """
        Render.
        
        """
        print "RENDERING"
        self.removeAllActors()
        
        filterLists = self.getFilterLists()
        count = 0
        for filterList in filterLists:
            print "RENDERING LIST", count
            count += 1
            
            filterList.addActors()


################################################################################
def setupLUT(specieList, specieRGB):
    """
    Setup the colour look up table
    
    """
    NSpecies = len(specieList)
    
    lut = vtk.vtkLookupTable()
    lut.SetNumberOfColors(NSpecies)
    lut.SetNumberOfTableValues(NSpecies)
    lut.SetTableRange(0, NSpecies - 1)
    lut.SetRange(0, NSpecies - 1)
    
    for i in xrange(NSpecies):
        lut.SetTableValue(i, specieRGB[i][0], specieRGB[i][1], specieRGB[i][2], 1.0)
    
    return lut

################################################################################
def getActorsForFilteredSystem(visibleAtoms, mainWindow, actorsCollection):
    """
    Make the actors for the filtered system
    
    """
    NVisible = len(visibleAtoms)
    
    # resolution
    res = setRes(NVisible)
    
    lattice = mainWindow.inputState
    
    # make LUT
    lut = setupLUT(lattice.specieList, lattice.specieRGB)
    
    NSpecies = len(lattice.specieList)
    
    atomPointsList = []
    atomScalarsList = []
    for i in xrange(NSpecies):
        atomPointsList.append(vtk.vtkPoints())
        atomScalarsList.append(vtk.vtkFloatArray())
        
    # loop over atoms, setting points
    pos = lattice.pos
    spec = lattice.specie
    for i in xrange(NVisible):
        index = visibleAtoms[i]
        specInd = spec[index]
        
        atomPointsList[specInd].InsertNextPoint(pos[3*index], pos[3*index+1], pos[3*index+2])
        atomScalarsList[specInd].InsertNextValue(specInd)
        
    # now loop over species, making actors
    for i in xrange(NSpecies):
        
        atomsPolyData = vtk.vtkPolyData()
        atomsPolyData.SetPoints(atomPointsList[i])
        atomsPolyData.GetPointData().SetScalars(atomScalarsList[i])
        
        atomsGlyphSource = vtk.vtkSphereSource()
        atomsGlyphSource.SetRadius(lattice.specieCovalentRadius[i])
        atomsGlyphSource.SetPhiResolution(res)
        atomsGlyphSource.SetThetaResolution(res)
        
        atomsGlyph = vtk.vtkGlyph3D()
        atomsGlyph.SetSource(atomsGlyphSource.GetOutput())
        atomsGlyph.SetInput(atomsPolyData)
        atomsGlyph.SetScaleFactor(1.0)
        atomsGlyph.SetScaleModeToDataScalingOff()
        
        atomsMapper = vtk.vtkPolyDataMapper()
        atomsMapper.SetInput(atomsGlyph.GetOutput())
        atomsMapper.SetLookupTable(lut)
        atomsMapper.SetScalarRange(0, NSpecies - 1)
        
        atomsActor = vtk.vtkActor()
        atomsActor.SetMapper(atomsMapper)
        
        actorsCollection.AddItem(atomsActor)


################################################################################
def getActorsForFilteredDefects(interstitials, vacancies, antisites, onAntisites, mainWindow, actorsCollection):
    
    NInt = len(interstitials)
    NVac = len(vacancies)
    NAnt = len(antisites)
    NDef = NInt + NVac + NAnt
    
    # resolution
    res = setRes(NDef)
    
    inputLattice = mainWindow.inputState
    refLattice = mainWindow.refState
    
    #----------------------------------------#
    # interstitials first
    #----------------------------------------#
    NSpecies = len(inputLattice.specieList)
    intPointsList = []
    intScalarsList = []
    for i in xrange(NSpecies):
        intPointsList.append(vtk.vtkPoints())
        intScalarsList.append(vtk.vtkFloatArray())
    
    # make LUT
    lut = setupLUT(inputLattice.specieList, inputLattice.specieRGB)
    
    # loop over interstitials, settings points
    pos = inputLattice.pos
    spec = inputLattice.specie
    for i in xrange(NInt):
        index = interstitials[i]
        specInd = spec[index]
        
        intPointsList[specInd].InsertNextPoint(pos[3*index], pos[3*index+1], pos[3*index+2])
        intScalarsList[specInd].InsertNextValue(specInd)
    
    # now loop over species making actors
    for i in xrange(NSpecies):
        
        intsPolyData = vtk.vtkPolyData()
        intsPolyData.SetPoints(intPointsList[i])
        intsPolyData.GetPointData().SetScalars(intScalarsList[i])
        
        intsGlyphSource = vtk.vtkSphereSource()
        intsGlyphSource.SetRadius(inputLattice.specieCovalentRadius[i])
        intsGlyphSource.SetPhiResolution(res)
        intsGlyphSource.SetThetaResolution(res)
        
        intsGlyph = vtk.vtkGlyph3D()
        intsGlyph.SetSource(intsGlyphSource.GetOutput())
        intsGlyph.SetInput(intsPolyData)
        intsGlyph.SetScaleFactor(1.0)
        intsGlyph.SetScaleModeToDataScalingOff()
        
        intsMapper = vtk.vtkPolyDataMapper()
        intsMapper.SetInput(intsGlyph.GetOutput())
        intsMapper.SetLookupTable(lut)
        intsMapper.SetScalarRange(0, NSpecies - 1)
        
        intsActor = vtk.vtkActor()
        intsActor.SetMapper(intsMapper)
        
        actorsCollection.AddItem(intsActor)
        
    #----------------------------------------#
    # antisites occupying atom
    #----------------------------------------#
    NSpecies = len(inputLattice.specieList)
    intPointsList = []
    intScalarsList = []
    for i in xrange(NSpecies):
        intPointsList.append(vtk.vtkPoints())
        intScalarsList.append(vtk.vtkFloatArray())
    
    # make LUT
    lut = setupLUT(refLattice.specieList, refLattice.specieRGB)
    
    # loop over interstitials, settings points
    pos = refLattice.pos
    spec = inputLattice.specie
    for i in xrange(NAnt):
        index = onAntisites[i]
        specInd = spec[index]
        intScalarsList[specInd].InsertNextValue(specInd)
        
        index = antisites[i]
        intPointsList[specInd].InsertNextPoint(pos[3*index], pos[3*index+1], pos[3*index+2])
    
    # now loop over species making actors
    for i in xrange(NSpecies):
        
        intsPolyData = vtk.vtkPolyData()
        intsPolyData.SetPoints(intPointsList[i])
        intsPolyData.GetPointData().SetScalars(intScalarsList[i])
        
        intsGlyphSource = vtk.vtkSphereSource()
        intsGlyphSource.SetRadius(refLattice.specieCovalentRadius[i])
        intsGlyphSource.SetPhiResolution(res)
        intsGlyphSource.SetThetaResolution(res)
        
        intsGlyph = vtk.vtkGlyph3D()
        intsGlyph.SetSource(intsGlyphSource.GetOutput())
        intsGlyph.SetInput(intsPolyData)
        intsGlyph.SetScaleFactor(1.0)
        intsGlyph.SetScaleModeToDataScalingOff()
        
        intsMapper = vtk.vtkPolyDataMapper()
        intsMapper.SetInput(intsGlyph.GetOutput())
        intsMapper.SetLookupTable(lut)
        intsMapper.SetScalarRange(0, NSpecies - 1)
        
        intsActor = vtk.vtkActor()
        intsActor.SetMapper(intsMapper)
        
        actorsCollection.AddItem(intsActor)
    
    #----------------------------------------#
    # vacancies
    #----------------------------------------#
    NSpecies = len(refLattice.specieList)
    intPointsList = []
    intScalarsList = []
    for i in xrange(NSpecies):
        intPointsList.append(vtk.vtkPoints())
        intScalarsList.append(vtk.vtkFloatArray())
    
    # make LUT
    lut = setupLUT(refLattice.specieList, refLattice.specieRGB)
    
    # loop over interstitials, settings points
    pos = refLattice.pos
    spec = refLattice.specie
    for i in xrange(NVac):
        index = vacancies[i]
        specInd = spec[index]
        
        intPointsList[specInd].InsertNextPoint(pos[3*index], pos[3*index+1], pos[3*index+2])
        intScalarsList[specInd].InsertNextValue(specInd)
    
    # now loop over species making actors
    for i in xrange(NSpecies):
        
        vacsPolyData = vtk.vtkPolyData()
        vacsPolyData.SetPoints(intPointsList[i])
        vacsPolyData.GetPointData().SetScalars(intScalarsList[i])
        
        vacsGlyphSource = vtk.vtkCubeSource()
        vacsGlyphSource.SetXLength(1.5 * refLattice.specieCovalentRadius[i])
        vacsGlyphSource.SetYLength(1.5 * refLattice.specieCovalentRadius[i])
        vacsGlyphSource.SetZLength(1.5 * refLattice.specieCovalentRadius[i])
        
        vacsGlyph = vtk.vtkGlyph3D()
        vacsGlyph.SetSource(vacsGlyphSource.GetOutput())
        vacsGlyph.SetInput(vacsPolyData)
        vacsGlyph.SetScaleFactor(1.0)
        vacsGlyph.SetScaleModeToDataScalingOff()
        
        vacsMapper = vtk.vtkPolyDataMapper()
        vacsMapper.SetInput(vacsGlyph.GetOutput())
        vacsMapper.SetLookupTable(lut)
        vacsMapper.SetScalarRange(0, NSpecies - 1)
        
        vacsActor = vtk.vtkActor()
        vacsActor.SetMapper(vacsMapper)
        vacsActor.GetProperty().SetSpecular(0.4)
        vacsActor.GetProperty().SetSpecularPower(10)
        vacsActor.GetProperty().SetOpacity(1.0)
        
        actorsCollection.AddItem(vacsActor)
    
    #----------------------------------------#
    # antisites
    #----------------------------------------#
    NSpecies = len(refLattice.specieList)
    intPointsList = []
    intScalarsList = []
    for i in xrange(NSpecies):
        intPointsList.append(vtk.vtkPoints())
        intScalarsList.append(vtk.vtkFloatArray())
    
    # make LUT
    lut = setupLUT(refLattice.specieList, refLattice.specieRGB)
    
    # loop over interstitials, settings points
    pos = refLattice.pos
    spec = refLattice.specie
    for i in xrange(NAnt):
        index = antisites[i]
        specInd = spec[index]
        
        intPointsList[specInd].InsertNextPoint(pos[3*index], pos[3*index+1], pos[3*index+2])
        intScalarsList[specInd].InsertNextValue(specInd)
    
    # now loop over species making actors
    for i in xrange(NSpecies):
        
        vacsPolyData = vtk.vtkPolyData()
        vacsPolyData.SetPoints(intPointsList[i])
        vacsPolyData.GetPointData().SetScalars(intScalarsList[i])
        
        cubeGlyphSource = vtk.vtkCubeSource()
        cubeGlyphSource.SetXLength(2.0 * refLattice.specieCovalentRadius[i])
        cubeGlyphSource.SetYLength(2.0 * refLattice.specieCovalentRadius[i])
        cubeGlyphSource.SetZLength(2.0 * refLattice.specieCovalentRadius[i])
        edges = vtk.vtkExtractEdges()
        edges.SetInputConnection(cubeGlyphSource.GetOutputPort())
        vacsGlyphSource = vtk.vtkTubeFilter()
        vacsGlyphSource.SetInputConnection(edges.GetOutputPort())
        vacsGlyphSource.SetRadius(0.1)
        vacsGlyphSource.SetNumberOfSides(5)
        vacsGlyphSource.UseDefaultNormalOn()
        vacsGlyphSource.SetDefaultNormal(.577, .577, .577)
        
        vacsGlyph = vtk.vtkGlyph3D()
        vacsGlyph.SetSource(vacsGlyphSource.GetOutput())
        vacsGlyph.SetInput(vacsPolyData)
        vacsGlyph.SetScaleFactor(1.0)
        vacsGlyph.SetScaleModeToDataScalingOff()
        
        vacsMapper = vtk.vtkPolyDataMapper()
        vacsMapper.SetInput(vacsGlyph.GetOutput())
        vacsMapper.SetLookupTable(lut)
        vacsMapper.SetScalarRange(0, NSpecies - 1)
        
        vacsActor = vtk.vtkActor()
        vacsActor.SetMapper(vacsMapper)
        
        actorsCollection.AddItem(vacsActor)


################################################################################
def makeTriangle(indexes):
    """
    Make a triangle given indexes in points array
    
    """
    
    inda = indexes[0]
    indb = indexes[1]
    indc = indexes[2]
    
    triangle = vtk.vtkTriangle()
    triangle.GetPointIds().SetId(0,inda)
    triangle.GetPointIds().SetId(1,indb)
    triangle.GetPointIds().SetId(2,indc)
    
    return triangle


################################################################################
def getActorsForHullFacets(facets, pos, mainWindow, actorsCollection):
    """
    Render convex hull facets
    
    """
    
    # probably want to pass some settings through too eg colour, opacity etc
    
    
    points = vtk.vtkPoints()
    for i in xrange(len(pos) / 3):
        points.InsertNextPoint(pos[3*i], pos[3*i+1], pos[3*i+2])
    
    # create triangles
    triangles = vtk.vtkCellArray()
    for i in xrange(len(facets)):
        triangle = makeTriangle(facets[i])
        triangles.InsertNextCell(triangle)
    
    # polydata object
    trianglePolyData = vtk.vtkPolyData()
    trianglePolyData.SetPoints(points)
    trianglePolyData.SetPolys(triangles)
    
    # mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInput(trianglePolyData)
    
    # actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(0.5)
    actor.GetProperty().SetColor(0,0,1)
    
    actorsCollection.AddItem(actor)
    
    