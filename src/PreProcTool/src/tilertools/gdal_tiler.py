#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (c) 2011-2013 Vadim Shlyakhov
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
###############################################################################

import argparse
import os
import logging
import sys
import time

from tilertools.tiler_function import *
from tilertools.tiler_backend import Pyramid, resampling_lst, base_resampling_lst
from tilertools import map2gdal
from tilertools import tiler_global_mercator


def preprocess_src(src_opt):
    # ----------------------------
    logGdalTiler = logging.getLogger()

    try:
        src, options = src_opt
        opt = LooseDict(options)
        res = map2gdal.process_src(src, no_error=True, opt=opt)
        ld('preprocess_src', res)
        return res
    except Exception as e:
        logGdalTiler.error('{}'.format(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logGdalTiler.debug('{}::{}::{}'.format(exc_type, fname, exc_tb.tb_lineno))

        sys.exit()

    # ----------------------------


def process_src(src_def_opt):
    # ----------------------------
    logGdalTiler = logging.getLogger('gdaltiler.process_src')

    try:
        src, delete_src, options = src_def_opt
        opt = LooseDict(options)
        opt.tile_format = opt.tile_format.lower()
        opt.tile_ext = '.' + opt.tile_format
        opt.delete_src = delete_src

        profile = Pyramid.profile_class(opt.profile)

        ext = profile.defaul_ext if opt.strip_dest_ext is None else ''
        dest = dest_path(src, opt.dest_dir, ext)

        prm = profile(src, dest, opt)
        pf('tile year = {}'.format(os.path.splitext(os.path.basename(src))[0]))
        ld('tile year = {}'.format(os.path.splitext(os.path.basename(src))[0]))
        prm.walk_pyramid()
    except Exception as e:
        logGdalTiler.error('{}'.format(e))

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logGdalTiler.debug('{}::{}::{}'.format(exc_type, fname, exc_tb.tb_lineno))

        sys.exit()

    # ----------------------------


# ----------------------------
class GdalTiler(object):

    def option_args(self, arg_lst):

        # parser = argparse.ArgumentParser(usage="usage: %prog <options>... source...",
        #                                  description='Tile cutter for GDAL-compatible raster maps')

        parser = argparse.ArgumentParser(description='Tile cutter for GDAL-compatible raster maps')

        parser.add_argument('-p', '--profile', '--to', dest="profile", metavar='PROFILE',
                            default='zyx', type=str, choices=Pyramid.profile_lst(),
                            help='output tiles profile (default: zyx)')

        parser.add_argument("-f", "--list-profiles", action="store_true",
                            help='list tile profiles')
        parser.add_argument("-z", "--zoom", default=None, type=str, metavar="ZOOM_LIST",
                            help='list of zoom ranges to generate')
        parser.add_argument("--srs", default=None, metavar="SOURCE_SRS",
                            help="override source's spatial reference system")
        parser.add_argument("--tiles-srs", default=None, metavar="TILES_SRS",
                            help="target SRS for generic profile")
        parser.add_argument("--tile-size", default='256,256', metavar="SIZE_X,SIZE_Y",
                            help='generic profile: tile size (default: 256,256)')
        parser.add_argument("--zoom0-tiles", default='1,1', metavar="NTILES_X,NTILES_Y",
                            help='generic profile: number of tiles along the axis at the zoom 0 (default: 1,1)')
        parser.add_argument('--overview-resampling', default='nearest', metavar="METHOD1",
                            choices=resampling_lst(),
                            help='overview tiles resampling method (default: nearest)')
        parser.add_argument('--base-resampling', default='nearest', metavar="METHOD2",
                            choices=base_resampling_lst(),
                            help='base image resampling method (default: nearest)')
        parser.add_argument('-r', '--release', action="store_true",
                            help='set resampling options to (antialias,bilinear)')
        parser.add_argument('--tps', action="store_true",
                            help='Force use of thin plate spline transformer based on available GCPs)')
        parser.add_argument("-c", "--cut", action="store_true",
                            help='cut the raster as per cutline provided either by source or by "--cutline" option')
        parser.add_argument("--cutline", default=None, metavar="DATASOURCE",
                            help='cutline data: OGR datasource')
        parser.add_argument("--cutline-match-name", action="store_true",
                            help='match OGR feature field "Name" against source name')
        parser.add_argument("--cutline-blend", dest="blend_dist", default=None, metavar="N",
                            help='CUTLINE_BLEND_DIST in pixels')
        parser.add_argument("--src-nodata", dest="src_nodata", metavar='N[,N]...',
                            help='Nodata values for input bands')
        parser.add_argument("--dst-nodata", dest="dst_nodata", metavar='N',
                            help='Assign nodata value for output paletted band')
        parser.add_argument("--tiles-prefix", default='', metavar="URL",
                            help='prefix for tile URLs at googlemaps.hml')
        parser.add_argument("--tile-format", default='png', metavar="FMT",
                            help='tile image format (default: png)')
        parser.add_argument("--paletted", action="store_true",
                            help='convert tiles to paletted format (8 bit/pixel)')
        parser.add_argument("-t", "--dest-dir", dest="dest_dir", type=str, default=None,
                            help='destination directory (default: source)')
        parser.add_argument("--noclobber", action="store_true",
                            help='skip processing if the target pyramid already exists')
        parser.add_argument("-s", "--strip-dest-ext", action="store_true",
                            help='do not add a default extension suffix from a destination directory')

        parser.add_argument("-q", "--quiet", action="store_const",
                            const=0, default=1, dest="verbose")
        parser.add_argument("-d", "--debug", action="store_const",
                            const=2, dest="verbose")
        parser.add_argument("-l", "--long-name", action="store_true",
                            help='give an output file a long name')
        parser.add_argument("-n", "--after-name", action="store_true",
                            help='give an output file name after a map name (from metadata)')
        parser.add_argument("-m", "--after-map", action="store_true",
                            help='give an output file name  after name of a map file, otherwise after a name of an image file')

        # ----------------------------
        options, args = parser.parse_known_args(arg_lst)


        if not args:
            parser.error('No input file(s) specified')

        return options, args

    # ----------------------------

    def __init__(self, arguments):
        logGdalTiler = logging.getLogger('gdaltiler.init')
        # ----------------------------
        try:
            options, args = self.option_args(arguments)

            parser = argparse.ArgumentParser(usage = "usage: %prog <options>... source...",
                                         description='Tile cutter for GDAL-compatible raster maps')

            if options.verbose == 2:
                set_nothreads()

            if options.list_profiles:
                Pyramid.profile_lst(tty=True)
                sys.exit(0)

            if options.release:
                options.overview_resampling, options.base_resampling = ('antialias', 'cubic')

            try:
                sources = args
            except:
                raise Exception("No sources specified")

            srcOpt = []
            for s in sources:
                srcOpt.append((s, options))

            res = parallel_map(preprocess_src, srcOpt)

            srcDefOpt = []
            for r in flatten(res):
                srcDefOpt.append((r[0], r[1], options))
            # logTile = logging.getLogger('landis.tiler')
            # logTile.debug('Start tiling process with multiprocessing')
            parallel_map(process_src, srcDefOpt)
            # logTile.debug('End tiling process with multiprocessing')
        except Exception as e:
            logGdalTiler.error('{}'.format(e))

            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logGdalTiler.debug('{}::{}::{}'.format(exc_type, fname, exc_tb.tb_lineno))

            sys.exit()
            # __init__()


if __name__ == '__main__':
    argv = sys.argv
    if sys.argv:
        gdaltiler = GdalTiler(argv[1:])
