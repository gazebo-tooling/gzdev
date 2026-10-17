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
        filter-build-and-test  Decide whether a change needs to be built and tested
        ign-docker-env         Launch a docker container with default Ignition project configuration
        repository             Enable/Disable gazebo repositories.
"""

from importlib import import_module
import sys

if __name__ == '__main__':
    # filter-build-and-test uses only the standard library. Dispatch it before
    # docopt is imported so it runs where gzdev's requirements are not
    # installed.
    if len(sys.argv) > 1 and sys.argv[1] == 'filter-build-and-test':
        filter_build_and_test = import_module('plugins.filter_build_and_test')
        sys.exit(filter_build_and_test.main(sys.argv[2:]))

    from docopt import docopt

    args = docopt(str(__doc__), version='gzdev-core 0.1.0', options_first=True)
    cmd = args['<command>']
    is_valid = {'ign-docker-env': True,
                'repository': True}

    if is_valid.get(cmd):
        plugin = import_module('plugins.' + cmd)
        plugin.main()
    else:
        print('\nERROR: `%s` is not a valid gzdev plugin.\n' % cmd, file=sys.stderr)
        sys.exit(1)
