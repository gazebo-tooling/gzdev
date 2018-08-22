# Copyright 2018 David Rosa
# Licensed under the Apache License, Version 2.0
"""
Usage:
	gzdev spawn [<gzv> | --gzv=<number>]
				[<ros> | --ros=<distro_name>]
				[<config> | --config=<file_name>]
				[<pr> | --pr=<number>]
				[--dev | --source]
                [--pull]
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

"""

import docker
from docopt import docopt
from os import environ
from os.path import dirname, realpath
from subprocess import run, PIPE, CalledProcessError
from sys import stderr
from re import sub

# `official_ros_gzv` contains only the official Gazebo version
# chosen to go with a particular ROS release. Whereas `compatible` contains both
# officially and unofficially supported ROS/Gazebo combinations.
# `official_ros_gzv` is useful for auto-selecting and displaying the official
# Gazebo version that goes with a specified ROS distro when the user
# does not pass the --gzv parameter e.g. `gzdev spawn --ros=melodic`

official_ros_gzv = {"kinetic": 7, "lunar": 7, "melodic": 9}
gz7_ros = {}.fromkeys(["kinetic", "lunar"])
gz8_ros = {}.fromkeys(["kinetic", "lunar"])
gz9_ros = {}.fromkeys(["kinetic", "lunar", "melodic"])
compatible = {7: gz7_ros, 8: gz8_ros, 9: gz9_ros}
max_gzv = sorted(compatible.keys())[-1]


def normalize_args(args):
    gzv = args["<gzv>"] if args["<gzv>"] else args["--gzv"]
    ros = args["<ros>"] if args["<ros>"] else args["--ros"]
    config = args["<config>"] if args["<config>"] else args["--config"]
    pr = args["<pr>"] if args["<pr>"] else args["--pr"]
    confirm = args["--yes"]
    nvidia = args["--nvidia"]
    source = args["--source"]
    pull = args["--pull"]

    ros = ros.lower() if ros else None
    gzv = int(gzv) if gzv and gzv.isdecimal() else gzv
    if gzv == None and ros and ros in official_ros_gzv:
        gzv = official_ros_gzv[ros]

    return gzv, ros, config, pr, confirm, nvidia, source, pull


def error(msg):
    print("\n" + msg + "\n", file=stderr)
    exit(0)


def validate_input(args):
    gzv, ros, config, pr, confirm, nvidia, source, pull = args

    if type(gzv) is int and (gzv <= 0 or gzv > max_gzv) or type(gzv) is str:
        error("ERROR: '%s' is not a valid Gazebo version number." % gzv)

    if gzv and gzv not in compatible:
        error("ERROR: This tool does not support Gazebo %d." % gzv)
    elif not gzv and not ros:
        error("ERROR: Gazebo version was not specified.")

    if ros and ros not in official_ros_gzv:
        error("ERROR: '%s' is not a valid/supported ROS distribution." % ros)

    if gzv and ros and ros not in compatible[gzv]:
        error("ERROR: Gazebo %d is not compatible with ROS %s!" % (gzv, ros))

    tmp = official_ros_gzv[ros] if ros else None
    if ros and tmp != None and tmp != gzv and not confirm:
        error("WARNING: Unofficial Gazebo %d + ROS %s version selected!\n" %
              (gzv, ros) + "We recommend using Gazebo %d + ROS %s :)\n\n" %
              (tmp, ros) + "    * If you know what you are doing, " +
              "then add option --y to confirm selection and continue.\n" +
              "    * Otherwise, please visit"
              "http://gazebosim.org/tutorials?tut=ros_wrapper_versions"
              "for more info.")


def print_spawn_msg(args):
    gzv, ros, config, pr, confirm, nvidia, source, pull = args
    gz_msg, ros_msg, config_msg, pr_msg = ("", "", "", "")

    if ros:
        ros_msg = " + ROS %s" % ros

    if gzv:
        gz_msg = "Spawning docker container for Gazebo %d" % gzv

    if config:
        config_msg = " running world configuration %s" % config

    if pr:
        pr_msg = " from PR# %s" % pr

    print("\n~~~ " + gz_msg + ros_msg + config_msg + pr_msg + " ~~~\n")


