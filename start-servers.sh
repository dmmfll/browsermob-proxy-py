#!/usr/bin/env bash
TOOLS=$(pwd)/tools
VERSION='3.141.59'
JAR=selenium-server-standalone-$VERSION.jar
NETLOC='172.17.0.1'
cd $TOOLS/browsermob-proxy-2.1.4/bin/ && \
./browsermob-proxy --port 9090 & \
cd $TOOLS && \
java -jar $JAR -role hub &
cd $TOOLS && \
java -Dwebdriver.chrome.driver=$(which chromedriver) -Dwebdriver.gecko.driver=$(which geckodriver) -jar $JAR -role node -hub http://$NETLOC:4444/grid/register/ &
# See https://stackoverflow.com/a/52829112/1913726
# java -Dwebdriver.chrome.driver=/path/to/chromedriver.exe -jar /Users/admin/selenium-server-standalone-3.14.0.jar -role node -hub http://<IP_GRID_HUB>:4444/grid/register
