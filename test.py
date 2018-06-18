from pytest import raises
from plugins import spawn


def test_input():
	spawn.validate_input((7, None, None, None, None))
	spawn.validate_input((8, None, None, None, None))
	spawn.validate_input((9, None, None, None, None))
	spawn.validate_input((7, "kinetic", None, None, None))
	spawn.validate_input((7, "lunar", None, None, None))
	spawn.validate_input((9, "melodic", None, None, None))
	with raises(SystemExit):
		spawn.validate_input((0, "melodic", None, None, None))


def test_output(capsys):
	spawn.run((9, "melodic", None, None, None))
	captured = capsys.readouterr()
	assert captured.out == "\nSpawning docker container for Gazebo 9 + ROS melodic.\n\n"


def execute(argv):
	args = spawn.parse_args(argv)
	spawn.validate_input(args)
	spawn.run(args)


def test_all():
	argv = {
		"<gzv>": None,
		"<ros>": None,
		"<config>": None,
		"<pr>": None,
		"--gzv": None,
		"--ros": None,
		"--config": None,
		"--pr": None,
		"--yes": False
	}
	with raises(SystemExit):
		execute(argv)
		argv["<gzv>"] = "0"
		execute(argv)
	argv["<gzv>"] = "9"
	execute(argv)
	argv["<gzv>"] = "8"
	execute(argv)

test_all()
