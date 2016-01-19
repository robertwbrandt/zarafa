#!/bin/bash
#
#     Script for backing up Zarafa mailboxes
#     Bob Brandt <projects@brandt.ie>
#

_backupLocation="/srv/backup/brick-level-backup"
_backupLog="$_backupLocation/backup.log"
_backupThreads=4

/usr/sbin/zarafa-backup -t $_backupThreads -a -v -o "$_backupLocation" 2>&1 | tee "$_backupLog"
! grep "fatal" "$_backupLog" >/dev/null 2>&1
tmp=$?



exit $tmp
