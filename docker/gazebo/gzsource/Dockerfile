FROM phusion/baseimage:0.10.1

ARG GZV

CMD ["/sbin/my_init"]

RUN apt-get update && apt-get install -y --no-install-recommends libgl1-mesa-glx
RUN apt-get update && apt-get install -y --no-install-recommends libgl1-mesa-dri
RUN apt-get update && apt-get install -y --no-install-recommends xvfb
RUN apt-get update && apt-get install -y --no-install-recommends x11-apps
RUN apt-get update && apt-get install -y --no-install-recommends mesa-utils
RUN bash -c 'echo "deb https://xpra.org \
	`lsb_release -sc` main" > /etc/apt/sources.list.d/xpra.list'
RUN bash -c 'source /etc/os-release && \
	echo "deb http://packages.osrfoundation.org/gazebo/$ID-stable \
	`lsb_release -sc` main" > /etc/apt/sources.list.d/gazebo-latest.list'
RUN curl https://xpra.org/gpg.asc | apt-key add -
RUN curl http://packages.osrfoundation.org/gazebo.key | apt-key add -
RUN apt-get update && apt-get install -y xpra=2.3.*
RUN apt-get update && apt-get install -y build-essential cmake debhelper mesa-utils cppcheck xsltproc python-lxml python-psutil python bc netcat-openbsd gnupg2 net-tools locales
RUN apt-get update && apt-get install -y libfreeimage-dev libprotoc-dev libprotobuf-dev protobuf-compiler freeglut3-dev libcurl4-openssl-dev libtinyxml-dev libtar-dev libtbb-dev libogre-1.9-dev libxml2-dev pkg-config qtbase5-dev libqwt-qt5-dev libltdl-dev libgts-dev libboost-thread-dev libboost-signals-dev libboost-system-dev libboost-filesystem-dev libboost-program-options-dev libboost-regex-dev libboost-iostreams-dev libbullet-dev libsimbody-dev libignition-common-dev libignition-fuel-tools-dev libignition-transport4-dev libignition-math4-dev libignition-msgs-dev libtinyxml2-dev libsdformat6-dev
RUN apt-get update && apt-get install -y --no-install-recommends mercurial
RUN apt-get update && apt-get install -y python3-dev python3-pip
RUN echo "deb [arch=amd64,arm64] http://repo.ros2.org/ubuntu/main `lsb_release -cs` main" > /etc/apt/sources.list.d/ros2-latest.list
RUN curl http://repo.ros2.org/repos.key | apt-key add -
RUN apt-get update && apt-get install -y python3-colcon-common-extensions
RUN pip3 install --upgrade setuptools vcstool
RUN mkdir -p /tmp/gazebo/src && cd /tmp/gazebo && \
	curl https://gist.githubusercontent.com/dirk-thomas/6c1ca2a7f5f8c70ce7d3e1ef10a9f678/raw/490aaba72321284af956c9db12f9ef1550ef88cf/Gazebo9.repos -o Gazebo9.repos && \
	vcs import src < Gazebo9.repos && colcon metadata add default https://raw.githubusercontent.com/colcon/colcon-metadata-repository/master/index.yaml && colcon metadata update
RUN cd /tmp/gazebo && colcon build
RUN ["bash", "-c", "echo -e '#!/bin/bash\nxvfb-run -s \"-screen 0 1280x1024x24\" gazebo --verbose' > /usr/bin/xvfb-gazebo && chmod +x /usr/bin/xvfb-gazebo"]

EXPOSE 10000

# nvidia-docker1 hooks
LABEL com.nvidia.volumes.needed="nvidia_driver"
ENV PATH /usr/local/nvidia/bin:${PATH}
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64:${LD_LIBRARY_PATH}

# nvidia-docker2-container-runtime
ENV NVIDIA_VISIBLE_DEVICES \
	${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES \
	${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics

CMD ["xpra", "start", ":100", "--start-child=gazebo --verbose", "--daemon=off",\
	"--opengl=yes", "--bind-tcp=0.0.0.0:10000", "--mdns=no", "--av-sync=no",\
	"--notifications=no", "--exit-with-children=yes", "--pulseaudio=no", \
	"--exit-with-client=yes", "--printing=no", "--speaker=disabled"]
