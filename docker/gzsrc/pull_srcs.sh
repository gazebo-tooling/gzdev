#!/bin/bash
mkdir src &&
curl https://bitbucket.org/rosatamsen/gazebodistro/raw/default/gazebo${GZV}.yml -o Gazebo${GZV}.repos &&
vcs import src < Gazebo${GZV}.repos &&
colcon metadata add default https://raw.githubusercontent.com/colcon/colcon-metadata-repository/master/index.yaml &&
colcon metadata update
