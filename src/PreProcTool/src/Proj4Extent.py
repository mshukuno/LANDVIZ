#!/usr/bin/env python

# AssignProjectionFromFile.py

import sys
import argparse
import math
from osgeo import gdal
from osgeo import osr


def GetExtent(gt, cols, rows):
    ''' Return list of corner coordinates from a geotransform

        @type gt:   C{tuple/list}
        @param gt: geotransform
        @type cols:   C{int}
        @param cols: number of columns in the dataset
        @type rows:   C{int}
        @param rows: number of rows in the dataset
        @rtype:    C{[float,...,float]}
        @return:   coordinates of each corner
    '''
    ext = []
    xarr = [0, cols]
    yarr = [0, rows]

    for px in xarr:
        for py in yarr:
            x = gt[0] + (px * gt[1]) + (py * gt[2])
            y = gt[3] + (px * gt[4]) + (py * gt[5])
            ext.append([x, y])
        yarr.reverse()
    return ext


def GetSpatialRef(inputRaster):
    # OpenFile
    ds = gdal.Open(inputRaster, gdal.GA_ReadOnly)
    if ds is None:
        print('Failed to open Dataset: {}'.format(inputRaster))
        sys.exit()

    # Fetch Projection
    prj = ds.GetProjectionRef()
    sr = osr.SpatialReference()
    if sr.SetFromUserInput(prj) != 0:
        print('Failed to process SRS definition: {}'.format(prj))
        sys.exit()

    proj4 = sr.ExportToProj4()

    # Fetch Geotransform
    gt = ds.GetGeoTransform()
    gt = ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    ext = GetExtent(gt, cols, rows)

    ds = None

    return proj4, ext


def getZoom(ext, mapWidth=400, mapHeight=300):
    c = 40075016.6855785
    dx = abs(ext[0][0] - ext[2][0])
    dy = abs(ext[0][1] - ext[2][1])
    mpW = dx / mapWidth
    mpH = dy / mapHeight
    zW = math.log(c / mpW, 2) - 8
    zH = math.log(c / mpH, 2) - 8
    z = math.floor(min(zW, zH))

    return z


def main():
    # Argument Pars
    parser = argparse.ArgumentParser(description='Get Proj4 String and Extent from File')
    parser.add_argument('inputfile', help='Input File with Projection')

    args = vars(parser.parse_args())

    # Fetch Spatial Reference
    proj4, ext = GetSpatialRef(args['inputfile'])
    zoom = getZoom(ext)

    print("proj4=\"{}\"").format(proj4)
    print("ulx=\"{}\" uly=\"{}\" lrx=\"{}\" lry=\"{}\"").format(ext[0][0], ext[0][1], ext[2][0], ext[2][1])
    print("min=\"{}\" max=\"{}\" init=\"{}\"").format(int(zoom), int(zoom + 4), int(zoom + 2))


if __name__ == '__main__':
    main()