def print_src_install_msgs(tag_name):
    print("Access the container with the following command:")
    print("     docker exec -it %s /bin/bash" % tag_name)
    print("Once in the container:")
    print("     - Pull all source code repos with: gzrepos.sh")
    print("     - Then compile and run with verbose output using: gzcolcon.sh")
    print("       or less output messages with: colcon build && gazebo")


def log_nvidia_docker(docker_client, tag_name, path, container_log, client_log):
    try:
        container = docker_client.containers.get(tag_name)
        logs = container.logs(stream=True)
        for log in logs:
            if type(log) is bytes:
                container_log += log.decode("utf8")
            else:
                container_log += log
    except KeyboardInterrupt:
        client_log += "Nvidia spawn stopped with a Keyboard Interrupt.\n"
    except (docker.errors.NotFound, docker.errors.APIError):
        client_log += "Container might have been force removed by user.\n"
        client_log += "[ERROR] Container not found. Failed to log and remove.\n"
    if container:
        container.remove(force=True)
        client_log += "Succesfully stopped and removed running container.\n"

    write_log(path + tag_name + ".log", container_log + client_log)


def write_log(log_path, log):
    print("-> Logging output and errors to \"%s\".\n" % log_path)
    with open(log_path, 'w') as log_file:
        log_file.write(log)


