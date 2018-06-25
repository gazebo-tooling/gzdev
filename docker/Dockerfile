FROM phusion/baseimage:0.10.1

ARG GZV

CMD ["/sbin/my_init"]

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	libgl1-mesa-glx \
	libgl1-mesa-dri \
	mesa-utils \
	x11-apps

# git-core pkg-config automake libtool libpthread-stubs0-dev xserver-xorg-dev x11proto-xinerama-dev libx11-xcb-dev libxcb-glx0-dev libxrender-dev libgl1-mesa-dri libxcb-glx0-dev
# dri deps
# 	xutils-dev
# mesa deps -> apt-get build-dep mesa
# 	python python-pip libxrandr-dev
# pip install mako

# report "swras" typo
#./autogen.sh --prefix=/usr --libdir=${LIBDIR} --with-gallium-drivers=svga --with-dri-drivers=swrast

RUN	bash -c 'source /etc/os-release && \
	echo "deb http://packages.osrfoundation.org/gazebo/$ID-stable \
	`lsb_release -sc` main" > /etc/apt/sources.list.d/gazebo-latest.list' && \
	curl http://packages.osrfoundation.org/gazebo.key -o - | apt-key add && \
	apt-get update && \
	apt-get install -y gazebo$GZV; \
	apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
