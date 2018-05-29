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
	-h --help               Show this screen.
	--version               Show gzdev's version.
	--gzv=<number>          Gazebo version number.
	--ros=<distro_name>     ROS distribution name.
	--config=<file_name>    Gazebo world configuration file.
	--pr=<number>           Gazebo branch to compile from based on Pull Request #.
	--yes                   Confirm selection of unofficial ROS + Gazebo version.

"""
from docopt import docopt

args = docopt(__doc__, version="gzdev-spawn 0.1")

gzv = args["<gzv>"] if args["<gzv>"] else args["--gzv"]
ros = args["<ros>"] if args["<ros>"] else args["--ros"]
config = args["<config>"] if args["<config>"] else args["--config"]
pr = args["<pr>"] if args["<pr>"] else args["--pr"]
confirm = args["--yes"]

gz_msg, ros_msg, config_msg, pr_msg = ("", "", "", "")

if (ros):
	ros_msg = " + ROS %s" % ros
	if gzv == None or (gzv and not confirm):
		tmp = gzv

		if ros == "melodic": gzv = "9"
		if ros == "lunar": gzv = "7"
		if ros == "kinetic": gzv = "7"
		if ros == "jade": gzv = "5"
		if ros == "indigo": gzv = "2"

		if tmp != None and tmp != gzv:
			print("WARNING: Unofficial Gazebo %s%s version selected!\n" % (tmp, ros_msg),
				"We recommend using Gazebo %s%s :)\n\n" % (gzv, ros_msg),
			"    * If you know what you are doing add option --y to confirm selection and continue.\n",
			"    * Otherwise, please visit http://gazebosim.org/tutorials?tut=ros_wrapper_versions for more info.\n", sep="")
			exit()

if (gzv):
	gz_msg = "\nSpawning docker container for Gazebo %s" % gzv

if (config):
	config_msg = " running world configuration %s" % config

if (pr):
	pr_msg = " from PR #%s" % pr

if not gzv:
	print(__doc__)
else:
	print(gz_msg + ros_msg + config_msg + pr_msg + ".\n")