def spawn_container(args):
    gzv, ros, config, pr, confirm, nvidia, source, pull = args
    gzv = str(gzv)
    tag_name = "gz" + gzv
    build_args = {"GZV": gzv}
    dockerfile = "docker/"
    docker_client = docker.from_env()
    docker_build = docker_client.images.build
    docker_run = docker_client.containers.run
    runtime = None
    cmd = ""
    container_log = "~~~ Container Log ~~~\n"
    client_log = "\n~~~ Client log ~~~\n\n"
    gzdev_path = dirname(realpath(__file__ + "/..")) + "/"
    log_i = 0
    src_volume = ""
    xpra_volumes = {}

    if source:
        run([
            'curl', 'https://bitbucket.org/osrf/release-tools/raw/default/' +
            'jenkins-scripts/lib/dependencies_archive.sh', '-o',
            '/tmp/dependencies.sh'
        ], stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout
        base_deps = run('ROS_DISTRO=dummy GAZEBO_MAJOR_VERSION=' + gzv +
                        ' . /tmp/dependencies.sh && echo $BASE_DEPENDENCIES',
                        shell=True, stdout=PIPE,
                        stderr=PIPE, universal_newlines=True).stdout.replace(
                            "\\", "").rstrip()
        gz_base_deps = run(
            'ROS_DISTRO=dummy GAZEBO_MAJOR_VERSION=' + gzv +
            ' . /tmp/dependencies.sh && echo $GAZEBO_BASE_DEPENDENCIES',
            shell=True, stdout=PIPE, stderr=PIPE,
            universal_newlines=True).stdout.replace("\\", "").rstrip()

        gz_base_deps = sub("\w*(ignition|sdformat)[-\w]*", "", gz_base_deps)

        build_args.update({
            "BASE_DEPENDENCIES": base_deps,
            "GAZEBO_BASE_DEPENDENCIES": gz_base_deps
        })
        dockerfile += "gzsrc/"
        tag_name += "_src"
        src_volume = ' --volume=%sgazebo:/mnt/gazebo ' % gzdev_path
        xpra_volumes = {
            gzdev_path + 'gazebo': {'bind': '/mnt/gazebo', 'mode': 'rw'}
        }
        if pull:
            cmd = "gzrepos.sh"
        else:
            cmd = None
    else:
        cmd = "gzxpra.sh"

    if nvidia:
        try:
            runtime = "nvidia"
            if not source:
                cmd = "gazebo --verbose"
            client_log += run(["nvidia-docker", "version"], stdout=PIPE,
                              stderr=PIPE, universal_newlines=True).stdout
        except FileNotFoundError:
            runtime = None
            client_log += "[ERROR] `nvidia-docker` command was not found.\n"

    print("-> Building docker image. The first time will take a few minutes...",
          "\n   You might want to grab a cup of coffee",
          "or whatever suits your cup of tea :)\n")

    docker_build(path=gzdev_path + dockerfile, rm=True, buildargs=build_args,
                 tag=tag_name)

    # The docker container is configured to remove itself after the user closes
    # Gazebo or if an error occurs. But sometimes, the container from a previous
    # run might still exist. In such cases, calling gzdev spawn again with the
    # same parameters would trigger a name conflict and throw an error.
    # Therfore, it's best to try removing the container with the same name tag,
    # if any, so we can perform a clean docker run right after.
    try:
        docker_client.containers.get(tag_name).remove(force=True)
        client_log += "Found and removed container from previous spawn.\n"
    except docker.errors.NotFound:
        pass

    print("-> Running docker container and forwarding",
          "hardware accelerated graphics to your screen\n")

    if runtime == "nvidia":
        if cmd is None:
            cmd = []
        else:
            cmd = cmd.split()

        nvidia_docker = ('nvidia-docker' + ' run' + ' -itd' + ' --name=' + \
            tag_name + ' --env=DISPLAY' + ' --env=QT_X11_NO_MITSHM=1' + \
            ' --volume=/tmp/.X11-unix:/tmp/.X11-unix:rw ' + src_volume +  \
            tag_name).split() + cmd

        client_log += run(nvidia_docker, stdout=PIPE, stderr=PIPE,
                          universal_newlines=True).stdout

        if source:
            print_src_install_msgs(tag_name)
            exit()

        log_nvidia_docker(docker_client, tag_name, gzdev_path, container_log,
                          client_log)
    elif not runtime:
        try:
            xpra_volumes.update(
                {'/tmp/.X11-unix': {'bind': '/tmp/.X11-unix', 'mode': 'rw'}})

            container = docker_run(
                tag_name, command=cmd, stdin_open=True, tty=True, detach=True,
                environment=[
                    "DISPLAY=" + environ["DISPLAY"], "QT_X11_NO_MITSHM=1"
                ], ports={'10000': 10000}, volumes=xpra_volumes, name=tag_name,
                runtime=runtime)
        except docker.errors.APIError as error:
            client_log += "[ERROR] " + error.explanation
            client_log += "Could not spawn docker container.\n"
            container_log += "NONE"
            write_log(gzdev_path + tag_name + ".log",
                      container_log + client_log)
            exit()

        if source:
            print_src_install_msgs(tag_name)
            exit()

        # The following code ensures the xpra client does not attach to the
        # xpra host before the server is up and ready to accept connections.
        # At the same time, we store and then log the output of the xpra server.
        if not nvidia:
            try:
                for log in container.logs(stream=True):
                    if type(log) is bytes:
                        container_log += log.decode("utf8")
                    else:
                        container_log += log
                    if container_log.endswith("xpra is ready.\x1b[0m\r\n"):
                        break
            except KeyboardInterrupt:
                client_log += "Xpra server polling stopped with a Keyboard Interrupt.\n"

            # Store the current length of the container's log so then we can use it
            # as an index to continue logging the rest of the Xpra server's output.
            log_i = len(container.logs())

            # Run and attach the Xpra client to the Xpra server
            try:
                client_log += run(["xpra", "attach", "tcp:localhost:10000"],
                                  stdout=PIPE, stderr=PIPE,
                                  universal_newlines=True, check=True).stdout
            except CalledProcessError:
                client_log += "Xpra client was not able to connect to xpra server.\n"
            except KeyboardInterrupt:
                client_log += "Xpra was stopped with a Keyboard Interrupt.\n"
            except FileNotFoundError:
                client_log += "[ERROR] `xpra` command was not found.\n"

            # Log both Gazebo's and Xpra server's output after client shutdown.
            # Convert tmp byte string to printable pretty string
            if container:
                for log in container.logs()[log_i:]:
                    container_log += chr(log)
                container.remove(force=True)
                client_log += "Succesfully stopped and removed running container.\n"

            write_log(gzdev_path + tag_name + ".log",
                      container_log + client_log)
        else:
            log_nvidia_docker(docker_client, tag_name, gzdev_path,
                              container_log, client_log)


def main():
    try:
        args = normalize_args(docopt(__doc__, version="gzdev-spawn 0.1.0"))
        validate_input(args)
        print_spawn_msg(args)
        spawn_container(args)
    except KeyboardInterrupt:
        print("spawn was stopped with a Keyboard Interrupt.\n")


if __name__ == '__main__':
    main()
