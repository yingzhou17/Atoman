
"""
Base class for renderers.

"""
from __future__ import unicode_literals


class BaseRenderer(object):
    """
    Base class for renderers.
    
    """
    def __init__(self):
        self._data = {}
        self._actor = None
    
    def getActor(self):
        """Return the actor."""
        return self._actor
    
    def writePovray(self, filename):
        """Write POV-Ray data to file."""
        pass
