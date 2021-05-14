# !/usr/bin/env python

import logging
from lxml import etree
import app_settings

logger = logging.getLogger(__name__)


class XMLreader(object):
    # constructor
    def __init__(self, xmlFile, xsdFile=None):
        try:
            # parse xml file
            self.__xmlTree = etree.parse(xmlFile)
            # print(xmlFile)

            if xsdFile is not None:
                # parse xsd file IF is there
                xmlSchema = etree.XMLSchema(etree.parse(xsdFile))
                # validate self.__xmlTree against self.__xmlSchema
                xmlSchema.assertValid(self.__xmlTree)

        except Exception as e:
            app_settings.error_log(logger, e)

    # public

    def queryXML(self, xpathString, attributeName=None):
        """
        Returns a List of Dicts with AttributeKey:Value
        
        #: xpathString   : query xpath string 
        #: attributeName : string of Attribute to return (OPTIONAL)
        """
        try:
            elementList = []
            for xmlElement in self.__xmlTree.xpath(xpathString):
                if attributeName is not None:
                    attribList = {}
                    if attributeName in xmlElement.attrib:
                        attribList[attributeName] = xmlElement.attrib[attributeName]
                        elementList.append(attribList)
                else:
                    elementList.append(xmlElement.attrib)

            if len(elementList) == 0:
                return False

            if len(elementList) == 1 and len(elementList[0]) == 1 and attributeName is not None:
                return elementList[0][attributeName]

            return elementList

        except Exception as e:
            app_settings.error_log(logger, e)
