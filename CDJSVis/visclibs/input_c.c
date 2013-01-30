
/*******************************************************************************
 ** Copyright Chris Scott 2011
 ** IO routines written in C to improve performance
 *******************************************************************************/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <errno.h>


int specieIndex(char*, int, char*);


/*******************************************************************************
 * Update specie list and counter
 *******************************************************************************/
int specieIndex(char* sym, int NSpecies, char* specieList)
{
    int index, j, comp;
    
    
    index = NSpecies;
    for (j=0; j<NSpecies; j++)
    {
        comp = strcmp( &specieList[3*j], &sym[0] );
        if (comp == 0)
        {
            index = j;
            
            break;
        }
    }
    
    return index;
}


/*******************************************************************************
** read animation-reference file
*******************************************************************************/
void readRef( char* file, int specieDim, int* specie, int posDim, double* pos, int chargeDim, double* charge, 
              int KEDim, double* KE, int PEDim, double* PE, int forceDim, double* force, int speclistDim, 
              char* specieList_c, int specCountDim, int* specieCount_c, int maxPosDim, double* maxPos, int minPosDim, 
              double* minPos )
{
    int i, j, NAtoms, specInd;
    FILE *INFILE;
    double xdim, ydim, zdim;
    char symtemp[3];
    char* specieList;
    double xpos, ypos, zpos;
    double xforce, yforce, zforce;
    int id, index;
    double ketemp, petemp, chargetemp;
    int NSpecies, comp, specieMatch;
    
    
    INFILE = fopen( file, "r" );
    if (INFILE == NULL)
    {
        printf("ERROR: could not open file: %s\n", file);
        printf("       reason: %s\n", strerror(errno));
        exit(35);
    }
    
    fscanf( INFILE, "%d", &NAtoms );
    
    fscanf(INFILE, "%lf%lf%lf", &xdim, &ydim, &zdim);
    
    specieList = malloc( 3 * sizeof(char) );
    
    minPos[0] = 1000000;
    minPos[1] = 1000000;
    minPos[2] = 1000000;
    maxPos[0] = -1000000;
    maxPos[1] = -1000000;
    maxPos[2] = -1000000;
    NSpecies = 0;
    for (i=0; i<NAtoms; i++)
    {
        fscanf(INFILE, "%d%s%lf%lf%lf%lf%lf%lf%lf%lf%lf", &id, symtemp, &xpos, &ypos, &zpos, &ketemp, &petemp, &xforce, &yforce, &zforce, &chargetemp);
        
        /* index for storage is (id-1) */
        index = id - 1;
        
        pos[3*index] = xpos;
        pos[3*index+1] = ypos;
        pos[3*index+2] = zpos;
        
        KE[index] = ketemp;
        PE[index] = petemp;
        
//        force[3*index] = xforce;
//        force[3*index+1] = yforce;
//        force[3*index+2] = zforce;
        
        charge[index] = chargetemp;
        
        /* find specie index */
        specInd = specieIndex(symtemp, NSpecies, specieList);
        
        specie[i] = specInd;
        
        if (specInd == NSpecies)
        {
            /* new specie */
            specieList = realloc( specieList, 3 * (NSpecies+1) * sizeof(char) );
            
            specieList[3*specInd] = symtemp[0];
            specieList[3*specInd+1] = symtemp[1];
            specieList[3*specInd+2] = symtemp[2];
            
            specieList_c[2*specInd] = symtemp[0];
            specieList_c[2*specInd+1] = symtemp[1];
            
            NSpecies++;
        }
        
        /* update specie counter */
        specieCount_c[specInd]++;
                
        /* max and min positions */
        if ( xpos > maxPos[0] )
        {
            maxPos[0] = xpos;
        }
        if ( ypos > maxPos[1] )
        {
            maxPos[1] = ypos;
        }
        if ( zpos > maxPos[2] )
        {
            maxPos[2] = zpos;
        }
        if ( xpos < minPos[0] )
        {
            minPos[0] = xpos;
        }
        if ( ypos < minPos[1] )
        {
            minPos[1] = ypos;
        }
        if ( zpos < minPos[2] )
        {
            minPos[2] = zpos;
        }
    }
    
    fclose(INFILE);
    
    /* terminate specie list */
    specieList_c[2*NSpecies] = 'X';
    specieList_c[2*NSpecies+1] = 'X';
    
    free(specieList);
}


