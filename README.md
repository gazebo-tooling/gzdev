# gzdev-core
[![Build Status](https://travis-ci.org/osrf/gzdev.svg?branch=dev-core)](https://travis-ci.org/osrf/gzdev)
```
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
# gzdev-spawn
[![Build Status](https://travis-ci.org/osrf/gzdev.svg?branch=dev-spawn)](https://travis-ci.org/osrf/gzdev)
```
Usage:
	gzdev spawn [<gzv> | --gzv=<number>]
	            [<ros> | --ros=<distro_name>]
	            [<config> | --config=<file_name>]
	            [<pr> | --pr=<number>]
	            [--yes]
	gzdev spawn -h | --help
	gzdev spawn --version

Options:
	-h --help               Show this screen.
	--version               Show gzdev's version.
	--gzv=<number>          Gazebo version number.
	--ros=<distro_name>     ROS distribution name.
	--config=<file_name>    Gazebo world configuration file.
	--pr=<number>           Gazebo branch to compile from based on Pull Request #.
	--yes                   Confirm selection of unofficial ROS + Gazebo version.
```
