# Copyright (c) 2015-2016 MaxPoint Interactive, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#    disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
zapper.py -- A tool to build Python Zipapps.

The zipapp tool is introduced in python 3.5, but this script is an
    attempt to provide some of that functionality now.

the idea is to read a 'build' file that has an entry point, then
    create a '__main__.py' file that calls that entry point.
"""
from __future__ import absolute_import

import os
import argparse

import yaml

from zapper.zapper import Zapper  # Now THAT'S an import
from zapper.utils import file_exists


def _parse_args():
    """
    Parse Command Line Args.

    Returns:
        argparse object.

    Raises:
        ValueError if 'src' path is invalid.
    """

    # Set up our argument parser.
    parser = argparse.ArgumentParser(
        description='A tool to build python zipapps.',
        usage='%(prog)s SRC_PATH [DEST_PATH]'
    )

    parser.add_argument('src_path',
                        nargs=1,
                        type=str,
                        help='Path to the app to build.')
    parser.add_argument('dest_path',
                        nargs='?',
                        type=str,
                        help='The desired destination.')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        default=False,
                        help='Toggle verbosity.')

    args = parser.parse_args()

    # Ensure the provided Source Path exists, and raise a
    #   ValueError if it does not.
    args.src_path = args.src_path[0]
    if not file_exists(args.src_path):
        raise ValueError('"{0}" does not exist or is not readable!'
                         .format(args.src_path))

    return args


def _read_build_file(src_path):
    """
    Read the 'build' file.

    Args:
        src_path (str):     The path to the source code.

    Returns:
        dict containing contents of 'build' file.

    Raises:
        ValueError if we can't find a build file.
        ValueError if build file does not contain 'zapper' key.
    """

    # Possible names for the build file. 'build' and 'build.yml'
    #   seemed sensible enough.
    possible_build_file_names = ['build', 'build.yml', 'build.yaml']

    # Look for a file named either 'build' or 'build.yml'
    build_file = None
    for build_file_name in possible_build_file_names:
        build_file_path = os.path.join(src_path, build_file_name)
        if file_exists(build_file_path):
            build_file = build_file_path
            break

    # If the build file doesn't exist, bomb out.
    if not build_file:
        raise ValueError(
            'Build file not found in source directory: {0}'.format(src_path))

    # Read a build file located in the source path.
    with open(build_file, 'r') as f:
        build_data = yaml.load(f.read())

    # We require that the build file have a zapper "root" key,
    #   so we'll raise a ValueError if it does not.
    if 'zapper' not in build_data:
        raise ValueError('"{0}" does not contain a "zapper" key!'
                         .format(src_path))

    return build_data['zapper']


def _zap(src, dest, opts, verbose):
    """
    Run Zapper!

    Args:
        opts (dict):        Zapper opts
    """

    zapper = Zapper(src_directory=src,
                    dest=dest,
                    entry_point=opts.get('entry_point'),
                    app_name=opts.get('app_name'),
                    requirements=opts.get('requirements'),
                    requirements_txt=opts.get('requirements_txt'),
                    ignore=opts.get('ignore'),
                    clean_pyc=opts.get('clean_pyc'),
                    debug=verbose)
    zapper.build()


def main():
    """
    Main
    """

    # Gather up our arguments and options
    args = _parse_args()
    zapper_opts = _read_build_file(args.src_path)

    # If we have multiple entries in the 'zapper' portion of
    #   the build config, loop through them all. Otherwise
    #   just run once.
    if isinstance(zapper_opts, list):
        for instance_opts in zapper_opts:
            _zap(args.src_path, args.dest_path, instance_opts, args.verbose)

    else:
        _zap(args.src_path, args.dest_path, zapper_opts, args.verbose)
