#!/usr/bin/env python2
"""Generate ILAMB diagnostics 

This script provides an interface to run the ILAMB package 

It resides in the $SRCROOT/postprocessing/ilamb_env
__________________________
Created on August, 2016

@author: CSEG <cseg@cgd.ucar.edu>
"""

from __future__ import print_function
import sys

# check the system python version and require 2.7.x or greater
if sys.hexversion < 0x02070000:
    print(70 * '*')
    print('ERROR: {0} requires python >= 2.7.x. '.format(sys.argv[0]))
    print('It appears that you are running python {0}'.format(
        '.'.join(str(x) for x in sys.version_info[0:3])))
    print(70 * '*')
    sys.exit(1)

import argparse
import glob
import os
import pprint
import re
import string
import sys
import traceback
import shutil
import xml.etree.ElementTree as ET

import netCDF4 as nc
import clm_to_mip

from cesm_utils import cesmEnvLib

#=====================================================
# commandline_options - parse any command line options
#=====================================================
def commandline_options():
    """Process the command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='cesm_ilamb_generator: CESM wrapper python program to create variable time series files from history time slice files.')

    parser.add_argument('--backtrace', action='store_true',
                        help='show exception backtraces as extra debugging output')

    parser.add_argument('--debug', nargs=1, required=False, type=int, default=0,
                        help='debugging verbosity level output: 0 = none, 1 = minimum, 2 = maximum. 0 is default')

    parser.add_argument('--caseroot', nargs=1, required=True, 
                        help='fully quailfied path to case root directory')

    parser.add_argument('--standalone', action='store_true',
                        help='switch to indicate stand-alone post processing caseroot')

    options = parser.parse_args()

    # check to make sure CASEROOT is a valid, readable directory
    if not os.path.isdir(options.caseroot[0]):
        err_msg = 'cesm_ilamb_generator.py ERROR: invalid option --caseroot {0}'.format(options.caseroot[0])
        raise OSError(err_msg)

    return options

#==============================================================================================
# readArchiveXML - read the $CASEROOT/env_ilamb.xml file and build the pyReshaper classes
#==============================================================================================
def readXML(caseroot, standalone, debug):
    """ reads the $CASEROOT/env_ilamb.xml  

    Arguments:
    caseroot (string) - case root path
    standalone (boolean) - logical to indicate if postprocessing case is stand-alone or not
    """
    specifiers = list()
    xml_tree = ET.ElementTree()

    # get path to env_ilamb.xml file
    env_ilamb = '{0}/postprocess/env_ilamb.xml'.format(caseroot)
    if standalone:
        env_ilamb = '{0}/env_ilamb.xml'.format(caseroot)

    # check if the env_ilamb.xml file exists
    if ( not os.path.isfile(env_ilamb) ):
        err_msg = "cesm_ilamb_generator.py ERROR: {0} does not exist.".format(env_ilamb)
        raise OSError(err_msg)
    else:
        # parse the xml
        xml_tree.parse(env_ilamb)

        # loop through all the comp_archive_spec elements to find the ilamb related elements
        for group in xml_tree.findall("groups/group"):
            if group.get("name") == 'ilamb_globals':
                globals = {}
                globals['obs_data'] = {}
                for entry in group.findall("entry"):
                    id = entry.get("id")
                    if "ILAMB_ROOT" in id:
                        globals['ilamb_root'] = entry.get("value")
                    elif "POSTPROCESS_PATH" in id:
                        globals['postprocess_path'] = entry.get("value")
                    elif "NETCDF_FORMAT" in id:
                        globals['netcdf_format'] = entry.get("value")
                    elif "OBS_DATA" in id:
                        i = id.split('__')[1]
                        globals['obs_data'][i] = entry.get("value")
            elif group.get("name") == 'case_info':
                cases = {}
                for entry in group.findall("entry"):
                    var = id.split('__')[0]
                    i = id.split('__')[1]
                    if i not in cases.keys():
                        cases[i] = {}
                    if "TIME_VARIANT_VARS" in var:
                        cases[i][var] = entry.get("value").split(',')
                    elif "YEARS" in var:
                        cases[i][var] = entry.get("value")
                        start = entry.get("value").split('-')[0]
                        end = entry.get("value").split('-')[1]
                        cases[i]['START'] = start
                        cases[i]['END'] = end
                        cases[i]['START_YEAR'] = start[:3]
                        cases[i]['END_YEAR'] = end[:3]
                        if len(start)>4 and len(end)>4:
                            cases[i]['START_MONTH'] = start[4:5] 
                            cases[i]['END_MONTH'] = end[4:5]
                    else:
                        cases[i][var] = entry.get("value")                    

    return globals, cases

def get_date(fn):

    f =  netCDF4.Dataset(fn,"r")
    time = f['time'][0]
    f.close()

    return time
    

def setup_reshaper(globals, cases):

    specifiers = list()
    for k,case in cases.iteritems():
        if case['CONVERT_TO_TS'] == 'TRUE':
            history_files = list()
    
            # Get the date ranges
            if 'START_MONTH' in case.keys():
                yr0 = get_date(case['CASE_PATH']+'/'+case['FILE_PREFIX']+case['START_YR']+'-'+case['START_MONTH']+'.nc')
                yr1 = get_date(case['CASE_PATH']+'/'+case['FILE_PREFIX']+case['END_YR']+'-'+case['END_MONTH']+'.nc')
            else:
                yr0 = get_date(case['CASE_PATH']+'/'+case['FILE_PREFIX']+case['START_YR']+'.nc')
                yr1 = get_date(case['CASE_PATH']+'/'+case['FILE_PREFIX']+case['END_YR']+'.nc')

            files = glob.glob(case['CASE_PATH']+'/'+case['FILE_PREFIX']+'*.nc')
            for f in files:
                c_d = get_date(f)
                if c_d >= yr0 and c_d <= yr1:
                    history_files.append(f)

            # sort the list of input history files in order to get the output suffix 
            # from the first and last file
            if len(history_files) > 0:
                history_files.sort()

            # get a reshpaer specification object
            spec = specification.create_specifier()

            # populate the spec object with data for this history stream
            spec.input_file_list = history_files
            spec.netcdf_format = globals['NETCDF_FORMAT']
            spec.output_file_prefix = case['TIMESERIES_OUTPUT_PATH']+'/'+case['FILE_PREFIX']
            spec.output_file_suffix = case['.'+case['YEARS']+'.nc']
            spec.time_variant_metadata = case['TIME_VARIANT_VARS']

            # print the specifier
            if debug:
                dbg = list()
                pp = pprint.PrettyPrinter(indent=5)
                dbg = [comp_name, spec.input_file_list, spec.netcdf_format, spec.output_file_prefix, spec.output_file_suffix, spec.time_variant_metadata]
                pp.pprint(dbg)
                           
            # append this spec to the list of specifiers
            specifiers.append(spec)

    return specifiers


def run_reshaper(caseroot, options, scomm, globals, cases, debug):
    # initialize the specifiers list to contain the list of specifier classes
    specifiers = list()

    # loading the specifiers from the env_ilamb.xml  only needs to run on the master task (rank=0) 
    if rank == 0:
        specifiers = setup_reshaper(globals,cases)
    scomm.sync()

    # specifiers is a list of pyreshaper specification objects ready to pass to the reshaper
    specifiers = scomm.partition(specifiers, func=partition.Duplicate(), involved=True)

    # create the PyReshaper object - uncomment when multiple specifiers is allowed
    reshpr = reshaper.create_reshaper(specifiers, serial=False, verbosity=debug)

    # Run the conversion (slice-to-series) process 
    reshpr.convert()

    # Print timing diagnostics
    reshpr.print_diagnostics()


def create_ilamb_root(ilamb_root, globals, cases):

    if not os.path.exists(ilamb_root):
        os.makedirs(directory)
    if not os.path.exists(ilamb_root+'/DATA'):
        os.makedirs(ilamb_root+'/DATA')
    if not os.path.exists(ilamb_root+'/MODELS'):
        os.makedirs(ilamb_root+'/MODELS')

    for dir in globals['obs_data']:
        shutil.copytree(dir, ilamb_root+'/DATA', copy_function=os.link)

    for k,case in cases.iteritems():
        shutil.copytree(case['MIP_OUTPUT_PATH'], ilamb_root+'/MODELS', copy_function=os.link)

#======
# main
#======

def main(options, scomm, rank, size):
    """
    """
    # initialize the CASEROOT environment dictionary
    cesmEnv = dict()

    # CASEROOT is given on the command line as required option --caseroot
    caseroot = options.caseroot[0]

    # set the caseroot based on standalone or not
    pp_caseroot = caseroot
    if not options.standalone:
        caseroot, pp_subdir = os.path.split(caseroot)
    if rank == 0:
        print('cesm_ilamb_generator: caseroot = {0}'.format(caseroot))

    # set the debug level 
    debug = options.debug[0]

    # cesmEnv["id"] = "value" parsed from the CASEROOT/env_*.xml files
    env_file_list = ['env_case.xml', 'env_run.xml', 'env_build.xml', 'env_mach_pes.xml']

    # check if the standalone option is set
    if options.standalone:
        env_file_list = ['env_postprocess.xml']
    cesmEnv = cesmEnvLib.readXML(caseroot, env_file_list)

    # Read XML ilamb file
    if rank == 0:
        globals,cases = readXML(caseroot, options.standalone, debug)
    scomm.sync()

    # Run the Reshaper to create time series files
    run_reshaper(caseroot, options, scomm, globals, cases, debug)
    scomm.sync()

    # Run the MIP converter
    clm_to_mip.run_mip(globals, cases, scomm)
    scomm.sync()

    # Configure the ILMB input directory
    ilamb_root = globals['ILAMB_ROOT']+'/MODELS/'
    create_ilamb_root(ilamb_root, globals, cases)

    # Run ILAMB
    config = globals['POSTPROCESS_PATH']+'/ilamb/ilamb/clm.cfg'
    driver.run_ilamb(model_root=ilamb_root, config=config, models=[], confront=[], regions=['global'], clean=True, quiet=False, filter=[""], build_dir=globals['BUILD_DIR'], comm=scomm)
    scomm.sync()

    if rank == 0:
        print('************************************************************')
        print('Successfully completed ILMB Package')
        print('************************************************************')  
 
    return 0

#===================================

if __name__ == "__main__":
    # initialize simplecomm object
    scomm = simplecomm.create_comm(serial=False)

    rank = scomm.get_rank()
    size = scomm.get_size()

    if rank == 0:
        print('...Running on {0} cores'.format(size))

    options = commandline_options()
    try:
        status = main(options, scomm, rank, size)
        if rank == 0:
            print('************************************************************')
            print('Successfully completed ILMB Package')
            print('************************************************************')
        sys.exit(status)

##    except RunTimeError as error:
        
    except Exception as error:
        print(str(error))
        if options.backtrace:
            traceback.print_exc()
        sys.exit(1)
