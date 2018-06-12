"""
Usage:
	gzdev spawn [<gzv> | --gzv=<number>]
	            [<ros> | --ros=<distro_name>]
	            [<config> | --config=<file_name>]
	            [<pr> | --pr=<number>]
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
	--yes                   Confirm selection of unofficial ROS + Gazebo version

"""
from docopt import docopt

ros_gzv = {"melodic": 9, "lunar": 7, "kinetic": 7, "indigo": 2}
gz2 = {}.fromkeys(["indigo"])
gz7 = {}.fromkeys(["indigo", "kinetic", "lunar"])
gz8 = {}.fromkeys(["kinetic", "lunar"])
gz9 = {}.fromkeys(["kinetic", "lunar", "melodic"])

compatible = [None, None, gz2, None, None, None, None, gz7, gz8, gz9]


def parse_args():
	args = docopt(__doc__, version="gzdev-spawn 0.1")

	gzv = args["<gzv>"] if args["<gzv>"] else args["--gzv"]
	ros = args["<ros>"] if args["<ros>"] else args["--ros"]
	config = args["<config>"] if args["<config>"] else args["--config"]
	pr = args["<pr>"] if args["<pr>"] else args["--pr"]
	confirm = args["--yes"]

	ros = ros.lower() if ros else None
	gzv = int(gzv) if gzv and gzv.isdecimal() else gzv

	return gzv, ros, config, pr, confirm


def error(msg):
	# raise SystemExit("\n" + msg + "\n")
	exit("\n" + msg + "\n")


def validate_input():
	gzv, ros, config, pr, confirm = argv

	if type(gzv) is int and (gzv <= 0 or
		gzv >= len(compatible)) or type(gzv) is str:
		error("ERROR: '%s' is not a valid Gazebo version number." % gzv)

	if not gzv and ros and ros not in ros_gzv:
		error("ERROR: '%s' is not a valid/supported ROS distribution." % ros)

	if gzv and not compatible[gzv]:
		error("ERROR: This tool does not support Gazebo %d." % gzv)

	if gzv and ros and ros not in compatible[gzv]:
		error("ERROR: Gazebo %d is not compatible with ROS %s!" % (gzv, ros))


def run():
	gzv, ros, config, pr, confirm = argv
	gz_msg, ros_msg, config_msg, pr_msg = ("", "", "", "")

	if ros:
		ros_msg = " + ROS %s" % ros

		if gzv == None or (gzv and not confirm):
			tmp = gzv
			gzv = ros_gzv[ros]

			if tmp != None and tmp != gzv:
				print(
					"WARNING: Unofficial Gazebo %d%s version selected!\n" %
					(tmp, ros_msg),
					"We recommend using Gazebo %d%s :)\n\n" % (gzv, ros_msg),
					"    * If you know what you are doing, ",
					"then add option --y to confirm selection and continue.\n",
					"    * Otherwise, please visit"
					"http://gazebosim.org/tutorials?tut=ros_wrapper_versions"
					"for more info.\n",
					sep="")
				exit()

	if gzv:
		gz_msg = "\nSpawning docker container for Gazebo %d" % gzv
	else:
		exit("\nERROR: Gazebo version was not specified.\n")

	if config:
		config_msg = " running world configuration %s" % config

	if pr:
		pr_msg = " from PR# %s" % pr

	print(gz_msg + ros_msg + config_msg + pr_msg + ".\n")


argv = parse_args()
if __name__ == '__main__':
	validate_input()
	run()
