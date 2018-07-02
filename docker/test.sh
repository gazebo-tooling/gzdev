#docker volume create gazebo_colcon
docker run --rm -it -v gazebo_colcon:/tmp/gazebo gazebo9_xenial

#command for both X11(display) and Xpra(TCP port)
#	docker run --rm -it -e DISPLAY=192.168.99.1:0 -p 10000:10000 gz9 bash
#xpra command inside host container:
#	xpra start :100 --start-child=glxgears --daemon=off --bind-tcp=0.0.0.0:10000 --opengl=yes --no-mdns --no-notifications --no-pulseaudio
#xpra command on client OS:
#	xpra attach tcp:localhost:10000

#Enable indirect glx rendering (software rendering) on mac X11 apps
#	defaults write org.macosforge.xquartz.X11 enable_iglx -bool true
#	defaults read org.macosforge.xquartz.X11
