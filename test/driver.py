from ILAMB.ModelResult import ModelResult
from ILAMB.Scoreboard import Scoreboard
from ILAMB import ilamblib as il
import os,time,sys,argparse
from mpi4py import MPI
import numpy as np

# MPI stuff
comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

# Some color constants for printing to the terminal
OK   = '\033[92m'
FAIL = '\033[91m'
ENDC = '\033[0m'

def InitializeModels(model_root,models=[],verbose=False,filter=""):
    """Initializes a list of models

    Initializes a list of models where each model is the subdirectory
    beneath the given model root directory. The global list of models
    will exist on each processor.

    Parameters
    ----------
    model_root : str
        the directory whose subdirectories will become the model results
    models : list of str, optional
        only initialize a model whose name is in this list
    verbose : bool, optional
        enable to print information to the screen

    Returns
    -------
    M : list of ILAMB.ModelResults.ModelsResults
       a list of the model results, sorted alphabetically by name

    """
    # initialize the models
    M = []
    max_model_name_len = 0
    if rank == 0 and verbose: print "\nSearching for model results in %s\n" % model_root    
    for subdir, dirs, files in os.walk(model_root):
        for mname in dirs:
            if len(models) > 0 and mname not in models: continue
            M.append(ModelResult(subdir + "/" + mname, modelname = mname, filter=filter))            
            max_model_name_len = max(max_model_name_len,len(mname))
        break
    M = sorted(M,key=lambda m: m.name.upper())

    # assign unique colors
    clrs = il.GenerateDistinctColors(len(M))
    for m in M:
        clr     = clrs.pop(0)
        m.color = clr

    # optionally output models which were found
    if rank == 0 and verbose:
        for m in M: 
            print ("    {0:>45}").format(m.name)

    if len(M) == 0:
        if verbose and rank == 0: print "No model results found"
        comm.Barrier()
        comm.Abort(0)

    return M

def MatchRelationshipConfrontation(C):
    """Match relationship strings to confrontation longnames

    We allow for relationships to be studied by specifying the
    confrontation longname in the configure file. This routine loops
    over all defined relationships and finds the matching
    confrontation. (NOTE: this really belongs inside the Scoreboard
    object)

    Parameters
    ----------
    C : list of ILAMB.Confrontation.Confrontation
        the confrontation list

    Returns
    -------
    C : list of ILAMB.Confrontation.Confrontation
        the same list with relationships linked to confrontations
    """
    for c in C:
        if c.relationships is None: continue
        for i,longname in enumerate(c.relationships):
            found = False
            for cor in C:
                if longname.lower() == cor.longname.lower():
                    c.relationships[i] = cor
                    found = True
    return C
                
def FilterConfrontationList(C,match_list):
    """Filter the confrontation list

    Filter the confrontation list by requiring that at least one
    string in the input list is found in the longname in the
    confrontation.

    Parameters
    ----------
    C : list of ILAMB.Confrontation.Confrontation
       the source list of confrontations
    match_list : list of str
       the list of strings

    Returns
    -------
    Cf : list of ILAMB.Confrontation.Confrontation
        the list of filtered confrontations
    """
    if len(match_list) == 0: return C
    Cf = []
    for c in C:
        for match in match_list:
            if match in c.longname: Cf.append(c)
    return Cf

def BuildLocalWorkList(M,C):
    """Build the local work list
    
    We enumerate a list of work by taking combinations of model
    results and confrontations. This list is partitioned evenly among
    processes preferring to cluster as many confrontations with the
    same name together. While the work of the model-confrontation pair
    is local, some post-processing operations need performed once per
    confrontation. Thus we also need to flag one instance of each
    confrontation as the master process.

    Parameters
    ----------
    M : list of ILAMB.ModelResult.ModelResult
       list of models to analyze
    C : list of ILAMB.Confrontation.Confrontation
       list of confrontations
    
    Returns
    -------
    localW : list of (ILAMB.ModelResult.ModelResult, ILAMB.Confrontation.Confrontation) tuples
        the work local to this process
    """
    
    # Evenly divide up the work among processes
    W = []
    for c in C:
        for m in M:
            W.append([m,c])
    wpp    = float(len(W))/size
    begin  = int(round( rank   *wpp))
    end    = int(round((rank+1)*wpp))    
    localW = W[begin:end]

    # Determine who is the master of each confrontation
    for c in C:
        sendbuf = np.zeros(size,dtype='int')
        for w in localW:
            if c is w[1]: sendbuf[rank] += 1
        recvbuf = None
        if rank == 0: recvbuf = np.empty([size, sendbuf.size],dtype='int')
        comm.Gather(sendbuf,recvbuf,root=0)
        if rank == 0: 
            numc = recvbuf.sum(axis=1)
        else:
            numc = np.empty(size,dtype='int')
        comm.Bcast(numc,root=0)
        if rank == numc.argmax():
            c.master = True
        else:
            c.master = False
    
    return localW

