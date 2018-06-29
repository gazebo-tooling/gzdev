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
from docopt import docopt
from sys import stderr
from dockerfile_parse import DockerfileParser
from pprint import pprint
import json
import docker

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


def run(args):
	gzv, ros, config, pr, confirm = args
	gz_msg, ros_msg, config_msg, pr_msg = ("", "", "", "")
	docker_build = docker.from_env().images.build
	docker_run = docker.from_env().containers.run

	if ros:
		ros_msg = " + ROS %s" % ros

	if gzv:
		gz_msg = "Spawning docker container for Gazebo %d" % gzv
		# docker_build(path="docker", rm=True, buildargs={"GZV":str(gzv)}, tag="gz"+str(gzv))
		# docker_run("gz"+gzv, "xeyes", environment=["DISPLAY=192.168.99.1:0"], name="gz"+gzv remove=True)
	else:
		error("ERROR: Gazebo version was not specified.")

	if config:
		config_msg = " running world configuration %s" % config

	if pr:
		pr_msg = " from PR# %s" % pr

	print("\n" + gz_msg + ros_msg + config_msg + pr_msg + ".\n")

def docker_test():
	dfp = DockerfileParser()
	dfp.content = """\
	From  base
	LABEL foo="bar baz"
	USER  me
	RUN ls
	RUN apt-get update"""

	# Print the parsed structure:
	# pprint(dfp.structure)
	pprint(dfp.json)
	# pprint(dfp.labels)

	# Set a new base:
	dfp.baseimage = 'centos:7'
	parsed_json = json.loads(dfp.json)
	parsed_json[3]["RUN"] = "echo hello"
	print(parsed_json)
	# dfp.json = json.dumps(parsed_json)
	dfp._modify_instruction("FROM", "xenial:latest")
	dfp._modify_instruction("RUN", "")
	# Print the new Dockerfile with an updated FROM line:
	print(dfp.content)


def main():
	args = normalize_args(docopt(__doc__, version="gzdev-spawn 0.1.0"))
	validate_input(args)
	run(args)


if __name__ == '__main__':
	main()
