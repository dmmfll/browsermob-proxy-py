#!/usr/bin/env bash
TOOLS=$(pwd)/tools
VERSION='3.141.59'
cd $TOOLS/browsermob-proxy-2.1.4/bin/ && \
./browsermob-proxy --port 9090 & \
cd $TOOLS && \
java -Dwebdriver.chrome.driver=chromedriver -Dwebdriver.gecko.driver=geckodriver -jar selenium-server-standalone-$VERSION.jar &
