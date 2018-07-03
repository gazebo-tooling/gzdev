# gzdev [![Build Status](https://travis-ci.org/osrf/gzdev.svg?branch=master)](https://travis-ci.org/osrf/gzdev)
gzdev is a tool that facilitates the development of the open source robotics simulator Gazebo. The tool aims to streamline many of the usual tasks that Gazebo developers face on a daily basis.

# core
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
```

# spawn
```
Usage:
	gzdev spawn [<gzv> | --gzv=<number>]
	            [<ros> | --ros=<distro_name>]
	            [<config> | --config=<file_name>]
	            [<pr> | --pr=<number>]
	            [--dev | --source]
	            [--yes]
	gzdev spawn -h | --help
	gzdev spawn --version

Options:
	-h --help               Show this screen
	--version               Show gzdev's version
	--gzv=<number>          Gazebo release version number
	--ros=<distro_name>     ROS distribution name
	--config=<file_name>    World configuration file
	--pr=<number>           Branch to compile from based on Pull Request #
	--dev                   Install Gazebo development libraries
	--source                Build Gazebo/ROS from source
	--yes                   Confirm selection of unofficial ROS + Gazebo version
```
