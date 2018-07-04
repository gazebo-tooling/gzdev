"""
Gazebo Dev Tool.

Usage:
	gzdev [--version] [--help]
	      <command> [<args>...]
	gzdev -h | --help
	gzdev --version

Options:
	-h --help      Show this screen.
	--version      Show gzdev's version.

Commands/Plugins:
	spawn          Spawn a virtual environment ready for development.

"""

from docopt import docopt
from importlib import import_module

if __name__ == '__main__':
	args = docopt(__doc__, version='gzdev-core 0.1.0', options_first=True)
	command = args['<command>']
	plugin = import_module("plugins." + command)
	plugin.main()
