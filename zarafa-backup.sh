#!/bin/bash
#
#     Script for postfix smarthost maps and resyncing Zarafa
#     Bob Brandt <projects@brandt.ie>
#     Zentyal <info@zentyal.com>
#

_backupLocation="/srv/backup/brick-level-backup"
_backupLog="$_backupLocation/backup.log"
_backupThreads=4

echo "Backup Zarafa Mailboxes"
_start=$( date )
/usr/sbin/zarafa-backup -t $_backupThreads -a -o "$_backupLocation" 2>&1 | tee "$_backupLog"
if grep "fatal" "$_backupLog" >/dev/null 2>&1
then
        echo "Zarafa Backup (which started at $_start) has failed at $( date )" | tee -a "$_backupLog"
	exit 1
else
	echo "Zarafa Backup (which started at $_start) has successfully completed at $( date )" | tee -a "$_backupLog"
	exit 0
fi


