#!/usr/bin/env python

# LANDIS-II-Visualization 
# PreProc Tool
# (c) 2014, Johannes Liem, Oregon State University

# Updates
# 03/31/2021
# Makiko Shukunobe, Center for Geospatial Analytics, North Carolina State University

import sys
import os
os.environ['PROJ_LIB'] = os.path.join(os.path.dirname(__file__), 'proj')

import module_locator
import logging
import argparse

from l2utils.collector import Collector
from l2utils.preprocess import PreProcess
from l2utils.preworker import PreWorker
from l2utils.outputworker import OutputWorker

from l2data import datastructure
from multiprocessing import freeze_support
import time
from datetime import timedelta


# from tilertools import *


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
        raise argparse.ArgumentError("{0} does not exist".format(x))
    return x


def parseArguemnts():
    # Argument Parser

    parser = argparse.ArgumentParser(description='Landis2Vis')

    subparsers = parser.add_subparsers(title="actions", dest="command")

    parserMerge = subparsers.add_parser("merge",
                                        help="Merge metadata XML configurations into one XML file")
    parserMerge.add_argument("-p", "--projectfile",
                             dest="projectFile", required=True, type=extantFile,
                             help="Pre-Proc-Project File", metavar="FILE")
    parserMerge.add_argument("-f", "--outputfile",
                             dest="configFile", required=True, type=str,
                             help="Merged XML Configuration Output XML File Name", metavar="FILE NAME")

    parserUpdate = subparsers.add_parser("update",
                                         help="Update metadataXML according configuration XML file created by merge")
    parserUpdate.add_argument("-p", "--projectfile",
                              dest="projectFile", required=True, type=extantFile,
                              help="Pre-Proc-Project File", metavar="FILE")
    parserUpdate.add_argument("-f", "--inputfile",
                              dest="configFile", required=True, type=str,
                              help="Merged XML Configuration input XML File Name", metavar="FILE NAME")

    parserPreproc = subparsers.add_parser("preproc",
                                          help="Run the PreProc tool")
    parserPreproc.add_argument("-p", "--projectfile",
                               dest="projectFile", required=True, type=extantFile,
                               help="Pre-Proc-Project File", metavar="FILE")

    parserPreproc.add_argument("-o", "--outputfolder",
                               dest="outputFolder", required=True, type=extantFolder,
                               help="Pre-Proc-Project Output Folder", metavar="FOLDER")

    return parser.parse_args()


def main(script, *args):

    try:
        # get the path and the file of the application file (executeable)

        # appPath, appFile = os.path.split(os.path.normpath(os.path.realpath(script)))
        appPath, appFile = os.path.split(os.path.normpath(os.path.realpath(__file__)))
        appPath = module_locator.module_path()

        if not os.path.isdir(appPath+'\logs'):
            os.mkdir(appPath+'\logs')

        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-25s %(levelname)-8s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p',
                            filename=appPath + '\logs\\' + time.strftime('%Y%m%d-%H%M%S') + '.log',
                            filemode='w')

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        logMain = logging.getLogger('landis.main')
        logMain.info('Start LANDIS-II PreProcTool')

        # parse commandline arguments
        args = parseArguemnts()
        confYamlPath = 'config\config.yaml'
        if args.command == 'merge':
            preprocess = PreProcess(appPath, confYamlPath, args)
            preprocess.mergeXMLs()
            sys.exit()

        elif args.command == 'update':
            preprocess = PreProcess(appPath, confYamlPath, args)
            preprocess.updateXMLs()
            sys.exit()

        elif args.command == 'preproc':
            start = time.time()
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
            logMain.info('End of LANDIS-II PreProcTool.')
            sys.exit(0)

    except Exception as e:
        logMain.error('Failed to run LANDIS-II PreProcTool')

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logMain.debug(exc_type, fname, exc_tb.tb_lineno)
        sys.exit(0)


if __name__ == '__main__':
    freeze_support()
    main(*sys.argv)
