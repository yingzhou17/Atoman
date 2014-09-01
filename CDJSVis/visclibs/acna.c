
/*******************************************************************************
 ** Adaptive Common Neighbour Analysis (Stutowski...)
 ** Copyright Chris Scott 2014
 *******************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <gsl/gsl_math.h>
#include "constants.h"
#include "boxeslib.h"
#include "neb_list.h"
#include "utilities.h"
#include "acna.h"


/* function prototypes */
int compare_two_nebs(const void *, const void *);
int analyseAtom(int, struct NeighbourList2 *);
int checkForNeighbourBond(int, int, struct NeighbourList2 *, double);
void setNeighbourBond(unsigned int *, int, int, int);
int findCommonNeighbours(unsigned int *, int, unsigned int *);


/*******************************************************************************
 ** Function that compares two elements in a neighbour list
 *******************************************************************************/
int compare_two_nebs(const void * a, const void * b)
{
    const struct Neighbour *n1 = a;
    const struct Neighbour *n2 = b;
    
    if (n1->separation < n2->separation)
    {
        return -1;
    }
    else if (n1->separation > n2->separation)
    {
        return 1;
    }
    else
    {
        return 0;
    }
}

/*******************************************************************************
 ** perform adaptive common neighbour analysis
 *******************************************************************************/
int adaptiveCommonNeighbourAnalysis(int NVisibleIn, int* visibleAtoms, int posDim, double *pos, int scalarsDim, double *scalars, 
                                    double *minPos, double *maxPos, double *cellDims, int *PBC, int NScalars, double *fullScalars,
                                    double maxBondDistance)
{
    int i, NVisible, index;
    int atomStructure;
    double *visiblePos, approxBoxWidth, maxSep2;
    struct Boxes *boxes;
    struct NeighbourList2 *nebList;
    
    
    printf("DEBUG: begin CLIB\n");
    
/* first we construct neighbour list for each atom, containing indexes and separation */
    
    /* construct visible pos array */
    visiblePos = malloc(3 * NVisibleIn * sizeof(double));
    if (visiblePos == NULL)
    {
        printf("ERROR: could not allocate visiblePos\n");
        exit(50);
    }
    
    for (i=0; i<NVisibleIn; i++)
    {
        index = visibleAtoms[i];
        
        visiblePos[3*i] = pos[3*index];
        visiblePos[3*i+1] = pos[3*index+1];
        visiblePos[3*i+2] = pos[3*index+2];
    }
    
    /* box visible atoms */
    approxBoxWidth = maxBondDistance;
    maxSep2 = maxBondDistance * maxBondDistance;
    boxes = setupBoxes(approxBoxWidth, minPos, maxPos, PBC, cellDims);
    putAtomsInBoxes(NVisibleIn, visiblePos, boxes);
    
    /* create neighbour list */
    nebList = constructNeighbourList2(NVisibleIn, visiblePos, boxes, cellDims, PBC, maxSep2);
    
    /* only required for building neb list */
    freeBoxes(boxes);
    free(visiblePos);
    
    printf("atom 0 has %d nebs\n", nebList[0].neighbourCount);
    
/* now we order the neighbour lists by separation */
    
    /* if less than min neighbours, mark as disordered!!! */
    
    /* sort neighbours by distance */
    for (i = 0; i < NVisibleIn; i++)
    {
//        if (i==0)
//        {
//            int j;
//            
//        	printf("NEBS %d:\n", i);
//            for (j=0; j<nebList[i].neighbourCount; j++)
//            {
//                printf("  VIS %8d; SEP %lf\n", nebList[i].neighbour[j].index, nebList[i].neighbour[j].separation);
//            }
//        }
        
        qsort(nebList[i].neighbour, nebList[i].neighbourCount, sizeof(struct Neighbour), compare_two_nebs);
        
        /* check sorted (debugging...) */
//        if (i==0)
//        {
//            int j;
//        	
//        	printf("NEBS %d:\n", i);
//            for (j=0; j<nebList[i].neighbourCount; j++)
//            {
//                printf("  VIS %8d; SEP %lf\n", nebList[i].neighbour[j].index, nebList[i].neighbour[j].separation);
//            }
//        }
    }
    
/* classify atoms */
    
    for (i = 0; i < NVisibleIn; i++)
    {
    	atomStructure = analyseAtom(i, nebList);
    	scalars[i] = (double) atomStructure;
    	
    	/* debugging */
    	printf("DEBUG: only doing 1st atom for now...\n");
    	break;
    }
    
    
    
    
/* there should be option to only show atoms of specific structure type */
    
    NVisible = 0;
    
    
/* tidy up */
    
    freeNeighbourList2(nebList, NVisibleIn);
    
    printf("DEBUG: end CLIB\n");
    
    return NVisible;
}

/*******************************************************************************
 ** classify atom
 *******************************************************************************/
