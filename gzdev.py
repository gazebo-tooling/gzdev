#!/usr/bin/env python3

# Copyright 2018 David Rosa
# Licensed under the Apache License, Version 2.0
"""
Streamline many of the usual tasks that Gazebo developers face on a daily basis.

Usage:
        gzdev [--version] [--help]
              <command> [<args>...]
        gzdev -h | --help
        gzdev --version

Options:
        -h --help      Show this screen.
        --version      Show gzdev's version.

Commands/Plugins:
        ign-docker-env Launch a docker container with default Ignition project configuration
        repository     Enable/Disable gazebo repositories.
"""

from docopt import docopt
from importlib import import_module
from sys import stderr

if __name__ == '__main__':
    args = docopt(__doc__, version='gzdev-core 0.1.0', options_first=True)
    cmd = args['<command>']
    is_valid = {'ign-docker-env': True,
                'repository': True}

    if is_valid.get(cmd):
        plugin = import_module('plugins.' + cmd)
        plugin.main()
    else:
        print('\nERROR: `%s` is not a valid gzdev plugin.\n' % cmd, file=stderr)
