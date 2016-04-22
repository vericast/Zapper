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
zapper.py -- Class for main zapper code.

The idea is to read a 'build' file that has an entry point, then
    create a '__main__.py' file that calls that entry point.
"""
from __future__ import absolute_import

import os
import zipfile
from shutil import rmtree

from zapper.utils import render_template, file_exists, shell_out, list_files, which

# Check if the user has zlib installed
try:
    import zlib
    has_zlib = True
except ImportError:
    has_zlib = False


class Zapper(object):
    """
    Create a Python ZipApp
    """

    # The Standard Python Shebang header.
    default_python_shebang = '#!/usr/bin/env python'

    # List to keep track of any files we create.
    files_created = []

    def __init__(self,
                 src_directory,
                 entry_point,
                 python_shebang=None,
                 dest=None,
                 app_name=None,
                 requirements=None,
                 requirements_txt=None,
                 ignore=None,
                 clean_pyc=True,
                 debug=False):
        """
        Constructor

        Args:
            src_directory (str):        The path to the artifact.
            entry_point (str):          The entrypoint for the zipapp.
            app_name (str):             Override default app name.
            requirements (list):        Requirements for the package.
            requirements_txt (str):     Path to a requirements.txt file.
            ignore (list):              Files to ignore.
            clean_pyc (bool):           If True, clean out *.pyc files before
                                            creating zipapp.
            debug (bool):               Debug mode.

        Raises:
            ValueError when unable to resolve 'app_name'.
        """

        self.python_shebang = python_shebang or self.default_python_shebang
        self.src_directory = src_directory
        self.dest = dest
        self.entry_point = entry_point
        self.requirements = requirements
        self.debug = debug

        # If we're given a path to a requirements.txt file, ensure we have
        #   an absolute path.
        # If a path is not provided, we'll assume it exists in the
        #   src_directory, and verify that later.
        if requirements_txt:
            if not os.path.isabs(requirements_txt):
                self.requirements_txt = os.path.join(self.src_directory, requirements_txt)
            else:
                self.requirements_txt = requirements_txt
        else:
            self.requirements_txt = os.path.join(self.src_directory, 'requirements.txt')

        self._debug('requirements_txt set to: "{0}"'.format(self.requirements_txt))

        # If ignore is not set, we'll at least check for standard
        #   virtualenvironment names.
        if not ignore:
            self.ignore = ['venv', 'env']  # Standard generic virtualenv names.
        else:
            self.ignore = ignore

        self._debug('ignore set to: "{0}"'.format(self.ignore))

        # If a dest is not provided, just go one level up from the
        #   src_directory.
        if not dest:
            self.dest = os.path.dirname(self.src_directory)
        else:
            self.dest = dest

        self._debug('dest set to: "{0}"'.format(self.dest))

        # If we haven't specified the app_name, try to resolve one
        #   from the directory name.
        if not app_name:
            if self.src_directory.endswith('/'):
                tmp_src_directory = self.src_directory[:-1]
            else:
                tmp_src_directory = self.src_directory

            self.app_name = '{0}.pyz'.format(os.path.basename(tmp_src_directory))
            if not self.app_name:
                raise ValueError('Unable to figure out app name!')

        else:
            self.app_name = app_name

        self._debug('app name set to: "{0}"'.format(self.app_name))

        self.dest_path = os.path.join(self.dest, self.app_name)

        self.clean_pyc = clean_pyc
        self.vendor_path = os.path.join(src_directory, 'vendor')

    def __del__(self):
        """
        Destructor
        """

        self._clean()

    def _debug(self, msg):
        """
        Check if debug is toggled, and if so, print a message.

        Args:
            msg (str):          The message to display.
        """

        if self.debug:
            print(msg)

    def _prepend_shebang(self):
        """
        Open a file and write a python shebang as the first line.
        """

        self._debug('Prepending python shebang "{0}" to "{1}"'
                    .format(self.python_shebang, self.dest_path))

        # Read in the file, rewind to the top, write our header line, then
        #   write all the contents back.
        with open(self.dest_path, 'r+') as f:
            file_content = f.read()
            f.seek(0, 0)
            f.write('{0}\n{1}'.format(self.python_shebang, file_content))

    def _create_main(self):
        """
        Template out and write a __main__ file.

        Template out and write a '__main__.py' file that calls the
            entry point specified in the 'build' file like so:

                sys.exit(entry_point(parameters))

        Raises:
            ValueError if the supplied entry point isn't formatted
                as: "module_name:main_function params"
        """

        self._debug('Creating __main__.py')

        # Attempt to parse any paremeters out of the entry point.
        parameters = None
        try:
            self.entry_point, parameters = self.entry_point.split()
        except ValueError:
            pass

        self._debug('Parameters Found: "{0}"'
                    .format(parameters if parameters else 'None'))

        # Attempt to parse out the module path and entry_point from
        #   self.entry_point.
        try:
            module_path, entry_point = self.entry_point.split(':')
        except ValueError:
            raise ValueError('"{0}" is a malformed entry point! '
                             'It should be formatted like: '
                             '"module_name:main_function"'
                             .format(self.entry_point))

        self._debug('Module Path: "{0}"\nEntry Point: "{1}"'
                    .format(module_path, entry_point))

        # Path to place our '__main__.py' file.
        main_path = os.path.join(self.src_directory, '__main__.py')

        # Write out our templated __main__.py file.
        self._debug('Writing "{0}"'.format(main_path))
        with open(main_path, 'w') as f:
            f.write(render_template('__main__.py.j2',
                                    module_path=module_path,
                                    entry_point=entry_point,
                                    parameters=parameters))

        # Note that we created a file at 'main_path'.
        self.files_created.append(main_path)

    def _install_requirements(self):
        """
        Install specified dependencies to a 'vendor' directory.

        If requirements are defined in the build file, install those to
            a 'vendor' directory. If they are not defined, read the
            'requirements.txt' file (if it exists) and install those to
            a 'vendor' directory.

        Raises:
            OSError if Pip is not installed.
        """

        # On windows, pip is 'pip.exe', but everywhere else its pip.
        if os.name == 'posix':
            pip_name = 'pip'
        else:
            pip_name = 'pip.exe'

        # Test if Pip is installed and bomb if it's not.
        pip_cmd = which(pip_name)
        if not pip_cmd:
            raise OSError('Required program "pip" not installed!')

        # Check if our vendor path exists, and if it doesn't,
        #   create it. This way if a project already has one,
        #   I don't step on too many toes.
        self._debug('Installing Dependencies.')
        if not file_exists(self.vendor_path):
            self._debug('Creating "{0}"'.format(self.vendor_path))
            os.makedirs(self.vendor_path)
            self.files_created.append(self.vendor_path)

        # Loop through provided requirements and install
        #   run 'pip install'
        if self.requirements:
            self._debug('Requrements List provided.')
            for requirement in self.requirements:
                cmd = [
                    'pip',
                    'install',
                    '{0}'.format(requirement),
                    '--target={0}'.format(self.vendor_path),
                ]

                self._debug('Installing "{0}"" with command "{1}"'
                            .format(requirement, self.vendor_path))

                output = shell_out(cmd)
                self._debug('{0}'.format(output))

        # If a requirements.txt file is provided, feed it to 'pip'
        #   and install everything to the vendor directory.
        if self.requirements_txt:
            if not file_exists(self.requirements_txt):
                self._debug('"requirements.txt" not found at: "{0}"'
                            .format(self.requirements_txt))
                return

            cmd = [
                'pip',
                'install',
                '-r',
                '{0}'.format(self.requirements_txt),
                '--target={0}'.format(self.vendor_path),
            ]

            self._debug('Running command: "{0}"'.format(cmd))

            output = shell_out(cmd)
            self._debug('{0}'.format(output))

    def _ignored(self, fpath):
        """
        Check if a file or path is in the ignore list.

        Args:
            fpath (str):        Filepath or file name
        """

        for ignore_file in self.ignore:
            # Check for a perfect match
            if fpath in ignore_file:
                return True

            # Check if a relative path matches
            rel_path = os.path.relpath(fpath, self.src_directory)
            if rel_path in ignore_file:
                return True

            # Check if the filename/basename matches.
            fname = os.path.basename(fpath)
            if fname in ignore_file:
                return True

            # Check if we're in an ignored directory
            try:
                path_parts = rel_path.split('/')
            except:
                continue
            for part in path_parts:
                if part == ignore_file:
                    return True

        return False

    def _zip_directory(self):
        """
        Recursively zip a diorectory.
        """

        # Check if we have zlib installed -- which allows us to
        #   compress the resulting zip file. Otherwise just
        #   store it.
        if has_zlib:
            zmode = zipfile.ZIP_DEFLATED
            self._debug('Using ZIP_DEFLATED')
        else:
            zmode = zipfile.ZIP_STORED
            self._debug('Using ZIP_STORED')

        with zipfile.ZipFile(self.dest_path, 'w', zmode) as z:
            for f in list_files(self.src_directory):
                # Check ignore
                if self._ignored(f):
                    self._debug('Ignoring file "{0}"'.format(f))
                    continue

                rel_path = os.path.relpath(f, self.src_directory)

                self._debug('Writing "{0}" to zip archive.'.format(rel_path))

                z.write(f, rel_path)

    def _clean(self):
        """
        Clean up after myself.
        """

        self._debug('Cleaning up')

        # Loop through all files we've created, and attempt
        #   to remove them.
        for fpath in self.files_created:
            if not file_exists(fpath):
                continue

            self._debug('Removing "{0}"'.format(fpath))
            if os.path.isdir(fpath):
                rmtree(fpath)
            else:
                os.remove(fpath)

    def _clean_pyc(self):
        """
        Remove all files ending in '.pyc'.
        """

        self._debug('Cleaning out ".pyc" files')

        # Search for all files that end with the extension '.pyc'
        #   and remove them.
        for f in list_files(self.src_directory):
            if f.endswith('.pyc'):
                self._debug('Removing "{0}"'.format(f))
                os.remove(f)

    def build(self):
        """
        Build a zipapp.
        """

        # Clean out any pyc's we have.
        if self.clean_pyc:
            self._clean_pyc()

        # Create __main__.py.
        self._create_main()

        # Install Dependencies.
        self._install_requirements()

        # Zip up package.
        self._zip_directory()

        # write header into file.
        self._prepend_shebang()

        # enable execute flag on resulting artifact.
        self._debug('Setting execute flag on "{0}"'.format(self.dest_path))
        os.chmod(self.dest_path, 0755)
