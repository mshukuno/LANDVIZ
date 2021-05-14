#!/usr/bin/env python

# Modified
# 08/31/2020
# Makiko Shukunobe, Center for Geospatial Analytics, North Carolina State University

import os
import shutil
import math
import logging
import time
from l2utils.mapworker import MapWorker
import json
from tilertools import gdal_tiler
import app_settings

logger = logging.getLogger(__name__)


class PreWorker(object):
    """
    - Assign Spatial Reference To Maps
    - Assign NoDataValue To Maps
    - get MinMax Values Over Time
    """
    def __init__(self, PROJECT, CONFIG):
        self.PROJECT = PROJECT
        self.CONFIG = CONFIG
        self.out_json = []

    def prepairTables(self):
        try:
            logger.info('Start prepairing Table Output')
            start = time.time()
            for s in self.PROJECT:
                for e in s:
                    for o in e:
                        if o.outputType == "Table":
                            src = o.csvFilePath
                            dst = os.path.join(self.CONFIG['PROJECT']['OUTPUT_DIR'], 'landisdata', 'modeldata',
                                               str(s.scenarioIndex), str(e.extensionIndex),
                                               str(o.outputIndex)) + "\\" + str(o.outputIndex) + ".csv"
                            shutil.copyfile(src, dst)
            end = time.time()
            logger.info('End prepairing Table Output [time: {} sec]'.format(end - start))

        except Exception as e:
            app_settings.error_log(logger, e)

    def prepairMaps(self):
        try:
            z = self.PROJECT.getZoomString()

            logger.info('Start prepairing Map Output')

            start = time.time()

            for s in self.PROJECT:
                for e in s:
                    for o in e:
                        if o.outputType == "Map":
                            mapInfo = {'scenario': s.scenarioName, 'extension': e.extensionName, 'output': o.outputName}
                            logger.info(f'scenario: {mapInfo["scenario"]}')
                            logger.info(f'extension: {mapInfo["extension"]}')
                            logger.info(f'output: {mapInfo["output"]}')

                            # FIXME: year 0 ??? s.timeMin + e.timeInterval
                            tempPathConcat = list()
                            for year in range(s.timeMin, s.timeMax + e.timeInterval, e.timeInterval):
                                rasterMapAtYear = os.path.normpath(self.getFilePath(o.filePathTemplate, str(year)))
                                # print rasterMapAtYear
                                if os.path.isfile(rasterMapAtYear):

                                    tempPath = os.path.join(self.CONFIG['PROJECT']['OUTPUT_DIR'], 'landisdata',
                                                            'modeldata', str(s.scenarioIndex), str(e.extensionIndex),
                                                            str(o.outputIndex)) + "\\" + str(year) + ".png"

                                    mw = MapWorker(self.PROJECT.spatialReferenceWKT, self.PROJECT.geoExtent, o.dataType)

                                    stats = mw.process(rasterMapAtYear, tempPath)
                                    #                                     print(stats)
                                    if stats:
                                        tempPathConcat.append(tempPath)
                                        o.addStats(year, stats)
                                        tilesOutputDirTT = os.path.join(self.CONFIG['PROJECT']['OUTPUT_DIR'],
                                                                        'landisdata', 'modeldata', str(s.scenarioIndex),
                                                                        str(e.extensionIndex), str(o.outputIndex))
                                        logger.info('prepair year = {}'.format(year))
                                    else:
                                        logger.info(
                                            f'prepair year = {year} [No valid pixels found in sampling - skip map tiles]')

                                else:
                                    logger.info('prepair year = {} [year not available]'.format(year))

                            try:
                                gdal_tiler.GdalTiler(
                                    ['-s', '-p', 'xyz', '-z', z, '-t', tilesOutputDirTT] + tempPathConcat)

                            except Exception as e:
                                app_settings.error_log(logger, e)

                            # delete tiling input
                            for temp in tempPathConcat:
                                os.remove(temp)
                                os.remove(temp+".aux.xml")

                            # print "STATS for ", o.outputName, o.getStats()
                            # statsDictToJson = {}
                            # statsDictToJson['byYear'] = dict(o.getStats())
                            overallTimeStats = {}
                            overallTimeStats = o.getOverallStats()

                            if o.dataType == 'nominal':
                                classification = self.createNominalClassification(overallTimeStats['minMaxMasked'][0],
                                                                                  overallTimeStats['minMaxMasked'][1],
                                                                                  overallTimeStats['middle'],
                                                                                  o.dataType)
                                classification['classes'] = overallTimeStats['uniqueValsMaksed']
                            elif o.dataType == 'ordinal':
                                classification = self.createOrdinalClassification(overallTimeStats['minMaxMasked'][0],
                                                                                  overallTimeStats['minMaxMasked'][1],
                                                                                  overallTimeStats['middle'],
                                                                                  o.dataType)
                            elif o.dataType == 'continuous':
                                classification = self.createContinuousClassification(
                                    overallTimeStats['minMaxMasked'][0], overallTimeStats['minMaxMasked'][1],
                                    overallTimeStats['middle'], o.dataType)

                            statsDictToJson = {}
                            # if o.dataType == 'continuous':
                            statsDictToJson['classification'] = classification
                            statsDictToJson['overTime'] = overallTimeStats
                            # statsDictToJson['byTime'] = o.getStats()

                            # print statsDictToJson
                            # print statsDictToJson

                            with open(os.path.normpath(
                                    os.path.join(self.CONFIG['PROJECT']['OUTPUT_DIR'], 'landisdata', 'modeldata',
                                                 str(s.scenarioIndex), str(e.extensionIndex),
                                                 str(o.outputIndex)) + '\metadata.stats.json'), 'w') as f:
                                f.write(json.dumps(statsDictToJson, sort_keys=True, indent=2))
            #                             print(j, file=f)
            end = time.time()
            logger.info('End prepairing Map Output [time: {} sec]'.format(end - start))

        except Exception as e:
            app_settings.error_log(logger, e)

    def createNominalClassification(self, min, max, middle, scaleType):
        try:
            # FIXME: classcount not fixed (from input file)
            classification = {}
            classification['drawReverse'] = False
            classification['legendMin'] = min
            classification['legendMax'] = max
            classification['legendMiddle'] = middle
            classification['colorSchema'] = 'qualitative'
            return classification

        except Exception as e:
            app_settings.error_log(logger, e)

    def createOrdinalClassification(self, min, max, middle, scaleType):
        try:
            # classCount = 4;
            classification = {}
            classification['drawReverse'] = False

            if min < 0 and max > 0:
                classification['colorSchema'] = 'diverging'
            if min > 0 and max > 0:
                classification['colorSchema'] = 'sequential'
            if min < 0 and max < 0:
                classification['colorSchema'] = 'sequential'
                classification['drawReverse'] = True

            classification['legendMin'] = min
            classification['legendMax'] = max
            classification['legendMiddle'] = middle
            classification['classes'] = []
            for i in range(min, max + 1):
                classification['classes'].append(i)
            return classification

        except Exception as e:
            app_settings.error_log(logger, e)

    def createContinuousClassification(self, min, max, middle, scaleType):
        # FIXME: classcount not fixed (from input file)
        try:
            classCount = self.PROJECT.initClassCount + 1
            classification = {}
            classification['drawReverse'] = False

            # ColorSchema
            if min < 0 and max > 0:
                classification['colorSchema'] = 'diverging'
            if min > 0 and max > 0:
                classification['colorSchema'] = 'sequential'
            if min < 0 and max < 0:
                classification['colorSchema'] = 'sequential'
                classification['drawReverse'] = True

            operatorMin = self.getOperator(min)
            operatorMax = self.getOperator(max)
            operatorMiddle = math.trunc(math.log10(math.fabs(middle)))

            # if math.log(math.abs(min)):

            legendMin = math.floor(float(min) / operatorMin) * operatorMin
            legendMax = math.ceil(float(max) / operatorMax) * operatorMax
            legendMiddle = round(float(middle) / operatorMax) * operatorMax

            if legendMin == 0:
                legendMin = 1

            # print 'min: {0} => {1}'.format(min, legendMin)
            # print 'max: {0} => {1}'.format(max, legendMax)
            # print 'middle: {0} => {1}'.format(middle, legendMiddle)

            # if Diff of min and max is < class count ...

            classification['legendMin'] = legendMin
            classification['legendMax'] = legendMax
            classification['legendMiddle'] = legendMiddle
            classification['classes'] = []

            rightRange = legendMax - legendMiddle
            operator = self.getOperator(rightRange / (classCount / 2))
            rightClassSize = round(float(rightRange / (classCount / 2)) / operator) * operator

            classification['classes'].append(legendMiddle)
            for i in range(math.trunc((classCount / 2) - 1)):
                val = classification['classes'][len(classification['classes']) - 1] + rightClassSize
                operator = self.getOperator(val)
                legendVal = round(float(val) / operator) * operator
                classification['classes'].append(legendVal)

            classification['classes'] = sorted(classification['classes'], reverse=True)
            #  print classification['classes']

            leftRange = legendMiddle - legendMin
            # print leftRange, classCount/2.0
            operator = self.getOperator(leftRange / (classCount / 2.0))
            leftClassSize = round(float(leftRange / (classCount / 2.0)) / operator) * operator
            #             print()

            for i in range(math.trunc((classCount / 2) - 1)):
                val = classification['classes'][len(classification['classes']) - 1] - leftClassSize
                operator = self.getOperator(val)
                legendVal = round(float(val) / operator) * operator
                classification['classes'].append(legendVal)

            classification['classes'] = sorted(classification['classes'], reverse=False)
            # print classification['classes']
            # print min, max, middle, scaleType
            return classification

        except Exception as e:
            app_settings.error_log(logger, e)

    def getOperator(self, value):
        try:
            if (value > 0):
                digits = math.trunc(math.log10(math.fabs(value)))
            else:
                digits = 0
            if digits <= 3:
                return 10
            else:
                return 10 ** (digits - 2)

        except Exception as e:
            app_settings.error_log(logger, e)

    def getFilePath(self, pathTemplate, year):
        return (((pathTemplate.replace('{timestep}', year)).replace('[', '')).replace(']', '')).replace('/', '\\')
