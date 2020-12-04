# gzdev [![Build Status](https://travis-ci.org/osrf/gzdev.svg?branch=master)](https://travis-ci.org/osrf/gzdev) [![Build Status](https://build.osrfoundation.org/job/gzdev-ci-pr_any-xenial-amd64/badge/icon)](https://build.osrfoundation.org/job/gzdev-ci-pr_any-xenial-amd64)
gzdev is a command line tool that facilitates the development of the open source robotics simulator Gazebo. The tool aims to streamline many of the usual tasks that Gazebo developers face on a daily basis.

# Installation

**Prerequisites**
* [Python](https://www.python.org/downloads/) - Version 3.5 or greater recommended

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
        repository     Enable/Disable gazebo repositories.
```

## repository
```
System operations to manage extra repositories affecting Gazebo/Ignition/ROS

Usage:
	gzdev repository (ACTION) [<repo-name>] [<repo-type>] [--project=<project_name>]
        gzdev repository list
	gzdev repository (-h | --help)
	gzdev repository --version
Action:
        enable                  Enable repository in the system
        disable                 Disable repository (if present)
        list                    List repositories enabled
Options:
	-h --help               Show this screen
	--version               Show gzdev's version
"""
```
## Basic examples
`gzdev repository enable osrf prerelease`

## Per project configuration
Some projects require prerelease or nigthly repositories in order to work in early
stages.

`gzdev repository enable --project=ignition-math6`

# Support/Contribute
* [GitHub Issue Tracker](https://github.com/osrf/gzdev/issues) - gzdev specific questions
* [Gazebo Answers](http://answers.gazebosim.org) - Gazebo specific questions
* [Gazebo Community](https://community.gazebosim.org) - General Discussion

# License
The project is licensed under the Apache License, Version 2.0.
