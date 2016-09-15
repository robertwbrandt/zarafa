#!/bin/bash
#
#     Script to restart Apache for Activesync
#     Bob Brandt <projects@brandt.ie>
# 
if nc -v -z activesync.opw.ie 443
then
	logger -st 'activesync' 'Connection to activesync.opw.ie 443 port [tcp/https] succeeded!'
else
	logger -st 'activesync' 'connect to activesync.opw.ie port 443 (tcp) failed: Connection refused. Restarting Apache2.'
	/etc/init.d/apache2 restart
fi
exit $?
