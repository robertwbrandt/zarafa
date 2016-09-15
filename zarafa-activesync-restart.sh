#!/bin/bash
#
#     Script to restart Apache for Activesync
#     Bob Brandt <projects@brandt.ie>
# 
if ! nc -v -z activesync.opw.ie 443
then
	logger -st 'activesync' 'Activesync(apache2) is not responding on port 443. Restarting Apache2.'
	echo /etc/init.d/apache2 restart
fi
exit $?
