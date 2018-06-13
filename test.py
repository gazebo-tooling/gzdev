from pytest import raises
from plugins import spawn

def test_input():
	spawn.validate_input((9, "melodic", None, None, None))
	with raises(SystemExit):
		spawn.validate_input((0, "melodic", None, None, None))

def test_output(capsys):
	spawn.run((9, "melodic", None, None, None))
	captured = capsys.readouterr()
	assert captured.out == "\nSpawning docker container for Gazebo 9 + ROS melodic.\n\n"
