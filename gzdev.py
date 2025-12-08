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

from importlib import import_module
import logging
import os
import pkgutil
import sys

from docopt import docopt


def get_plugins():
    plugins = {}
    plugins_path = os.path.join(os.path.dirname(__file__), "plugins")
    for _, name, _ in pkgutil.iter_modules([plugins_path]):
        plugins[name] = True
    return plugins


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    args = docopt(str(__doc__), version="gzdev-core 0.1.0", options_first=True)
    cmd = args["<command>"]

    plugins = get_plugins()

    if cmd in plugins:
        plugin = import_module(f"plugins.{cmd}")
        plugin.main()
    else:
        logging.error(f"\nERROR: `{cmd}` is not a valid gzdev plugin.\n")


if __name__ == "__main__":
    main()
