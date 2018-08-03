# Copyright 2018 David Rosa
# Licensed under the Apache License, Version 2.0

from pytest import raises
from plugins import spawn

argv = {
    "<gzv>": None, "<ros>": None, "<config>": None, "<pr>": None, "--gzv": None,
    "--ros": None, "--config": None, "--pr": None, "--yes": None,
    "--nvidia": None, "--source": None
}

run_code = {}
error_code = {}


def execute(argv):
    args = spawn.normalize_args(argv)
    spawn.validate_input(args)
    spawn.print_spawn_msg(args)
    reset_argv()


def reset_argv():
    for k in argv:
        argv[k] = None


# def check_run_code(capsys):
# 	spawn.run((9, "melodic", None, None, None))
# 	captured = capsys.readouterr()
# 	assert captured.out == "\nSpawning docker container for Gazebo 9 + ROS melodic.\n\n"


def test_gzv():
    gzv = ("7", "8", "9")
    bad_gzv = ("0", "6", "10", "a")

    for v in gzv:
        argv["--gzv"] = v
        execute(argv)

    for v in bad_gzv:
        with raises(SystemExit):
            execute(argv)
            argv["--gzv"] = v


def test_gz_ros():
    gzv = ("7", "07", "009")
    ros = ("Kinetic", "LUNAR", "melodic")

    for i in range(len(gzv)):
        argv["--gzv"] = gzv[i]
        argv["--ros"] = ros[i]
        execute(argv)

    for i in range(len(ros)):
        argv["--ros"] = ros[i]
        execute(argv)

    gzv = ("7", "8")
    for i in range(len(gzv)):
        with raises(SystemExit) as excinfo:
            argv["--gzv"] = gzv[i]
            argv["--ros"] = "melodic"
            execute(argv)
        assert excinfo.value.code == 0

    ros = ("Indigo", "jade", "turtle", "!@#$")
    for i in range(len(ros)):
        with raises(SystemExit):
            argv["--ros"] = ros[i]
            execute(argv)


def test_gz_ros_unofficial():
    gzv = ("8", "8", "9", "9")
    ros = ("kinetic", "lunar", "kinetic", "lunar")

    for i in range(len(gzv)):
        with raises(SystemExit):
            argv["--gzv"] = gzv[i]
            argv["--ros"] = ros[i]
            execute(argv)

    for i in range(len(gzv)):
        argv["--yes"] = True
        argv["--gzv"] = gzv[i]
        argv["--ros"] = ros[i]
        execute(argv)


def run_all():
    test_gzv()
    test_gz_ros()
    test_gz_ros_unofficial()


if __name__ == '__main__':
    run_all()
