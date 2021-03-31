# LANDIS-II-Visualization
# PreProc Tool patch
# Tool data preparation
# 08/31/2020
# Makiko Shukunobe, Center for Geospatial Analytics, North Carolina State University

import os, sys, logging
import lxml.etree as etree
import yaml
from xmldiff import main, formatting

# Merge function XML path
XML_ROOT_TAG = 'Catalog'
XML_META_WRAPPER_TAG = 'Scenario'
ATTRIB_NAME = 'name'
ATTRIB_XMLPATH = 'xmlPath'
PARENT_ATTRIB_XMLPATH = 'xmlPath'
PREPROCESS_XML_NAME = 'LANDIS II: XML Configuration Tool'

# LANDIS II metadata root XML path name
LANDISMETADATA_TAG = 'landisMetadata'

  
class PreProcess(object):
    def __init__(self, appPath, configYaml, args):
        self.projectFile = args.projectFile
        self.configFile = args.configFile
        self.CONFIG = self.loadYamlConfig(appPath, configYaml)

    def errorLogging(self, logObj, err):
        logObj.error(err)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logObj.debug(f'{exc_type}::{fname}::{exc_tb.tb_lineno}')
#         print(f'{exc_type}::{fname}::{exc_tb.tb_lineno}')
        sys.exit()

    def loadYamlConfig(self, appPath, configYaml):
        """
        Load Yaml configuration file.
        """
        try:
            logLoadYaml = logging.getLogger('preconfedit.loadYamlConfig')
            # load YAML CONFIG File
            with open(os.path.join(appPath, configYaml), 'r') as f:
                return yaml.load(f, Loader=yaml.FullLoader)
        
        except Exception as e:
            self.errorLogging(logLoadYaml, e)
        
    def getProjectXml(self, projectFile):
        """
        Get project XML files for project scenario lists.
        """
        try:
            logGetProjectXml = logging.getLogger('metadata_mod.get_project_xml')
            projectScenarios = []
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(projectFile, parser).getroot()
            scenarios = tree.xpath(self.CONFIG['XPATH']['SCENARIOLIST'])
            
            if scenarios:
                catalog = etree.Element(XML_ROOT_TAG, name=PREPROCESS_XML_NAME)
                for scenario in scenarios:
                    projectScenarios.append(scenario.attrib[self.CONFIG['ATTRIB']['SCENARIOPATH']])
                if len(projectScenarios) == 1:
                    logGetProjectXml.info('[1] scenario')
                elif len(projectScenarios) > 0: 
                    logGetProjectXml.info(f'[{len(projectScenarios)}] scenarios')
                return projectScenarios
            else:
                logGetProjectXml.debug('No "scenario" XML tag found in file.')            
        
        except Exception as e:
            self.errorLogging(logGetProjectXml, e)
       
    def mergeXMLs(self):
        """
        Merge extension metadata XML files.
        """
        try:
            logGetProjectXml = logging.getLogger('preprocess.mergeXMLs')
            # Get project XML file directory - result output file will be saved there.
            projectFileBase = os.path.dirname(self.projectFile)
            resultXml = os.path.join(projectFileBase, self.configFile)
            
            # Get senario directory
            projectScenarios = self.getProjectXml(self.projectFile)
            
            # LXML settings
            parser = etree.XMLParser(remove_blank_text=True)
            catalog = etree.Element(XML_ROOT_TAG, name=PREPROCESS_XML_NAME)
            
            totalXmlCounter = 0      
            # ForEach scenario get extension XML file
            # THEN 
            # * convert XML content to ElementTree object
            # * append it to "Catalog" ElementTree object   
            for scenario in projectScenarios:
                xmlFileCounter = 0 
                metadataPath = os.path.join(projectFileBase, scenario, 
                                            self.CONFIG['METADATA']['DIR'])
                if os.path.isdir(metadataPath):
                    for root, dirs, files in os.walk(metadataPath):
                        for f in files:
                            xmlFullPath = os.path.join(root, f)
                            nsXmlPath = xmlFullPath.split(scenario)[1]
                            # New element
                            project = etree.Element(XML_META_WRAPPER_TAG, 
                                name=scenario, xmlPath=nsXmlPath)
                            # Convert xml file to ElementTree
                            xmlContent = etree.parse(xmlFullPath, parser).getroot()
                            project.append(xmlContent)
                            catalog.append(project)
                            xmlFileCounter += 1
                    logGetProjectXml.info(f'{scenario}: [{xmlFileCounter}] XML files')
                    totalXmlCounter += xmlFileCounter
            # Write the ElenmentTree object to file 
              
            with open(resultXml, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n') 
                f.write(etree.tostring(catalog, pretty_print=True))
            
            logGetProjectXml.info(f'[{totalXmlCounter}] XML files merged')                 
            logGetProjectXml.info('Merge complete')
            logGetProjectXml.info('\nEND')
        
        except Exception as e:
            self.errorLogging(logGetProjectXml, e)
        
    def checkConfigXml(self, tree):
        """
        Check input configuration XML file is generated by the PreProc
        "merge" tool.
        """
        logCheckConfigXml = logging.getLogger('preprocess.checkConfigXml')
        if tree.tag == XML_ROOT_TAG:
            if tree.attrib['name'] == PREPROCESS_XML_NAME:
                return True
        else:
            logCheckConfigXml.error('Configuration XML does not match the schema')
            logCheckConfigXml.debug('Make sure your XML configuration file \
                is generated by ConfigXML Tool.')
            sys.exit()
    
    def writeXml(self, xmlFile, newTree, oldTree):
        """
        I/O output 
        """
        try:
            logWriteXml = logging.getLogger('preprocess.writeXml')
            with open(xmlFile, 'w') as f:
                f.write(etree.tostring(newTree).decode('utf-8'))
        except:
            logWriteXml.error('Rollback to original')
            with open(xmlFile, 'w') as f:
                f.write(etree.tostring(oldTree).decode('utf-8'))
                   
    def updateXMLs(self): 
        """
        Update extension metadata XMLs according metadata configuration.
        """
        logUpdateXmls = logging.getLogger('preprocess.updateXMLs')
        parser = etree.XMLParser(remove_blank_text=True) 
        formatter = formatting.XmlDiffFormatter(normalize=formatting.WS_NONE)
        
        try: 
            # Get senario directory
            projectScenarios = self.getProjectXml(self.projectFile)
            projectFileBase = os.path.dirname(self.projectFile)
#             print(projectFileBase)
            configXml = os.path.join(projectFileBase, self.configFile)
            tree = etree.parse(configXml, parser).getroot() 
            
            if self.checkConfigXml(tree):
                diffCounter = 0
            # ForEach 'Scenario' tag
            for scenario in tree.findall(XML_META_WRAPPER_TAG):
                # Get 'name' attribute text
                if scenario.attrib.has_key(ATTRIB_NAME):
                    scenarioName = scenario.attrib[ATTRIB_NAME]
    #                 print(scenario_name)
                # Get 'xmlPath' attribute text
                if scenario.attrib.has_key(ATTRIB_XMLPATH):
                    xmlPath = scenario.attrib[ATTRIB_XMLPATH]
                
                # IF 'Scenario' tag has 'name' and 'xmlPath' attributes
                if len(scenarioName) > 0 and len(xmlPath) > 0:
                    if scenarioName in projectScenarios:
                        # print(scenarioName, xmlPath)
                        # Get original XML file
                        xmlFile = f'{projectFileBase}\{scenarioName}\{xmlPath}'
                        # Parse target XML file
                        oldTree = etree.parse(xmlFile, parser)
                        # Get 'landisMetadata' tag elements
                        landisMeta = scenario.xpath(LANDISMETADATA_TAG)[0]
                        newTree = etree.ElementTree(landisMeta)
        
                        diffs = main.diff_trees(oldTree, newTree)
                        
                        if len(diffs) > 0:
                            logUpdateXmls.info(f'\n[{len(diffs)}] updates on \
                                {os.path.join(scenarioName, xmlPath)}')
                            for idx, diff in enumerate(diffs):
                                diffCounter += 1
                                logUpdateXmls.info(f'{idx + 1}: {diff}')
                            
                            self.writeXml(xmlFile, newTree, oldTree)
    
            if diffCounter == 0:
                logUpdateXmls.info('No updates')
        
            logUpdateXmls.info('END')
            
        except Exception as e:
            self.errorLogging(logUpdateXmls, e)

    

