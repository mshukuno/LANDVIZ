import sys
import os
import logging
import distutils.core
from regex import sub
import json
import zipfile
from osgeo import ogr
from osgeo import osr
from l2utils.weblinks import Weblinks
import app_settings

logger = logging.getLogger(__name__)


class OutputWorker(object):
    def __init__(self, PROJECT, CONFIG):
        """
        OutputWorker Constructor
        """
        self.PROJECT = PROJECT
        self.CONFIG = CONFIG

    def copyWebbase(self):
        try:
            logger.info('Copy webbase to output directory')

            excEnv = os.path.basename(sys.executable)

            if excEnv == 'PreProcTool.exe':
                distutils.dir_util.copy_tree(
                    self.CONFIG['APPLICATION']['PATH'] + "\webbase", self.CONFIG['PROJECT']['OUTPUT_DIR'])
                Weblinks(self.CONFIG['PROJECT']['INPUT_XML'],
                         os.path.join(self.CONFIG['APPLICATION']['PATH'], 'webbase'),
                         self.CONFIG['PROJECT']['OUTPUT_DIR'])
            else:
                templatePath = os.path.normpath(
                    os.path.join(self.CONFIG['APPLICATION']['PATH'], '..\\..\\WebVisTool\\build\\dist'))
                distutils.dir_util.copy_tree(templatePath, self.CONFIG['PROJECT']['OUTPUT_DIR'])
                Weblinks(self.CONFIG['PROJECT']['INPUT_XML'], templatePath, self.CONFIG['PROJECT']['OUTPUT_DIR'])

        except Exception as e:
            app_settings.error_log(logger, e)

    def generateOutputDirs(self):
        """
        generates output directories
        """
        logger.info('Generate output directories')
        op = self.CONFIG['PROJECT']['OUTPUT_DIR']
        opd = os.path.join(op, 'landisdata')

        if not os.path.isdir(op):
            logger.info("Create output directory: " + op)
            os.mkdir(op)

        if not os.path.isdir(opd):
            logger.info("Create landisdata directory: " + opd)
            os.mkdir(opd)

        metadata = 'metadata'
        modeldata = 'modeldata'
        try:
            if not os.path.isdir(os.path.join(opd, metadata)):
                os.mkdir(os.path.join(opd, metadata))
        except Exception as e:
            app_settings.error_log(logger, e)

        try:
            if not os.path.isdir(os.path.join(opd, modeldata)):
                os.mkdir(os.path.join(opd, modeldata))
            for s in self.PROJECT:
                sname = sub('[\\/:"*?<>| ]+', '_', s.scenarioName).lower()
                sn = str(s.scenarioIndex)
                if not os.path.isdir(os.path.join(opd, modeldata, sn)):
                    os.mkdir(os.path.join(opd, modeldata, sn))
                if not os.path.isdir(os.path.join(opd, modeldata, sn, "__" + sname + "__")):
                    os.mkdir(os.path.join(
                        opd, modeldata, sn, "__" + sname + "__"))
                for e in s:
                    if e.getOutputNum():
                        ename = sub('[\\/:"*?<>| ]+', '_',
                                    e.extensionName).lower()
                        en = str(e.extensionIndex)
                        if not os.path.isdir(os.path.join(opd, modeldata, sn, en)):
                            os.mkdir(os.path.join(opd, modeldata, sn, en))
                        if not os.path.isdir(os.path.join(opd, modeldata, sn, en, "__" + ename + "__")):
                            os.mkdir(os.path.join(opd, modeldata,
                                                  sn, en, "__" + ename + "__"))
                        for o in e:
                            oname = sub('[\\/:"*?<>| ]+', '_',
                                        o.outputName).lower()
                            on = str(o.outputIndex)
                            if not os.path.isdir(os.path.join(opd, modeldata, sn, en, on)):
                                os.mkdir(os.path.join(
                                    opd, modeldata, sn, en, on))
                            if not os.path.isdir(os.path.join(opd, modeldata, sn, en, on, "__" + oname + "__")):
                                os.mkdir(os.path.join(opd, modeldata,
                                                      sn, en, on, "__" + oname + "__"))

        except Exception as e:
            app_settings.error_log(logger, e)

    def saveMetadataJson(self):
        try:
            logger.info('Save Metadata as JSON files')

            scenariosDictToJson = {}
            scenariosDictToJson['scenarios'] = self.PROJECT.getScenarioDict()
            #             j=json.dumps(scenariosDictToJson, sort_keys=True, indent=2)
            with open(os.path.normpath(
                    self.CONFIG['PROJECT']['OUTPUT_DIR'] + '/landisdata/metadata/metadata.scenarios.json'), 'w') as f:
                f.write(json.dumps(scenariosDictToJson, sort_keys=True, indent=2))
            #             print(j, file=f)

            extensionOutputDictToJson = self.PROJECT.getExtensionOutputDict()
            #             j=json.dumps(extensionOutputDictToJson, sort_keys=True, indent=2)
            with open(os.path.normpath(
                    self.CONFIG['PROJECT']['OUTPUT_DIR'] + '/landisdata/metadata/metadata.extensions.json'), 'w') as f:
                f.write(json.dumps(extensionOutputDictToJson, sort_keys=True, indent=2))

        except Exception as e:
            app_settings.error_log(logger, e)

    def updateWebsettings(self):
        try:
            logger.info('Update web settings file')

            extent = self.PROJECT.geoExtent

            ul = ogr.Geometry(ogr.wkbPoint)
            ul.AddPoint(float(extent['ulx']), float(extent['uly']))

            lr = ogr.Geometry(ogr.wkbPoint)
            lr.AddPoint(float(extent['lrx']), float(extent['lry']))

            source = osr.SpatialReference()
            source.ImportFromWkt(self.PROJECT.spatialReferenceWKT)

            target = osr.SpatialReference()
            target.ImportFromEPSG(3857)  # WebProjection 3857 #Geographic 4326

            transform = osr.CoordinateTransformation(source, target)

            ul.Transform(transform)
            lr.Transform(transform)

            centerX = ul.GetX() + (abs(ul.GetX() - lr.GetX()) / 2.0)
            centerY = lr.GetY() + (abs(ul.GetY() - lr.GetY()) / 2.0)

            minX = min(ul.GetX(), lr.GetX())
            minY = min(ul.GetY(), lr.GetY())
            maxX = max(ul.GetX(), lr.GetX())
            maxY = max(ul.GetY(), lr.GetY())

            with open(os.path.normpath(self.CONFIG['PROJECT']['OUTPUT_DIR'] + "/config/default_settings.json"),
                      "r+") as jsonFile:
                data = json.load(jsonFile)

                data["projectname"] = self.PROJECT.projectName
                data["map"]["resolutions"] = self.PROJECT.getResolutions()
                data["map"]["resolution"] = self.PROJECT.getInitResolution()
                data["map"]["basemap"]["saturation"] = self.PROJECT.initSaturation
                data["map"]["basemap"]["contrast"] = self.PROJECT.initContrast
                data["map"]["basemap"]["brightness"] = self.PROJECT.initBrightness
                data["map"]["basemap"]["source"] = self.PROJECT.mapSource
                data["map"]["center"] = [centerX, centerY]
                data["map"]["extent"] = [minX, minY, maxX, maxY]
                data["map"]["legend"] = {}
                data["map"]["legend"]["seqCol"] = self.PROJECT.seqCol
                data["map"]["legend"]["divCol"] = self.PROJECT.divCol
                data["map"]["legend"]["qualCol"] = self.PROJECT.qualCol

                jsonFile.seek(0)  # rewind
                jsonFile.write(json.dumps(data, sort_keys=False, indent=2))
                jsonFile.truncate()

        except Exception as e:
            app_settings.error_log(logger, e)

    def zipdir(self, path, zip):
        for root, dirs, files in os.walk(path):
            for file in files:
                if os.path.splitext(file)[1] != '.exe':
                    zip.write(os.path.join(root, file))

    def zipOutputDir(self):
        try:
            logger.info('Create zipfile for server upload')
            # Create the zip file for server upload
            zipdn = os.path.normpath(self.CONFIG['PROJECT']['OUTPUT_DIR'])
            zipfn = zipdn + '.zip'

            zipf = zipfile.ZipFile(zipfn, 'w')
            self.zipdir(zipdn, zipf)
            zipf.close()

            logger.info('Output Folder: ' + os.path.abspath(zipdn))
            logger.info('Zip File: ' + os.path.abspath(zipfn))

        except Exception as e:
            app_settings.error_log(logger, e)