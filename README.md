# gzdev [![Build Status](https://travis-ci.org/osrf/gzdev.svg?branch=master)](https://travis-ci.org/osrf/gzdev) [![Build Status](https://build.osrfoundation.org/job/gzdev-ci-pr_any-xenial-amd64/badge/icon)](https://build.osrfoundation.org/job/gzdev-ci-pr_any-xenial-amd64)
gzdev is a command line tool that facilitates the development of the open source robotics simulator Gazebo. The tool aims to streamline many of the usual tasks that Gazebo developers face on a daily basis.

# Installation

**Prerequisites**
* [Python](https://www.python.org/downloads/) - Version 3.5 or greater recommended
* [Xpra](https://www.xpra.org/trac/wiki/Download) - Multi-platform screen and application forwarding system a.k.a. screen for X11. Required for Mac OS X and Windows, but optional for Linux

1. Clone the repository  
`git clone https://github.com/osrf/gzdev.git && cd gzdev`

2. Install the necessary python packages [docker](https://pypi.org/project/docker), [docopt](https://pypi.org/project/docker/), and [pytest](https://pypi.org/project/pytest/) (optional)  
`pip3 install -r requirements.txt`

3. Create an alias pointing to the core python script and add it to your ~/.bashrc  
`alias gzdev=`/full/path/to/`gzdev.py`

# Usage
## core
```
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
	spawn          Spawn a virtual environment ready for development.
```

## spawn
```
Spawn various Gazebo versions and ROS distributions inside docker containers.

Usage:
	gzdev spawn [<gzv> | --gzv=<number>]
	            [<ros> | --ros=<distro_name>]
	            [<config> | --config=<file_name>]
	            [<pr> | --pr=<number>]
	            [--dev | --source]
	            [--yes]
	            [--nvidia]
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
	--nvidia                Select nvidia as the runtime for the container.
```
## Basic Examples
`gzdev spawn 9`

`gzdev spawn 9 --nvidia`

When looking to build Gazebo from source first do the folllowing at the root of the gzdev directory:  
`mkdir gazebo && cd gazebo`  
`export GZV=9 && bash ../docker/gzsrc/gzrepos.sh`  

*Notice that the $GZV environment variable specifies the Gazebo version #, and colcon, vcstool, and mercurial are required to run the script.  
These can be installed with pip3:  
`pip3 install colcon-common-extensions vcstool`  
and pip (python2.7 version):  
`pip install mercurial`

Then the following command will build the docker image, mount the gazebo source code directory into the running container, compile from source, set up the environment, and finally run gazebo  
`gzdev spawn 9 --source`

# Support/Contribute
* [GitHub Issue Tracker](https://github.com/osrf/gzdev/issues) - gzdev specific questions
* [Gazebo Answers](http://answers.gazebosim.org) - Gazebo specific questions
* [Gazebo Community](https://community.gazebosim.org) - General Discussion

# License
The project is licensed under the Apache License, Version 2.0.
