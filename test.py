from pytest import raises
from plugins import spawn

argv = {
	"<gzv>": None,
	"<ros>": None,
	"<config>": None,
	"<pr>": None,
	"--gzv": None,
	"--ros": None,
	"--config": None,
	"--pr": None,
	"--yes": None
}

run_code = {}
error_code = {}

def execute(argv):
	args = spawn.normalize_args(argv)
	spawn.validate_input(args)
	spawn.run(args)
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

	with raises(SystemExit):
		execute(argv)
		for v in bad_gzv:
			argv["--gzv"] = v
			execute(argv)


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
	with raises(SystemExit):
		for i in range(len(gzv)):
			argv["--gzv"] = gzv[i]
			argv["--ros"] = "melodic"
			execute(argv)

	ros = ("Indigo", "jade", "turtle", "!@#$")
	with raises(SystemExit):
		for i in range(len(ros)):
			argv["--ros"] = ros[i]
			execute(argv)


def test_gz_ros_unofficial():
	gzv = ("8", "8", "9", "9")
	ros = ("kinetic", "lunar", "kinetic", "lunar")

	with raises(SystemExit):
		for i in range(len(gzv)):
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


run_all()
