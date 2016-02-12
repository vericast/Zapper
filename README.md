# Zapper

Script to create Python Zipapps.

In python 3.5 theres a tool added that leverages an under-advertised feature of python, which is that the interpreter has the ability to read in, and potentially execute a zipfile. Python 3.5 adds zipapp, which simplifies a lot of the process for you. Since most Linux distros are well behind at 2.7, I wrote a stop gap script that seems to work pretty well for me.

Essentially it:

1. Reads a 'build' file that contains some metadata about the project.
2. Creates a `__main__.py` inside of the project directory that references some entry_point.
3. Installs any dependencies found in a requirements.txt
4. Zips up the package.
5. Write a python shebang into the zipfile.
6. chmod +x 's it.

Then boom, you can directly execute that script/application.

I've included a sample project that can easily be compiled down into a zipapp.

## Why?

This tool was built to fit some requirements I have when deploying code. Deploying python projects is kind of a pain. You have to copy over some flat file structure (or a zip, and unpack it somewhere), then you have to install requirements, preferably in a virtualenv, and some of those requirements will require compile headers...

It's just kind of a pain. As much as I love Python, I really wanted something like a jar. Pex is a great solution, but is kind of clumsy outside of pants. Pyz is a great solution, but required apps to be formatted a certain way, and would require a lot of education for other teams.

Enter Zapper. Zapper is something I can easily deploy as a Jenkins build job, and only really needs to know about where to find your main entry point. Assuming you've formatted the project like a sane python project, it should just kind of work.

## Usage

```bash
zapper SRC_PATH [DEST_PATH]
```

For zapper to work, the source path you point it at must have a yaml formatted file called build. Generally, it will look a little like:

```yaml
zapper:
  entry_point: zapper.cli:main
```

The reason I require a parent key for Zapper is that this tool was built for work, and our build system will have other things that read this same file.

Here's a list of all the current supported options:

```yaml
zapper:
  entry_point: module.path:entry_point comma,separated,parameters
  app_name: over_write_default_app_name
  requirements:
    - list
    - of
    - requirements
  requirements_txt: path/to/requirements.txt
  ignore:
    - list
    - of
    - files
    - to
    - ignore
  clean_pyc: True
```

If you have an application that you want to generate multiple zipapps from, you can supply a yaml list instead:

```yaml
zapper:
  - entry_point: my.app.cli:main
    app_name: main_app
    ignore:
      - utils

  - entry_point: my.app.cli:secondary
    app_name: second_app

  - entry_point: my.app.util:ternary someParameter
    app_name: utility_app
    requirements:
      - requests
      - jinj2
```

Any specified requirements will be loaded into a 'vendor' directory inside of the package. The generated `__main__.py` will then add that directory to the sys.path at run time. Note that you will still require a system level interpreter, and you aren't ENTIRELY isolated from system level packages, but that was outside of the scope of this project.

## Assumptions

Zapper makes a few assumptions about both your project and your environment.

* Pip must be installed.
  - Zapper uses Pip to install any dependencies, without it, zapper will complain.
* Zapper assumes you have a 'requirements.txt' file within your project. If you do not, no dependencies will be installed.
  - A 'requirements.txt' file is a file included in your project that lists out all the lirbraries (and the version of that library) that your application is dependent upon. This is generally a fairly common practice in Python. Read more about it [here](https://pip.readthedocs.org/en/1.1/requirements.html).

## Build Example Project

There's a very basic example "Hello, World" project inside the "example" directory. If you want to create a zipapp from that project, just run:

```bash
zipapp example/example_project example -v
```


# License

Copyright (c) 2015-2016 MaxPoint Interactive, Inc.

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
   disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
   products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
