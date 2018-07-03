FROM phusion/baseimage:0.10.1

ARG GZV

CMD ["/sbin/my_init"]

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	libgl1-mesa-glx \
	libgl1-mesa-dri \
	xvfb; \
	apt-get install -y xpra; \
	bash -c 'source /etc/os-release && \
	echo "deb http://packages.osrfoundation.org/gazebo/$ID-stable \
	`lsb_release -sc` main" > /etc/apt/sources.list.d/gazebo-latest.list' && \
	curl http://packages.osrfoundation.org/gazebo.key -o - | apt-key add && \
	apt-get update && \
	apt-get install -y gazebo$GZV; \
	apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 10000

CMD ["xpra", "start", ":100", "--start-child=gazebo --verbose", \
	"--daemon=off", "--opengl=yes", "--bind-tcp=0.0.0.0:10000", "--no-mdns", \
	"--no-notifications", "--no-pulseaudio", "--exit-with-children", \
	"--exit-with-client=yes"]
