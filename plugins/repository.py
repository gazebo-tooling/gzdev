# Copyright 2018 David Rosa
# Licensed under the Apache License, Version 2.0
"""
Actions related to adding/modifying apt repositories for ignition.

Usage:
        gzdev repository (ACTION) [<repo-name>] [<repo-type>]
            [--project=<project_name>] [--force-linux-distro=<distro>]
            [--keyserver=<keyserver>] [--gpg-check] [--pre-cleanup]
        gzdev repository list
        gzdev repository (-h | --help)
        gzdev repository --version

Action:
        enable                  Enable repository in the system
        disable                 Disable repository (if present)
        list                    List repositories enabled
        purge                   Remove all configurations installed by gzdev

Options:
        -h --help               Show this screen
        --version               Show gzdev's version
        --gpg-check             Do run a gpg check for validating the key
                                downloaded in enable action
                                (need the gpg binary)
        --pre-cleanup           Run 'purge' action before proceeding
"""

import distro
import logging
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request
import yaml
from typing import Any, Dict, List, Optional, Tuple, NoReturn

from docopt import docopt


GZDEV_FILE_PREFIX = "_gzdev_"


def _check_call(cmd: List[str]) -> None:
    logging.info("")
    logging.info(f"Invoking '{' '.join(cmd)}'")
    logging.info("")

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as ex:
        logging.error(ex)


def error(msg: str) -> NoReturn:
    logging.error(f"\n [err] {msg}\n")
    sys.exit(-1)


def warn(msg: str) -> None:
    logging.warning(f"\n [warn] {msg}\n")


def load_config_file(
    config_file_path: str = "config/repository.yaml",
) -> Dict[str, Any]:
    fn = pathlib.Path(__file__).parent / config_file_path
    with open(str(fn), "r") as stream:
        try:
            config = yaml.safe_load(stream)
            return config
        except yaml.YAMLError as exc:
            logging.error(exc)
            sys.exit(-1)


def get_first_valid_project_config(
    project: str, config: Dict[str, Any], linux_distro: str
) -> Optional[Dict[str, Any]]:
    """Returns the project configuration from yaml that correspond
    to the first match while searching starting from top to bottom
    """
    for p in config["projects"]:
        pattern = re.compile(p["name"])

        if pattern.search(project):
            # project name found, check that requirements are met
            try:
                requirements = p["requirements"]
                if linux_distro in requirements["distributions"][distro.id()]:
                    return p
            except KeyError as kerror:
                # 0. No requirments set
                if "requirements" in str(kerror):
                    return p
                # 1. No disitribution requirement set
                if "distributions" in str(kerror):
                    return p
                assert f"Unexpected keyerror: #{str(kerror)}"

    return None


