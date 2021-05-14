#!/usr/bin/env python

# LANDIS-II-Visualization 
# PreProc Tool
# (c) 2014, Johannes Liem, Oregon State University

# Updates
# 03/31/2021
# Makiko Shukunobe, Center for Geospatial Analytics, North Carolina State University

import sys
import os
import time
import argparse
from datetime import timedelta
import logging
import logging.handlers
import app_settings

# Set PreProcTool log file before the LANDVIZ module imports.
# It enables to use ```logger = logging.getLogger(__name__)```
# for each module.
appPath = app_settings.get_app_path()
appFile = app_settings.get_app_file()
logFile = os.path.join(appPath, 'logs', 'proproctool.log')
app_settings.setup_logger(logFile)

# Set osgeo PROJ_LIB environment variable
app_settings.set_env_proj_lib()

# LANDVIZ modules
from multiprocessing import freeze_support
from l2utils.collector import Collector
from l2utils.preprocess import PreProcess
from l2utils.preprocess import ExtensionLog
from l2utils.preworker import PreWorker
from l2utils.outputworker import OutputWorker


def extantFolder(x):
    """
    'Type' for argparse
    checks if outputfolder exists
    """
    if not os.path.isdir(x):
        os.mkdir(x)
    else:
        i = 1
        while os.path.isdir(x + "_{}".format(i)):
            i += 1
        x = x + "_{}".format(i)
        os.mkdir(x)
    return x


def extantFile(x):
    """
    'Type' for argparse - checks that file exists but does not open.
    """
    if not os.path.exists(x):
        raise argparse.ArgumentError(x, f"{x} does not exist")
    return x


def parseArguemnts(argv):
    # Argument Parser
    parser = argparse.ArgumentParser(description='LANDVIZ PreProcTool')

    subparsers = parser.add_subparsers(title="actions", dest="command")

    # merge tool
    parserMerge = subparsers.add_parser("merge",
                                        help="Merges metadata XML configurations into one XML file")
    mergeRequired = parserMerge.add_argument_group('required arguments')
    mergeRequired.add_argument("-p", "--projectfile",
                               dest="projectFile", required=True, type=extantFile,
                               help="Pre-Proc-Project XML File Path", metavar="FILE")
    mergeRequired.add_argument("-f", "--outputfile",
                               dest="configFile", required=True, type=str,
                               help="Output XML File Name", metavar="FILE NAME")
    # update tool
    parserUpdate = subparsers.add_parser("update",
                                         help="Updates metadata XML configuration files.  Require the merge tool "
                                              "output file as input file.")
    updateRequired = parserUpdate.add_argument_group('required arguments')
    updateRequired.add_argument("-p", "--projectfile",
                                dest="projectFile", required=True, type=extantFile,
                                help="Pre-Proc-Project XML File Path", metavar="FILE")
    updateRequired.add_argument("-f", "--inputfile",
                                dest="configFile", required=True, type=str,
                                help="Merged XML File Name", metavar="FILE NAME")
    # preProc tool
    parserPreproc = subparsers.add_parser("preproc",
                                          help="Creates LANDVIZ application after preprocessing data.")
    preprocRequired = parserPreproc.add_argument_group('required arguments')
    preprocRequired.add_argument("-p", "--projectfile",
                                 dest="projectFile", required=True, type=extantFile,
                                 help="Pre-Proc-Project File Path", metavar="FILE")
    preprocRequired.add_argument("-o", "--outputfolder",
                                 dest="outputFolder", required=True, type=extantFolder,
                                 help="Pre-Proc-Project Output Folder Path", metavar="FOLDER")

    # timesteps tool
    parserTimeSteps = subparsers.add_parser("timesteps", help="Creates a new CSV file with all time steps.")
    timeStepsRequired = parserTimeSteps.add_argument_group('required arguments')
    timeStepsRequired.add_argument("-i", "--inputfile", dest="csv_log_file", required=True, type=extantFile,
                                   help="Extension CSV log File", metavar="FILE")
    timeStepsRequired.add_argument("-f", "--outputfile", dest="out_csv_log_file", required=True, type=str,
                                   help="Output CSV file name")
    timeStepsRequired.add_argument("-ts_c", "--timestep-column", dest="time_step_column", required=True, type=str,
                                   help="Time steps")
    timeStepsRequired.add_argument("-ts_i", "--timestep-interval", dest="time_interval", required=True, type=int,
                                   help="Time step interval")
    timeStepsRequired.add_argument("-ts_min", "--min-time", dest="min_time", required=True, type=int,
                                   help="Minimum time step")
    timeStepsRequired.add_argument("-ts_max", "--max-time", dest="max_time", required=True, type=int,
                                   help="Maximum time step")
    parserTimeSteps.add_argument("-g", "--groupby", dest="group_by_column", required=False, type=str, default='',
                                 help="Group by column name")

    return parser.parse_args(argv)


def main(argv):
    logMain = logging.getLogger('landis.main')
    try:
        # parse commandline arguments
        args = parseArguemnts(argv)
        logMain.info('Start LANDIS-II PreProcTool')
        start = time.time()
        # Timestamp log file name
        logCopyDest = os.path.join(appPath, 'logs', f'{time.strftime("%Y%m%d-%H%M%S")}.log')

        confYamlPath = 'config\\config.yaml'
        if args.command == 'merge':
            preprocess = PreProcess(appPath, confYamlPath, args)
            preprocess.mergeXMLs()

        elif args.command == 'update':
            preprocess = PreProcess(appPath, confYamlPath, args)
            preprocess.updateXMLs()

        elif args.command == 'timesteps':
            timesteps = ExtensionLog(args)
            timesteps.checkTimeSteps()

        elif args.command == 'preproc':
            # LANDIS PreProc Collector: collects Project Configuration and Project Data
            collector = Collector()

            # CONFIG Object has different Configurations
            CONFIG = collector.setupConfig(appPath, appFile, confYamlPath, args)
            # PROJECT stores the complete Project (Infos aboute the Project/Scenarios/Extensions/Outputs)
            PROJECT = collector.setupProject()

            # LANDIS Preworker: prepare Tables and Maps
            preworker = PreWorker(PROJECT, CONFIG)

            outputworker = OutputWorker(PROJECT, CONFIG)
            outputworker.generateOutputDirs()

            preworker.prepairTables()
            preworker.prepairMaps()

            outputworker.saveMetadataJson()
            outputworker.copyWebbase()
            outputworker.updateWebsettings()

            outputworker.zipOutputDir()
        end = time.time()
        elapsed = str(timedelta(seconds=end - start))
        logMain.info(f'Processing time: {elapsed}')
        logMain.info('End of LANDIS-II PreProcTool')
        logging.shutdown()
        os.rename(logFile, logCopyDest)

    except SystemExit:  # argparse -h
        sys.exit(0)
    except Exception as err:
        app_settings.error_log(logMain, err)
        logMain.info('Failed to run LANDIS-II PreProcTool')


if __name__ == '__main__':
    freeze_support()
    main(sys.argv[1:])