int analyseAtom(int mainIndex, struct NeighbourList2 *nebList)
{
	int i, j, nn, ok, visInd1, visInd2;
	int numCommonNeighbours;
	double localScaling, localCutoff;
	
	
	/* check we have the minimum number of neighbours */
	if (nebList[mainIndex].neighbourCount < MIN_REQUIRED_NEBS)
		return ATOM_STRUCTURE_DISORDERED;
	
/* first we test for FCC, HCP, Icosohedral (12 1NN) */
	
	/* number of neighbours to test for */
	nn = 12;
	
	/* check enough nebs */
	if (nebList[mainIndex].neighbourCount < nn)
		return ATOM_STRUCTURE_DISORDERED;
	
	/* compute local cutoff */
	localScaling = 0.0;
	for (i = 0; i < nn; i++)
	{
		localScaling += nebList[mainIndex].neighbour[i].separation;
	}
	localScaling /= nn;
	localCutoff = localScaling * (1.0 + M_SQRT2) / 2.0;
	
	/* at this point I feel like we should check that the 12 NN are within localCutoff ????? */
	ok = 1;
	for (i = 0; i < nn; i++)
	{
		if (nebList[mainIndex].neighbour[i].separation > localCutoff)
		{
			ok = 0;
			break;
		}
	}
	
	if (ok)
	{
		int n421 = 0;
		int n422 = 0;
		int n555 = 0;
		unsigned int neighbourArray[MAX_REQUIRED_NEBS] = {0};
		unsigned int commonNeighbours;
		
		/* determine bonding between neighbours, based on local cutoff */
		for (i = 0; i < nn; i++)
		{
			visInd1 = nebList[mainIndex].neighbour[i].index;
			setNeighbourBond(neighbourArray, i, i, 0);
			for (j = i + 1; j < nn; j++)
			{
				visInd2 = nebList[mainIndex].neighbour[j].index;
				setNeighbourBond(neighbourArray, i, j, checkForNeighbourBond(visInd1, visInd2, nebList, localCutoff));
			}
		}
		
		printf("Finding common nebs\n");
		for (i = 0; i < nn; i++)
		{
			/* number of common neighbours */
			numCommonNeighbours = findCommonNeighbours(neighbourArray, i, &commonNeighbours);
			printf("  %d: num common nebs = %d\n", i, numCommonNeighbours);
			if (numCommonNeighbours != 4 && numCommonNeighbours != 5)
				break;
			
			/* number of bonds among common neighbours */
			
			
			
			/* number of bonds in the longest continuous chain */
			
			
		}
		if (n421 == 12) return ATOM_STRUCTURE_FCC;
		else if (n421 == 6 && n422 == 6) return ATOM_STRUCTURE_HCP;
		else if (n555 == 12) return ATOM_STRUCTURE_ICOSAHEDRAL;
	}
	
/* next we test for BCC (8 1NN + 6 2NN) */
	
	
	
	
	return ATOM_STRUCTURE_DISORDERED;
}

/*******************************************************************************
 ** find common neighbours
 *******************************************************************************/
int findCommonNeighbours(unsigned int *neighbourArray, int neighbourIndex, unsigned int *commonNeighbours)
{
#ifdef __GNUC__
	*commonNeighbours = neighbourArray[neighbourIndex];
	
	/* Count the number of bits set in neighbor bit field. */
	return __builtin_popcount(*commonNeighbours); // GNU g++ specific
#else
	unsigned int v;
	
	*commonNeighbours = neighbourArray[neighbourIndex];
	
	/* Count the number of bits set in neighbor bit field. */
	v = *commonNeighbours - ((*commonNeighbours >> 1) & 0x55555555);
	v = (v & 0x33333333) + ((v >> 2) & 0x33333333);
	return ((v + (v >> 4) & 0xF0F0F0F) * 0x1010101) >> 24;
#endif
}

/*******************************************************************************
 ** check if two neighbours are bonded
 *******************************************************************************/
int checkForNeighbourBond(int visInd1, int visInd2, struct NeighbourList2 *nebList, double cutoff)
{
	int i, bonded;
	
	
//	printf("Checking if bonded %d - %d\n", visInd1, visInd2);
	
	bonded = 0;
	for (i = 0; i < nebList[visInd1].neighbourCount; i++)
	{
		if (nebList[visInd1].neighbour[i].index == visInd2 && nebList[visInd1].neighbour[i].separation <= cutoff)
		{
//			printf("  bonded: sep = %lf (cut = %lf)\n", nebList[visInd1].neighbour[i].separation, cutoff);
			
			bonded = 1;
			break;
		}
	}
	
	return bonded;
}

/*******************************************************************************
 ** set neighbour bond
 *******************************************************************************/
void setNeighbourBond(unsigned int *neighbourArray, int index1, int index2, int bonded)
{
	if (bonded)
	{
		neighbourArray[index1] |= (1<<index2);
		neighbourArray[index2] |= (1<<index1);
	}
	else
	{
		neighbourArray[index1] &= ~(1<<index2);
		neighbourArray[index2] &= ~(1<<index1);
	}
}