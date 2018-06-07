apt-get update && apt-get -y upgrade
apt-get install -y ruby-dev ruby-ronn wget lsb-release mercurial vim python3 python3-pip build-essential software-properties-common cmake debhelper mesa-utils cppcheck xsltproc python-lxml python-psutil python bc netcat-openbsd gnupg2 net-tools locales
#. /etc/os-release
#echo "deb-src http://packages.osrfoundation.org/gazebo/$ID-stable `lsb_release -sc` main" > /etc/apt/sources.list.d/gazebo-latest.list
# wget http://packages.osrfoundation.org/gazebo.key -O - | apt-key add
apt-add-repository -y ppa:dartsim
apt-get update && apt-get install -y libtinyxml2-dev libdart6-dev libfreeimage-dev libprotoc-dev libprotobuf-dev protobuf-compiler freeglut3-dev libcurl4-openssl-dev libtinyxml-dev libtar-dev libtbb-dev libogre-1.9-dev libxml2-dev pkg-config qtbase5-dev libqwt-qt5-dev libltdl-dev libgts-dev libboost-thread-dev libboost-signals-dev libboost-system-dev libboost-filesystem-dev libboost-program-options-dev libboost-regex-dev libboost-iostreams-dev libbullet-dev libsimbody-dev

# echo "deb http://download.opensuse.org/repositories/network:/messaging:/zeromq:/release-stable/Debian_9.0/ ./" >> /etc/apt/sources.list
# wget https://download.opensuse.org/repositories/network:/messaging:/zeromq:/release-stable/Debian_9.0/Release.key -O - | apt-key add
apt-get install libzmq3-dev uuid-dev

pip3 install --upgrade pip wheel setuptools colcon-common-extensions vcstool
mkdir -p /tmp/gazebo/src && cd /tmp/gazebo
wget https://gist.githubusercontent.com/dirk-thomas/6c1ca2a7f5f8c70ce7d3e1ef10a9f678/raw/490aaba72321284af956c9db12f9ef1550ef88cf/Gazebo9.repos
vcs import src < Gazebo9.repos
colcon metadata add default https://raw.githubusercontent.com/colcon/colcon-metadata-repository/master/index.yaml
colcon metadata update
export PATH="/tmp/gazebo/install/SDFormat:/tmp/gazebo/build/:$PATH"
#colcon build