def WorkConfront(W,verbose=False,clean=False):
    """Performs the confrontation analysis

    For each model-confrontation pair (m,c) in the input work list,
    this routine will call c.confront(m) and keep track of the time
    required as well as any exceptions which are thrown.

    Parameters
    ----------
    W : list of (ILAMB.ModelResult.ModelResult, ILAMB.Confrontation.Confrontation) tuples
        the list of work
    verbose : bool, optional
        enable to print output to the screen monitoring progress
    clean : bool, optional
        enable to perform the confrontation again, overwriting previous results

    """
    maxCL = 45; maxML = 20
       
    # Run analysis on your local work model-confrontation pairs
    for w in W:
        m,c = w

        # if the results file exists, skip this confrontation unless we want to clean
        if os.path.isfile("%s/%s_%s.nc" % (c.output_path,c.name,m.name)) and clean is False:
            if verbose:
                print ("    {0:>%d} {1:<%d} %sUsingCachedData%s " % (maxCL,maxML,OK,ENDC)).format(c.longname,m.name)
                sys.stdout.flush()
            continue

        # try to run the confrontation
        try:
            t0 = time.time()
            c.confront(m)  
            dt = time.time()-t0
            if verbose:
                print ("    {0:>%d} {1:<%d} %sCompleted%s {2:>5.1f} s" % (maxCL,maxML,OK,ENDC)).format(c.longname,m.name,dt)
                sys.stdout.flush()

        # if things do not work out, print the exception so the user has some idea
        except (il.VarNotInModel,
                il.AreasNotInModel,
                il.VarNotMonthly,
                il.VarNotOnTimeScale,
                il.NotTemporalVariable,
                il.UnitConversionError,
                il.AnalysisError,
                il.VarsNotComparable) as ex:
            if verbose:
                print ("    {0:>%d} {1:<%d} %s%s%s" % (maxCL,maxML,FAIL,ex,ENDC)).format(c.longname,m.name)

def WorkPost(M,C,W,S,verbose=False):
    """Performs the post-processing

    Determines plot limits across all models, makes plots, generates
    other forms of HTML output.

    Parameters
    ----------
    M : list of ILAMB.ModelResult.ModelResult
       list of models to analyze
    C : list of ILAMB.Confrontation.Confrontation
       list of confrontations
    W : list of (ILAMB.ModelResult.ModelResult, ILAMB.Confrontation.Confrontation) tuples
        the list of work
    S : ILAMB.Scoreboard.Scoreboard
        the scoreboard context
    verbose : bool, optional
        enable to print output to the screen monitoring progress

    """
    maxCL = 45; maxML = 20
    
    # work done on just the master confrontation
    for c in C: c.determinePlotLimits()
        
    for w in W:
        m,c = w
        t0  = time.time()    
        c.computeOverallScore(m)
        c.modelPlots(m)
        dt = time.time()-t0
        if verbose: print ("    {0:>%d} {1:<%d} %sCompleted%s {2:>5.1f} s" % (maxCL,maxML,OK,ENDC)).format(c.longname,m.name,dt)
        sys.stdout.flush()
        
    for c in C:
        c.compositePlots()
        c.generateHtml()
    
    if rank==0:
        S.createHtml(M)
        S.createSummaryFigure(M)


parser = argparse.ArgumentParser(description='')
parser.add_argument('--model_root', dest="model_root", metavar='root', type=str, nargs=1, default=["./"],
                    help='root at which to search for models')
parser.add_argument('--config', dest="config", metavar='config', type=str, nargs=1,
                    help='path to configuration file to use')
parser.add_argument('--models', dest="models", metavar='m', type=str, nargs='+',default=[],
                    help='specify which models to run, list model names with no quotes and only separated by a space.')
parser.add_argument('--confrontations', dest="confront", metavar='c', type=str, nargs='+',default=[],
                    help='specify which confrontations to run, list confrontation names with no quotes and only separated by a space.')
parser.add_argument('--regions', dest="regions", metavar='r', type=str, nargs='+',default=['global'],
                    help='specify which regions to compute over')
parser.add_argument('--clean', dest="clean", action="store_true",
                    help='enable to remove analysis files and recompute')
parser.add_argument('-q','--quiet', dest="quiet", action="store_true",
                    help='enable to silence screen output')
parser.add_argument('--filter', dest="filter", metavar='filter', type=str, nargs=1, default=[""],
                    help='a string which much be in the model filenames')
parser.add_argument('--build_dir', dest="build_dir", metavar='build_dir', type=str, nargs=1,default=["./_build"],
                    help='path of where to save the output')

args = parser.parse_args()
if args.config is None:
    if rank == 0:
        print "\nError: You must specify a configuration file using the option --config\n"
    comm.Barrier()
    comm.Abort(1)

T0 = time.time()
M  = InitializeModels(args.model_root[0],args.models,not args.quiet,filter=args.filter[0])
if rank == 0 and not args.quiet: print "\nParsing config file %s...\n" % args.config[0]
S = Scoreboard(args.config[0],
               regions   = args.regions,
               master    = rank==0,
               verbose   = not args.quiet,
               build_dir = args.build_dir[0])
C  = MatchRelationshipConfrontation(S.list())
Cf = FilterConfrontationList(C,args.confront)

if rank == 0 and not args.quiet and len(Cf) != len(C):
    print "\nWe filtered some confrontations, actually running...\n"
    for c in Cf: print ("    {0:>45}").format(c.longname)
C = Cf

sys.stdout.flush(); comm.Barrier()

if rank==0 and not args.quiet: print "\nRunning model-confrontation pairs...\n"
    
sys.stdout.flush(); comm.Barrier()

W = BuildLocalWorkList(M,C)
WorkConfront(W,not args.quiet,args.clean)

sys.stdout.flush(); comm.Barrier()

if rank==0 and not args.quiet: print "\nFinishing post-processing which requires collectives...\n"

sys.stdout.flush(); comm.Barrier()

WorkPost(M,C,W,S,not args.quiet)

sys.stdout.flush(); comm.Barrier()

if rank==0: S.dumpScores(M,"scores.csv")
    
if rank==0 and not args.quiet: print "\nCompleted in {0:>5.1f} s\n".format(time.time()-T0)



