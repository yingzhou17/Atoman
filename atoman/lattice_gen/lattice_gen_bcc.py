
"""
Generate BCC lattice

@author: Chris Scott

"""
from __future__ import absolute_import
from __future__ import unicode_literals
import logging

import numpy as np

from ..system.lattice import Lattice
from . import _lattice_gen_bcc
from six.moves import range

################################################################################

class Args(object):
    """
    NCells: 3-tuple containing number of unit cells in each direction (default=(10,10,10))
    percGa: atomic percent Ga (max 25) (default=5)
    a0: lattice constant (default=4.64)
    f: output filename
    x,y,z: PBCs in each direction (default=True)
    quiet: suppress stdout
    
    """
    def __init__(self, sym="Fe", NCells=[10,10,10], a0=2.87, pbcx=True, pbcy=True, pbcz=True, quiet=False):
        self.sym = sym
        self.NCells = NCells
        self.a0 = a0
        self.pbcx = pbcx
        self.pbcy = pbcy
        self.pbcz = pbcz
        self.quiet = quiet

################################################################################

class BCCLatticeGenerator(object):
    """
    BCC lattice generator.
    
    """
    def __init__(self, log=None):
        pass
    
    def generateLattice(self, args):
        """
        Generate the lattice.
        
        """
        logger = logging.getLogger(__name__)
        logger.info("Generating BCC lattice")
        
        # numpy arrays
        numCells = np.asarray(args.NCells, dtype=np.int32)
        pbc = np.asarray([args.pbcx, args.pbcy, args.pbcz], dtype=np.int32)
        
        # lattice constant
        a0 = args.a0
        
        # lattice dimensions
        dims = [a0 * numCells[0], a0 * numCells[1], a0 * numCells[2]]
        
        # generate lattice data
        NAtoms, specie, pos, charge = _lattice_gen_bcc.generateBCCLattice(numCells, pbc, a0)
        
        # lattice structure
        lattice = Lattice()
        
        # set up correctly for this number of atoms
        lattice.reset(NAtoms)
        
        # set dimensions
        lattice.setDims(dims)
        
        # set data
        lattice.addSpecie(args.sym, count=NAtoms)
        lattice.specie = specie
        lattice.pos = pos
        lattice.charge = charge
        lattice.NAtoms = NAtoms
        
        # min/max pos
        for i in range(3):
            lattice.minPos[i] = np.min(lattice.pos[i::3])
            lattice.maxPos[i] = np.max(lattice.pos[i::3])
        
        # atom ID
        lattice.atomID = np.arange(1, lattice.NAtoms + 1, dtype=np.int32)
        
        # periodic boundaries
        lattice.PBC[0] = int(args.pbcx)
        lattice.PBC[1] = int(args.pbcy)
        lattice.PBC[2] = int(args.pbcz)
        
        logger.info("  Number of atoms: %d", NAtoms)
        logger.info("  Dimensions: %s", str(dims))
        
        return 0, lattice
