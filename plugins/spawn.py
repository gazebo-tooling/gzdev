"""
Usage:
	gzdev spawn [<gzv> | --gzv=<number>]
	            [<ros> | --ros=<distro_name>]
	            [<config> | --config=<file_name>]
	            [<pr> | --pr=<number>]
	            [--dev | --source]
	            [--yes]
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

"""
import docker
from docopt import docopt
from os import environ
from subprocess import run, PIPE, CompletedProcess
from sys import stderr

official_ros_gzv = {"kinetic": 7, "lunar": 7, "melodic": 9}
gz7_ros = {}.fromkeys(["kinetic", "lunar"])
gz8_ros = {}.fromkeys(["kinetic", "lunar"])
gz9_ros = {}.fromkeys(["kinetic", "lunar", "melodic"])
compatible = {7: gz7_ros, 8: gz8_ros, 9: gz9_ros}
max_gzv = 9


def normalize_args(args):
	gzv = args["<gzv>"] if args["<gzv>"] else args["--gzv"]
	ros = args["<ros>"] if args["<ros>"] else args["--ros"]
	config = args["<config>"] if args["<config>"] else args["--config"]
	pr = args["<pr>"] if args["<pr>"] else args["--pr"]
	confirm = args["--yes"]

	ros = ros.lower() if ros else None
	gzv = int(gzv) if gzv and gzv.isdecimal() else gzv
	if gzv == None and ros and ros in official_ros_gzv:
		gzv = official_ros_gzv[ros]

	return gzv, ros, config, pr, confirm


def error(msg):
	print("\n" + msg + "\n", file=stderr)
	exit(0)


def validate_input(args):
	gzv, ros, config, pr, confirm = args

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
	gzv, ros, config, pr, confirm = args
	gz_msg, ros_msg, config_msg, pr_msg = ("", "", "", "")

	if ros:
		ros_msg = " + ROS %s" % ros

	if gzv:
		gz_msg = "Spawning docker container for Gazebo %d" % gzv

	if config:
		config_msg = " running world configuration %s" % config

	if pr:
		pr_msg = " from PR# %s" % pr

	print("\n" + gz_msg + ros_msg + config_msg + pr_msg + "...\n")


def docker_run(args):
	gzv, ros, config, pr, confirm = args
	gzv = str(gzv)
	tag_name = "gz" + gzv
	docker_client = docker.from_env()
	docker_build = docker_client.images.build
	docker_run = docker_client.containers.run
	runtime = "nvidia"

	try:
		run(["nvidia-docker", "version"])
	except FileNotFoundError:
		runtime = ""

	docker_build(path="docker", rm=True, buildargs={"GZV": gzv}, tag=tag_name)

	try:
		docker_client.containers.get(tag_name).stop()
	except docker.errors.NotFound:
		pass

	docker_run(
		tag_name,
		stdin_open=True,
		tty=True,
		detach=True,
		environment=["DISPLAY=" + environ["DISPLAY"], "QT_X11_NO_MITSHM=1"],
		ports={'10000': 10000},
		volumes={'/tmp/.X11-unix':{'bind':'/tmp/.X11-unix', 'mode':'rw'}},
		name=tag_name,
		remove=True,
		runtime=runtime)

	try:
		ret = run(["xpra", "attach", "tcp:localhost:10000"],
						stdout=PIPE, stderr=PIPE, universal_newlines=True)
	except KeyboardInterrupt:
		exit()

	with open(tag_name + ".log", 'w') as log_file:
		log_file.write(ret.stdout)


def main():
	args = normalize_args(docopt(__doc__, version="gzdev-spawn 0.1.0"))
	validate_input(args)
	print_spawn_msg(args)
	docker_run(args)


if __name__ == '__main__':
	main()
