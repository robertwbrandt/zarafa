#!/bin/bash
#
#     Script to restart Apache for Activesync
#     Bob Brandt <projects@brandt.ie>
# 
#if nc -v -z activesync.opw.ie 443

user="castrof"
pass="cubacuba"
url="https://127.0.0.1/Microsoft-Server-ActiveSync"

#if nc -v -z activesync.opw.ie 443
if wget --timeout=10 --no-proxy --no-check-certificate -O /dev/null --http-user=$user --http-password=$pass $url
then
	logger -st 'activesync' 'Connection to activesync.opw.ie 443 port [tcp/https] succeeded!'
else
	logger -st 'activesync' 'Connection to activesync.opw.ie 443 port [tcp/https] failed: Connection refused. Unable to establish SSL connection.'
	/etc/init.d/apache2 restart
fi
exit $?


       