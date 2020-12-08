# gzdev ![CI](https://github.com/ignition-tooling/gzdev/workflows/CI/badge.svg) [![Build Status](https://build.osrfoundation.org/job/gzdev-ci-pr_any-xenial-amd64/badge/icon)](https://build.osrfoundation.org/job/gzdev-ci-pr_any-xenial-amd64)
gzdev is a command line tool that facilitates the development of the open source robotics simulator Gazebo. The tool aims to streamline many of the usual tasks that Gazebo developers face on a daily basis.

# Installation

**Prerequisites**
* [Python](https://www.python.org/downloads/) - Version 3.5 or greater recommended

1. Clone the repository:
```
git clone https://github.com/ignition-tooling/gzdev.git && cd gzdev
```

2. Install the necessary python packages [docker](https://pypi.org/project/docker), [docopt](https://pypi.org/project/docker/), and [pytest](https://pypi.org/project/pytest/) (optional). Also install [rocker](https://github.com/osrf/rocker) and [ign-rocker](https://github.com/adlarkin/ign-rocker) for the `ign-docker-env` command:
```
pip3 install -r requirements.txt
```

3. Create an alias pointing to the core python script and add it to your `~/.bashrc` (be sure to update the path in the command below):
```
alias gzdev=/ABSOLUTE/PATH/TO/gzdev.py
```

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
	ign-docker-env Launch docker environments ready for Ignition development
        repository     Enable/Disable gazebo repositories.
```

## ign-docker-env
(this command uses [rocker](https://github.com/osrf/rocker) and [ign-rocker](https://github.com/adlarkin/ign-rocker) - take a look at these repositories for more information)
```
Launch docker environments ready for Ignition development

Usage:
    gzdev ign-docker-env IGN_RELEASE
                [--linux-distro <linux-distro>]
                [--rocker-args ROCKER_ARGS]
                [--vol $LOCAL_PATH:$CONTAINER_PATH[::$LOCAL_PATH:$CONTAINER_PATH ...]]
    gzdev ign-docker-env -h | --help
    gzdev ign-docker-env --version

Options:
    -h --help                           Show this screen
    --version                           Show gzdev's version
    --linux-distro linux-distro         Linux distibution to use in docker env
    --rocker-args ROCKER_ARGS           Extra rocker arguments, captured in single quotes and separated by white space
    --vol $LOCAL_PATH:$CONTAINER_PATH   Load volumes into docker container (separate multiple volumes with '::')
```

### Basic examples
* Start a container with Ignition Citadel installed:
```
gzdev ign-docker-env citadel
```
* Start an Ubuntu Bionic container with Ignition Dome installed:
```
gzdev ign-docker-env dome --linux-distro ubuntu:bionic
```
* Start an Ubuntu Bionic container with Ignition Dome installed, passing in `/foo` locally as a volume into the container at `/bar`:
```
gzdev ign-docker-env dome --linux-distro ubuntu:bionic --vol /foo:/bar
```
* Start an Ignition Dome container with a user's `$HOME` directory mounted inside the container as a volume (among other things, this will allow dotfiles to be available in the container) - the path to `$HOME` in the container is the same as the local path to `$HOME`. Since `$HOME` is already mounted into the container, don't explicitly pass in any volumes with `--vol` that are a sub-directory of `$HOME`:
```
gzdev ign-docker-env dome --rocker-args '--home'
```
* Start a container with Ignition Citadel installed, loading two volumes: `/foo` locally into the container at `/bar`, and `/my_proj` locally into the container at `/ws`:
```
gzdev ign-docker-env citadel --vol /foo:/bar::/my_proj:/ws
```

### Using ign-docker-env to build Ignition repositories from source
1. Install [vcstool](https://github.com/dirk-thomas/vcstool)
2. Create a colcon workspace:
```
mkdir -p ~/colcon_ws/src/
export COLCON_WS_PATH=~/colcon_ws/
```
3. Determine the ignition version you'd like to work with (can be something like `citadel` or `dome`):
```
export IGN_DISTRO=citadel
```
4. Get all of the repositories needed to build `IGN_DISTRO` from source:
```
cd ~/colcon_ws/src/
wget 'https://raw.githubusercontent.com/ignition-tooling/gazebodistro/master/collection-'$IGN_DISTRO'.yaml'
vcs import < 'collection-'$IGN_DISTRO'.yaml'
```
5. Modify the repositories as needed (check out branches, make commits, etc.), and delete any repositories that you don't need to build from source
6. Start a container with your specified Ignition version, loading your colcon workspace into the container:
```
gzdev ign-docker-env $IGN_DISTRO --vol $COLCON_WS_PATH:/ws
```
7. Build the repositories in the workspace with colcon.
Make sure you go to the root of the workspace first:
```
cd /ws
```
Run the following command if you want to build tests:
```
colcon build --merge-install
```
Run the following command if you don't want to build tests:
```
colcon build --merge-install --cmake-args -DCMAKE_BUILD_TESTING=0
```
8. Source the workspace:
```
. /ws/install/setup.bash
```
9. Use Ignition!

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
```
## Basic examples
`gzdev repository enable osrf prerelease`

## Per project configuration
Some projects require prerelease or nigthly repositories in order to work in early
stages.

`gzdev repository enable --project=ignition-math6`

# Support/Contribute
* [GitHub Issue Tracker](https://github.com/ignition-tooling/gzdev/issues) - gzdev specific questions
* [Gazebo Answers](http://answers.gazebosim.org) - Gazebo specific questions
* [Gazebo Community](https://community.gazebosim.org) - General Discussion

# License
The project is licensed under the Apache License, Version 2.0.
