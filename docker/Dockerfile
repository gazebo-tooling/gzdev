FROM phusion/baseimage:0.10.1

ARG GZV

CMD ["/sbin/my_init"]

RUN apt-get update; \
	apt-get install -y --no-install-recommends \
	lsb-release; \
	bash -c 'source /etc/os-release && echo "deb http://packages.osrfoundation.org/gazebo/$ID-stable `lsb_release -sc` main" > /etc/apt/sources.list.d/gazebo-latest.list'; \
	curl http://packages.osrfoundation.org/gazebo.key -o - | apt-key add; \
	apt-get update; \
	apt-get install -y gazebo$GZV

RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
