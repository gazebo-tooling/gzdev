#!/bin/bash
colcon build --event-handler console_direct+ &&
gazebo --verbose
