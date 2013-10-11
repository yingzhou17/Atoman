
"""
Module for highlighting picked atoms/defects

@author: Chris Scott

"""
import vtk


################################################################################

class AtomHighlighter(object):
    """
    Atom highlighter
    
    """
    def __init__(self, parent, ren, renWinInteract):
        self.parent = parent
        
        self.source = vtk.vtkSphereSource()
        self.mapper = vtk.vtkPolyDataMapper()
        self.actor = vtk.vtkActor()
        
        self.ren = ren
        self.renWinInteract = renWinInteract
        
        self.added = False
    
    def add(self, pos, radius, rgb=[0.62, 0, 0.77]):
        """
        Highlight atom
        
        """
        if self.added:
            self.remove()
        
        # source
        self.source.SetCenter(pos)
        self.source.SetRadius(radius)
        
        # mapper
        self.mapper.SetInput(self.source.GetOutput())
        
        # actor
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetColor(rgb)
        
        # add to renderer
        self.ren.AddActor(self.actor)
        
        # reinit
        self.renWinInteract.ReInitialize()
        
        self.added = True
    
    def remove(self):
        """
        Remove 
        
        """
        if self.added:
            # remove from renderer
            self.ren.RemoveActor(self.actor)
            
            # reinit
            self.renWinInteract.ReInitialize()
            
            self.added = False