#!/bin/bash
#
#     Script to restart Apache for Activesync
#     Bob Brandt <projects@brandt.ie>
# 
#if nc -v -z activesync.opw.ie 443


#if nc -v -z activesync.opw.ie 443
if wget --timeout=10 --no-proxy --no-check-certificate -O /dev/null --http-user=castrof --http-password=cubacuba https://activesync.opw.ie/Microsoft-Server-ActiveSync
then
	logger -st 'activesync' 'Connection to activesync.opw.ie 443 port [tcp/https] succeeded!'
else
	logger -st 'activesync' 'Connection to activesync.opw.ie 443 port [tcp/https] failed: Connection refused. Unable to establish SSL connection.'
	/etc/init.d/apache2 restart
fi
exit $?


       