def get_repositories_config(project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    return project_config["repositories"]


def get_linux_distro() -> str:
    return distro.id().lower()


def get_repo_key(repo_name: str, config: Dict[str, Any]) -> str:
    for p in config["repositories"]:
        if p["name"] == repo_name:
            return p["key"]

    error("No key in repo: " + repo_name)


def get_repo_key_url(repo_name: str, config: Dict[str, Any]) -> str:
    for p in config["repositories"]:
        if p["name"] == repo_name:
            return p["key_url"]

    error("No key in repo: " + repo_name)


def get_repo_url(repo_name: str, repo_type: str, config: Dict[str, Any]) -> str:
    for p in config["repositories"]:
        if p["name"] == repo_name and p["linux_distro"].lower() == get_linux_distro():
            for t in p["types"]:
                if t["name"] == repo_type:
                    return t["url"]

    error("Unknown repository or type: " + repo_name + "/" + repo_type)


def get_sources_list_file_path(repo_name: str, repo_type: str) -> str:
    filename = f"{GZDEV_FILE_PREFIX}{repo_name}_{repo_type}.list"
    directory = "/etc/apt/sources.list.d"
    return directory + "/" + filename


def key_filepath(repo_name: str, repo_type: str) -> str:
    return f"/usr/share/keyrings/{GZDEV_FILE_PREFIX}{repo_name}_{repo_type}.gpg"


def assert_key_in_file(key: str, key_path: str) -> None:
    output = subprocess.check_output(["gpg", "--show-keys", key_path])

    if key not in output.decode("ascii"):
        error(f"Key {key} was not found in file {key_path}")


def download_key(repo_name: str, repo_type: str, key_url: str) -> str:
    key_path = key_filepath(repo_name, repo_type)
    if os.path.exists(key_path):
        warn(
            f"keyring gpg file already exists in the system: {key_path}\n"
            "Overwritting to grab the new one."
        )
        os.remove(key_path)
    try:
        response = urllib.request.urlopen(key_url)
        if response.code == 200:
            with open(key_path, "wb") as file:
                file.write(response.read())
        else:
            error(str(response.code))
    except urllib.error.HTTPError as e:
        error(f"HTTPError: {e.code}")
    except urllib.error.URLError as e:
        error(f"URLError: {e.reason}")

    return key_path


def remove_deprecated_apt_key(key: str) -> None:
    _check_call(["apt-key", "del", key])


def run_apt_update() -> None:
    _check_call(["apt-get", "update"])


def install_repos(
    repos_list: List[Dict[str, Any]],
    config: Dict[str, Any],
    linux_distro: str,
    gpg_check: bool,
) -> None:
    for p in repos_list:
        install_repo(p["name"], p["type"], config, linux_distro, gpg_check)


def install_repo(
    repo_name: str,
    repo_type: str,
    config: Dict[str, Any],
    linux_distro: str,
    gpg_check: bool,
) -> None:
    url = get_repo_url(repo_name, repo_type, config)
    key = get_repo_key(repo_name, config)
    key_url = get_repo_key_url(repo_name, config)

    try:
        key_path = download_key(repo_name, repo_type, key_url)
        if gpg_check:
            assert_key_in_file(key, key_path)

        # if not linux_distro provided, try to guess it
        if not linux_distro:
            linux_distro = distro.codename()

        content = f"deb [signed-by={key_path}] {url} {linux_distro} main"
        full_path = get_sources_list_file_path(repo_name, repo_type)
        if os.path.isfile(full_path):
            warn(
                "gzdev file with the repositoy already exists in the system:"
                f"{full_path}. \n Overwritting to use new signed-by."
            )

        f = open(full_path, "w")
        f.write(content)
        f.close()

        run_apt_update()
    except PermissionError:
        logging.error(
            "No permissiong to make system file modifications. Run the script with sudo."
        )


def disable_repo(repo_name: str) -> None:
    logging.info("disable feature not implemented yet")


def normalize_args(
    args: Dict[str, Any],
) -> Tuple[str, str, str, Optional[str], str, bool, bool]:
    action = args["ACTION"]
    repo_name = args["<repo-name>"] if args["<repo-name>"] else "osrf"
    repo_type = args["<repo-type>"] if args["<repo-type>"] else "stable"
    project = args["--project"]
    force_linux_distro = args["--force-linux-distro"]
    gpg_check = args["--gpg_check"] if "--gpg_check" in args else False
    pre_cleanup = args["--pre-cleanup"] if "--pre-cleanup" in args else False
    if pre_cleanup and action != "enable":
        error(
            f'--pre-cleanup is only supported in the "enable" action(not in {action})'
        )
    if force_linux_distro:
        linux_distro = force_linux_distro
    else:
        linux_distro = distro.codename()
    if "--keyserver" in args and args["--keyserver"]:
        warn("--keyserver option is deprecated. It is safe to remove it")
    return action, repo_name, repo_type, project, linux_distro, gpg_check, pre_cleanup


def validate_input(args: Tuple[str, str, str, Optional[str], str, bool, bool]) -> None:
    action = args[0]
    if action in ["enable", "disable", "list", "purge"]:
        pass
    else:
        error(f"Unknown action: {action}")


def process_project_install(
    project: str,
    config: Dict[str, Any],
    linux_distro: str,
    gpg_check: bool,
    dry_run: bool = False,
) -> None:
    project_config = get_first_valid_project_config(project, config, linux_distro)
    if not project_config:
        error("Unknown project: " + project)

    if not dry_run:  # useful for tests
        install_repos(
            get_repositories_config(project_config), config, linux_distro, gpg_check
        )


def process_input(
    args: Tuple[str, str, str, Optional[str], str, bool, bool], config: Dict[str, Any]
) -> None:
    action, repo_name, repo_type, project, linux_distro, gpg_check, pre_cleanup = args

    if pre_cleanup:
        remove_all_installed()

    if action == "enable":
        if project:
            # project dependant installation
            process_project_install(project, config, linux_distro, gpg_check)
        else:
            # generic repository installation
            install_repo(repo_name, repo_type, config, linux_distro, gpg_check)
    elif action == "disable":
        disable_repo(repo_name)
    elif action == "purge":
        remove_all_installed()


def remove_file_by_pattern(directory: str, pattern: Any) -> None:
    for filename in os.listdir(directory):
        if pattern.match(filename):
            filepath = os.path.join(directory, filename)
            try:
                os.remove(filepath)
                logging.info(f"Removed: {filepath}")
            except OSError as e:
                logging.error(f"Error: {filepath} - {e}")


def remove_all_installed() -> None:
    # Remove installed apt directories
    remove_file_by_pattern(
        "/etc/apt/sources.list.d/", re.compile(r"^" + GZDEV_FILE_PREFIX + "(.*)\\.list")
    )
    # Remove installed keys
    remove_file_by_pattern(
        "/usr/share/keyrings/", re.compile(r"^" + GZDEV_FILE_PREFIX + "(.*)\\.gpg")
    )


def main() -> None:
    try:
        args = normalize_args(docopt(str(__doc__), version="gzdev-repository 0.2.0"))
        config = load_config_file()
        validate_input(args)
        process_input(args, config)
    except KeyboardInterrupt:
        logging.info("repository was stopped with a Keyboard Interrupt.\n")


if __name__ == "__main__":
    main()
