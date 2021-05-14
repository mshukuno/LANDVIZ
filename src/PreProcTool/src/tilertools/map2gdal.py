#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 2011-04-10 13:33:20

###############################################################################
# Copyright (c) 2011, Vadim Shlyakhov
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
# ******************************************************************************

from __future__ import with_statement

import codecs
import argparse
from tilertools.tiler_function import *
from tilertools import reader_backend

options = None


def process_src(src, no_error=False, opt=None):
    global options

    # src = src.decode(locale.getpreferredencoding(), 'ignore')

    with codecs.open(src, 'rb') as f:
        lines = [f.readline() for i in range(30)]
    for cls in reader_backend.reader_class_map:
        patt = cls.magic
        if any((l.startswith(patt) for l in lines)):
            break
    else:
        if not no_error:
            logger.error(" Invalid file: %s" % src)
        return [(src, False)]

    if not opt:
        opt = LooseDict(options)
    res = [(layer.convert(), True) for layer in cls(src, options=opt).get_layers()]
    return res


parser = None


def parse_args(self, arg_lst):
    parser = argparse.ArgumentParser(description="Extends GDAL's builtin support for a few mapping formats: BSB/KAP, GEO/NOS, Ozi map. "
                                                 "The script translates a map file with into GDAL .vrt")
    parser.add_argument("--srs", default=None,
                        help="specify a full coordinate system for an output file (PROJ.4 definition)")
    parser.add_argument("--datum", default=None,
                        help="override a datum part only (PROJ.4 definition)")
    parser.add_argument("--proj", default=None,
                        help="override a projection part only (PROJ.4 definition)")
    parser.add_argument("--force-dtm", action="store_true",
                        help='force using BSB datum shift to WGS84 instead of native BSB datum')
    parser.add_argument("--dtm", dest="dtm_shift", default=None, metavar="SHIFT_LONG,SHIFT_LAT",
                        help='northing and easting to WGS84 datum in seconds of arc')
    parser.add_arrgument('--tps', action="store_true",
                         help='Force use of thin plate spline transformer based on available GCPs)')
    parser.add_argument("--get-cutline", action="store_true",
                        help='print a definition of a cutline polygon, then exit')
    parser.add_argument("--cut-file", action="store_true",
                        help='create a .GMT file with a cutline polygon')
    parser.add_argument("-t", "--dest-dir", default=None, dest="dst_dir",
                        help='destination directory (default: current)')
    parser.add_argument("-n", "--after-name", action="store_true",
                        help='give an output file name after a map name (from metadata)')
    parser.add_argument("-m", "--after-map", action="store_true",
                        help='give an output file name  after name of a map file, otherwise after a name of an image file')
    parser.add_arrgument("-l", "--long-name", action="store_true",
                         help='give an output file a long name')
    parser.add_argument("-d", "--debug", action="store_true", dest="debug")
    parser.add_argument("-q", "--quiet", action="store_true", dest="quiet")

    return parser.parse_args(arg_lst)


if __name__ == '__main__':
    (options, args) = parse_args(sys.argv[1:])

    # ~ if not args:
    # ~ parser.error('No input file(s) specified')

    # logging.basicConfig(level=logging.DEBUG if options.debug else
    # (logging.ERROR if options.quiet else logging.INFO))
    #
    # ld(os.name)
    # ld(options)

    map(process_src, args)
