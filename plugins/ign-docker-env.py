#
# Copyright (C) 2020 Open Source Robotics Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
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
    --vol $LOCAL_PATH:$CONTAINER_PATH   Load volumes into Docker container (separate multiple volumes with '::')

Notes:
    Valid inputs for IGN_RELEASE are 'citadel', 'dome', 'edifice', and 'fortress'.
    Valid inputs for the --linux-distro arg are 'ubuntu:bionic' or 'ubuntu:focal'.
"""

from docopt import docopt
from subprocess import check_call
from sys import stderr
import os
import time


ROCKER_CMD = ['rocker', '--x11', '--user']

# TODO: use a yaml file to get this information
# keep track of all valid versions and their default linux distro
bionic = 'ubuntu:bionic'
focal = 'ubuntu:focal'
IGN_VERSIONS = {
        'citadel' : bionic,
        'dome' : bionic,
        'edifice' : focal,
        'fortress' : focal
        }


# TODO: migrate this to use a gpu python library
def get_gpu_params():
    # check for nvidia
    for x in os.listdir('/dev/'):
        if x.startswith('nvidia'):
            return ['--nvidia']
    # check for intel
    if not os.path.isdir('/dev/dri'):
        return []
    for x in os.listdir('/dev/dri/'):
        if x.startswith('card'):
            return [f'--devices /dev/dri/{x}']
    return []


def _check_call(cmd):
    print('')
    print('Invoking '%s'' % ' '.join(cmd))
    print('')
    # sleep temporarily so that users can see the command being used
    time.sleep(1)

    try:
        check_call(cmd)
    except Exception as e:
        print(str(e))


def error(msg):
    print(f'\n {msg} \n', file=stderr)
    exit(-1)


def build_rocker_command(igniton_release, linux_distro, docker_args, vol_args):
    _, linux_distro_release = linux_distro.split(':')
    cmd = ROCKER_CMD + get_gpu_params()
    cmd += ['--ignition', f'{igniton_release}:{linux_distro_release}']
    cmd += docker_args if docker_args else []
    cmd += vol_args if vol_args else []
    cmd += [linux_distro, '/bin/bash']
    return cmd


def normalize_args(args):
    ignition_version = args['IGN_RELEASE']

    if args['--linux-distro']:
        linux_distro = args['--linux-distro']
    else:
        linux_distro = IGN_VERSIONS[ignition_version]

    docker_args = args['--rocker-args'].split(' ') if args['--rocker-args'] else None

    vol_args = ['--vol', args['--vol']] if args['--vol'] else None

    return ignition_version, linux_distro, docker_args, vol_args


def main():
    try:
        ignition_version, linux_distro, docker_args, vol_args = normalize_args(docopt(__doc__, version='gzdev-docker-env 0.1.0'))
        rocker_cmd = build_rocker_command(ignition_version, linux_distro, docker_args, vol_args)
        _check_call(rocker_cmd)
    except KeyError:
        print('Invalid value given for IGN_RELEASE. Please choose from ', list(IGN_VERSIONS.keys()))
    except KeyboardInterrupt:
        print('docker-env was stopped with a Keyboard Interrupt.\n')


if __name__ == '__main__':
    main()
