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
utils.py -- Conveincence functions for zapper.
"""
from __future__ import absolute_import

import os
import subprocess

from jinja2 import Environment, PackageLoader, TemplateNotFound, UndefinedError


def get_file_path(fname):
    """
    Return the path of a provided file.

    Args:
        fname (str): File to get path to.

    Returns:
        str
    """

    return os.path.dirname(os.path.realpath(fname))


def file_exists(fpath):
    """
    Check if a file exists and is readable.

    Args:
        fpath (str):        The file path to check.
    """

    if fpath is None:
        return False

    if os.path.exists(fpath) and os.access(fpath, os.R_OK):
        return True

    return False


def list_files(path):
    """
    Generator to Emulate something like:
        find ./ -f

    This will blow apart a directory tree and allow me to easily
        search for a file. Since this is a generator, it should
        be mitigate a lot of the ineffiency of walking the whold
        directory.

    Args:
        path (str): The path to traverse.

    Returns:
        str: files in the path.
    """

    for root, folders, files in os.walk(path):
        for filename in folders + files:
            yield os.path.join(root, filename)


def render_template(template_name, **kwargs):
    """
    Simple utility function to render out a specified template, using
        **kwargs to fill in variables.

    Args:
        template_path (str): The directory where we can find the template.
        template_name (str): The actual name of the template we want to
                                render.
        **kwargs (dict):     Key Value pairs of any variables we want rendered
                                out into the template.

    Raises:
        AncillaryFileNotFound:      If we cannot find the template.
        AncillaryUndefinedError:    If we run across an undefined variable.

    """

    # Attempt to load a Tempalte file from within the 'Zapper' package
    #   and raise an IOError if I'm unable to find it.
    try:
        env = Environment(loader=PackageLoader('zapper', 'templates'))
        template = env.get_template(template_name)
    except TemplateNotFound:
        raise IOError('Unable to find template {} in zapper!'
                      .format(template_name))

    # Attempt to render our template, and raise a Value Error if we
    #   run into any undefined variables.
    try:
        template_data = template.render(**kwargs)
    except UndefinedError as e:
        raise ValueError('Undefined variable found in {}! Error: {}'
                         .format(template_name, e))

    return template_data


def shell_out(cmd):
    """
    Run a shell command.

    Args:
        cmd (list):         A pre-tokenized command to run.
    """

    pid = subprocess.Popen(cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

    return pid.communicate()


def file_executable(fpath):
    """
    Check if a provided file path exists and is executable.

    Args:
        fpath (str):        The path to the file in question.
    """

    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def which(program):
    """
    Basically a Python implementation of 'which'.

    Search all PATHs in a users environment and see if a
        program of "program_name" exists there. Shutil
        has something for this in Python 3.3, but alas, I'm
        targeting 2.7+.

    Args:
        program (str):      The name of the program to search for.
    """

    # If I'm given a fully qualified path, just test that,
    #   otherwise, search the os's PATH environment variable
    program_path, program_name = os.path.split(program)
    if program_path:
        if file_executable(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if file_executable(exe_file):
                return exe_file

    return None
