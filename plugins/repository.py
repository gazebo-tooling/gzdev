# Copyright 2018 David Rosa
# Licensed under the Apache License, Version 2.0
"""
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

from docopt import docopt
import imp
from os import environ
from os.path import dirname, realpath, isfile, join
import re
from subprocess import run, PIPE, CalledProcessError, check_call
from sys import stderr
import pathlib
import platform
import yaml

def _check_call(cmd):
    print('')
    print("Invoking '%s'" % ' '.join(cmd))
    print('')

    try:
        check_call(cmd)
    except Exception as e:
        print(str(e))

def error(msg):
    print("\n" + msg + "\n", file=stderr)
    exit(-1)

def load_config_file(config_file_path = 'config/repository.yaml'):
    fn = pathlib.Path(__file__).parent / config_file_path
    with open(str(fn), 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            return config
        except yaml.YAMLError as exc:
            print(exc)
            exit(-1)

def load_project(project, config):
    for p in config['projects']:
        pattern = re.compile(p['name'])
        if pattern.search(project):
            return p['repositories']
            # stop in the first match
            break

    error("Unknown project: " + project)


def get_platform():
    return platform.linux_distribution()[2]

def get_repo_key(repo_name, config):
    for p in config['repositories']:
        if p['name'] == repo_name:
            return p['key']

    error("No key in repo: " + repo_name)

def get_repo_url(repo_name, repo_type, config):
    for p in config['repositories']:
        if p['name'] == repo_name:
            for t in p['types']:
                if t['name'] == repo_type:
                    return t['url']

    error("Unknown repository or type: " + repo_name + "/" + repo_type)


def get_sources_list_file_path(repo_name, repo_type):
    filename = "_gzdev_" + repo_name + "_" + repo_type + ".list"
    directory = "/etc/apt/sources.list.d"
    return directory + '/' + filename

def install_key(key):
    _check_call(['apt-key','adv','--keyserver','keyserver.ubuntu.com','--recv-keys', key])

def run_apt_update():
    _check_call(['apt-get','update'])

def install_repos(project_list, config):
    for p in project_list:
        install_repo(p['name'], p['type'], config)

def install_repo(repo_name, repo_type, config):
    url = get_repo_url(repo_name, repo_type, config)
    key = get_repo_key(repo_name, config)
    content = "deb " + url + " " + get_platform() + " main"
    full_path = get_sources_list_file_path(repo_name, repo_type)

    if isfile(full_path):
        error("gzdev file with the repositoy already exist in the system")

    install_key(key)

    try:
        f = open(full_path,'w')
        f.write(content)
        f.close()
    except PermissionError:
        print("No permissiong to install " + full_path + ". Run the script with sudo.")

    run_apt_update()

def disable_repo(repo_name):
    print("disable feature not implemented yet")

def normalize_args(args):
    action = args["ACTION"]
    repo_name = args["<repo-name>"] if args["<repo-name>"] else "osrf"
    repo_type = args["<repo-type>"] if args["<repo-type>"] else "stable"
    project = args["--project"]

    return action, repo_name, repo_type, project

def validate_input(args, config):
    action, repo_name, repo_type, project = args

    if (action == "enable" or action == "disable" or action =="list"):
        True
    else:
        error("Unknown action: " + action)

def process_input(args, config):
    action, repo_name, repo_type, project = args

    if project:
        project_list = load_project(project, config)

    if (action == "enable"):
        install_repos(project_list, config)
    elif (action == "disable"):
        disable_repo(repo_name)

def main():
    try:
        args = normalize_args(docopt(__doc__, version="gzdev-repository 0.1.0"))
        config = load_config_file()
        validate_input(args, config)
        process_input(args, config)
    except KeyboardInterrupt:
        print("spawn was stopped with a Keyboard Interrupt.\n")


if __name__ == '__main__':
    main()
