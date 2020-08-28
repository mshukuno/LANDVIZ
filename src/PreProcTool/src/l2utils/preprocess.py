import os, sys, logging
import lxml.etree as etree
import l2utils as utils
import yaml


class Utils(object):
    
    def __init__(self, CONFIG):
        self.CONFIG = CONFIG
    
    def error_logging(self, logObj, err):
        logObj.error(f'{err}')
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logObj.debug(f'{exc_type}::{fname}::{exc_tb.tb_lineno}')
        print(f'{exc_type}::{fname}::{exc_tb.tb_lineno}')
        sys.exit()
        
    def getProjectXml(self, projectFile):
        try:
            logGetProjectXml = logging.getLogger('metadata_mod.get_project_xml')
            projectScenarios = []
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(projectFile, parser).getroot()
            scenarios = tree.xpath(self.CONFIG['XPATH']['SCENARIOLIST'])
            
            if scenarios:
                catalog = etree.Element('Catalog', name='LANDIS II: XML Configuration Tool')
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
            self.error_logging(log_get_project_xmls, err)

    
class PreMerge(object):
    def __init__(self, appPath, configYaml, args):
        self.projectFile = args.projectFile
        self.outputFile = args.outputFile
        self.CONFIG = self.loadYamlConfig(appPath, configYaml)
        self.utils = Utils(self.CONFIG) 
    
    def loadYamlConfig(self, appPath, configYaml):
        try:
            # load YAML CONFIG File
            with open(os.path.join(appPath, configYaml), 'r') as f:
                return yaml.load(f, Loader=yaml.FullLoader)
            
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logObj.debug(f'{exc_type}::{fname}::{exc_tb.tb_lineno}')
            print(f'{exc_type}::{fname}::{exc_tb.tb_lineno}')
            sys.exit()
       
    def mergeXMLs(self):
        try:
            logGetProjectXml = logging.getLogger('preprocess.mergeXMLs')
            # Get project XML file directory - result output file will be saved there.
            projectFileBase = os.path.dirname(self.projectFile)
            resultXml = os.path.join(projectFileBase, self.outputFile+'.xml')
            
            # Get senario directory
            projectScenarios = self.utils.getProjectXml(self.projectFile)
            
            # LXML settings
            parser = etree.XMLParser(remove_blank_text=True)
            catalog = etree.Element('Catalog', name='LANDIS II: XML Configuration Tool')
            
            totalXmlCounter = 0      
            # ForEach scenario get extension XML file
            # THEN 
            # * convert XML content to ElementTree object
            # * append it to "Catalog" ElementTree object   
            for scenario in projectScenarios:
                xmlFileCounter = 0 
                metadataPath = os.path.join(projectFileBase, scenario, self.CONFIG['METADATA']['DIR'])
                if os.path.isdir(metadataPath):
                    for root, dirs, files in os.walk(metadataPath):
                        for f in files:
                            xmlFullPath = os.path.join(root, f)
                            nsXmlPath = xmlFullPath.split(scenario)[1]
                            # New element
                            project = etree.Element('Senario', name=scenario, xmlPath=nsXmlPath)
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
            logGetProjectXml.info('\nEND LANDIS-II PreProcTool')
            
        
        except Exception as e:
            logGetProjectXml.error(f'{e}')
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logGetProjectXml.debug(f'{exc_type}::{fname}::{exc_tb.tb_lineno}')
            print(f'{exc_type}::{fname}::{exc_tb.tb_lineno}')
            sys.exit()
            
            
        


