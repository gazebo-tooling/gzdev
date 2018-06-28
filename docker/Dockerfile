FROM phusion/baseimage:0.10.1

ARG GZV

CMD ["/sbin/my_init"]

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	libgl1-mesa-glx \
	libgl1-mesa-dri \
	mesa-utils \
	x11-apps; \
	apt-get install -y xpra

RUN	bash -c 'source /etc/os-release && \
	echo "deb http://packages.osrfoundation.org/gazebo/$ID-stable \
	`lsb_release -sc` main" > /etc/apt/sources.list.d/gazebo-latest.list' && \
	curl http://packages.osrfoundation.org/gazebo.key -o - | apt-key add && \
	apt-get update && \
	apt-get install -y gazebo$GZV; \
	apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 10000

CMD ["xpra", "start", ":100", "--start-child=glxgears",  "--daemon=off", "--bind-tcp=0.0.0.0:10000",  \
	"--no-mdns", "--no-notifications", "--no-pulseaudio"]
