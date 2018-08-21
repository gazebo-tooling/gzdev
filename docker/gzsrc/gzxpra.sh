#!/bin/bash
xpra start :100 --start-child="gazebo --verbose" --daemon=off \
				--opengl=yes --bind-tcp=0.0.0.0:10000 --mdns=no --av-sync=no \
				--notifications=no --exit-with-children=yes --pulseaudio=no \
				--exit-with-client=yes --printing=no --speaker=disabled