/*******************************************************************************
** read xyz input file
*******************************************************************************/
void readLBOMDXYZ( char* file, int posDim, double* pos, int chargeDim, double* charge, 
                   int KEDim, double* KE, int PEDim, double* PE, int forceDim, double* force, 
                   int maxPosDim, double* maxPos, int minPosDim, double* minPos, int xyzformat )
{
    FILE *INFILE;
    int i, index, id, NAtoms;
    double simTime, xpos, ypos, zpos;
    double chargetmp, KEtmp, PEtmp;
    double xfor, yfor, zfor;
    
    
    /* open file */
    INFILE = fopen(file, "r");
    if (INFILE == NULL)
    {
        printf("ERROR: could not open file: %s\n", file);
        printf("       reason: %s\n", strerror(errno));
        exit(35);
    }
    
    /* read header */
    fscanf(INFILE, "%d", &NAtoms);
    fscanf(INFILE, "%lf", &simTime);
        
    /* read atoms */
    minPos[0] = 1000000;
    minPos[1] = 1000000;
    minPos[2] = 1000000;
    maxPos[0] = -1000000;
    maxPos[1] = -1000000;
    maxPos[2] = -1000000;
    for (i=0; i<NAtoms; i++)
    {
        if (xyzformat == 0)
        {
            fscanf(INFILE, "%d%lf%lf%lf%lf%lf", &id, &xpos, &ypos, &zpos, &KEtmp, &PEtmp);
        }
        else if (xyzformat == 1)
        {
            fscanf(INFILE, "%d%lf%lf%lf%lf%lf%lf", &id, &xpos, &ypos, &zpos, &KEtmp, &PEtmp, &chargetmp);
        }
        
        index = id - 1;
        
        /* store data */
        pos[3*index] = xpos;
        pos[3*index+1] = ypos;
        pos[3*index+2] = zpos;
        
        KE[index] = KEtmp;
        PE[index] = PEtmp;
        
        if (xyzformat == 1)
        {
            charge[index] = chargetmp;
        }
        
        /* max and min positions */
        if ( xpos > maxPos[0] )
        {
            maxPos[0] = xpos;
        }
        if ( ypos > maxPos[1] )
        {
            maxPos[1] = ypos;
        }
        if ( zpos > maxPos[2] )
        {
            maxPos[2] = zpos;
        }
        if ( xpos < minPos[0] )
        {
            minPos[0] = xpos;
        }
        if ( ypos < minPos[1] )
        {
            minPos[1] = ypos;
        }
        if ( zpos < minPos[2] )
        {
            minPos[2] = zpos;
        }
    }
    
    fclose(INFILE);
}


/*******************************************************************************
 * Read LBOMD lattice file
 *******************************************************************************/
void readLatticeLBOMD( char* file, int specieDim, int* specie, int posDim, double* pos, int chargeDim, double* charge, 
                       int speclistDim, char* specieList_c, int specCountDim, int* specieCount_c, int maxPosDim, 
                       double* maxPos, int minPosDim, double* minPos )
{
    FILE *INFILE;
    int i, j, NAtoms, specInd;
    double xdim, ydim, zdim;
    char symtemp[3];
    char* specieList;
    double xpos, ypos, zpos, chargetemp;
    int NSpecies, comp, specieMatch;
    
    
    /* open file */
    INFILE = fopen( file, "r" );
    if (INFILE == NULL)
    {
        printf("ERROR: could not open file: %s\n", file);
        printf("       reason: %s\n", strerror(errno));
        exit(35);
    }
    
    /* read header */
    fscanf( INFILE, "%d", &NAtoms );
    fscanf(INFILE, "%lf%lf%lf", &xdim, &ydim, &zdim);
    
    /* allocate specieList */
    specieList = malloc( 3 * sizeof(char) );
    
    /* read in atoms */
    minPos[0] = 1000000;
    minPos[1] = 1000000;
    minPos[2] = 1000000;
    maxPos[0] = -1000000;
    maxPos[1] = -1000000;
    maxPos[2] = -1000000;
    NSpecies = 0;
    for (i=0; i<NAtoms; i++)
    {
        fscanf(INFILE, "%s%lf%lf%lf%lf", symtemp, &xpos, &ypos, &zpos, &chargetemp);
        
        /* store position and charge */
        pos[3*i] = xpos;
        pos[3*i+1] = ypos;
        pos[3*i+2] = zpos;
        
        charge[i] = chargetemp;
        
        /* find specie index */
        specInd = specieIndex(symtemp, NSpecies, specieList);
        
        specie[i] = specInd;
        
        if (specInd == NSpecies)
        {
            /* new specie */
            specieList = realloc( specieList, 3 * (NSpecies+1) * sizeof(char) );
            
            specieList[3*specInd] = symtemp[0];
            specieList[3*specInd+1] = symtemp[1];
            specieList[3*specInd+2] = symtemp[2];
            
            specieList_c[2*specInd] = symtemp[0];
            specieList_c[2*specInd+1] = symtemp[1];
            
            NSpecies++;
        }
        
        /* update specie counter */
        specieCount_c[specInd]++;
                
        /* max and min positions */
        if ( xpos > maxPos[0] )
        {
            maxPos[0] = xpos;
        }
        if ( ypos > maxPos[1] )
        {
            maxPos[1] = ypos;
        }
        if ( zpos > maxPos[2] )
        {
            maxPos[2] = zpos;
        }
        if ( xpos < minPos[0] )
        {
            minPos[0] = xpos;
        }
        if ( ypos < minPos[1] )
        {
            minPos[1] = ypos;
        }
        if ( zpos < minPos[2] )
        {
            minPos[2] = zpos;
        }
    }
    
    fclose(INFILE);
    
    /* terminate specie list */
    specieList_c[2*NSpecies] = 'X';
    specieList_c[2*NSpecies+1] = 'X';
        
    free(specieList);
}
