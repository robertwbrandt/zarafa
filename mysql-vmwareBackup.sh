#!/bin/bash
#
#     Script for backing up the MySQL Database with VMware Snapshots
#     Bob Brandt <projects@brandt.ie>
#
#     http://blog.erben.sk/2014/06/26/snapshoting-virtual-machine-running-mysql-database/
#     https://www.virtuallifestyle.nl/2013/03/back-up-mysql-on-linux-without-stopping-services-or-dumping-the-database/
#

_backupLocation="/srv/backup/sql-backup/zarafa-mysql-backup.sql"
_backupLog="/srv/backup/backup.log"
_mysqlCredentials="/etc/mysql/debian.cnf"
_mysqlTimeout=120
_vmwareTimeout=60
_mysqlLockFile="/tmp/mysql_tables_read_lock"
_version=1.1
_brandt_utils=/opt/brandt/common/brandt.sh

[ ! -r "$_brandt_utils" ] && echo "Unable to find required file: $_brandt_utils" 1>&2 && exit 6
. "$_brandt_utils"

function freeze() {
	sleep_time=$(( _mysqlTimeout + 10 ))

	rm -f $_mysqlLockFile
        logger -st "vmwareSnapshot-freeze" "Executing MySQL FLUSH TABLES WITH READ LOCK"
	mysql --defaults-file=$_mysqlCredentials -e "FLUSH TABLES WITH READ LOCK; system touch $_mysqlLockFile; system sleep $sleep_time; system logger -st 'vmwareSnapshot-freeze' 'lock released'; " &
	_mysqlPID=$!
	logger -st "vmwareSnapshot-freeze" "$0 child pid $_mysqlPID"

	c=0
	while [ ! -f $_mysqlLockFile ]
	do
        	# check if mysql is running
	        if ! ps -p $_mysqlPID 1>/dev/null ; then
        	        logger -st "vmwareSnapshot-freeze" "$0 mysql command has failed (bad credentials?)"
                	return 1
	        fi
        	sleep 1
	        c=$((c+1))
        	if [ $c -gt $_mysqlTimeout ]; then
	                logger -st "vmwareSnapshot-freeze" "$0 timed out waiting for lock"
        	        touch $_mysqlLockFile
                	kill -9 $_mysqlPID
	        fi
	done
	echo $_mysqlPID > $_mysqlLockFile
	return 0
}

function thaw() {
	if [ -f "$_mysqlLockFile" ]; then
	        local _mysqlPID=$(cat $_mysqlLockFile)
	        logger -st "vmwareSnapshot-thaw" "Releasing MySQL Table Read Lock (sending sigterm to $_mysqlPID)"
	        pkill -9 -P $_mysqlPID
	        rm -f $_mysqlLockFile
	fi
        exit 0
}

function setup() {
	local _fullpath=$( readlink -f $0 )
	ln -sf "$_fullpath" "/usr/sbin/pre-freeze-script"
	ln -sf "$_fullpath" "/usr/sbin/post-thaw-script"
}

function usage() {
        local _exitcode=${1-0}
        local _output=2
        [ "$_exitcode" == "0" ] && _output=1
        [ "$2" == "" ] || echo -e "$2"
        ( echo -e "Usage: $0 [options] command"
          echo -e "Commands:  freeze    thaw    setup"
          echo -e "Options:"
          echo -e " -h, --help     display this help and exit"
          echo -e " -v, --version  output version information and exit" ) >&$_output
        exit $_exitcode
}

# Execute getopt
if ! _args=$( getopt -o vh -l "help,version" -n "$0" -- "$@" 2>/dev/null ); then
        _err=$( getopt -o vh -l "help,version" -n "$0" -- "$@" 2>&1 >/dev/null )
        usage 1 "${BOLD_RED}$_err${NORMAL}"
fi

#Bad arguments
#[ $? -ne 0 ] && usage 1 "$0: No arguments supplied!\n"

eval set -- "$_args";
while /bin/true ; do
    case "$1" in
        -h | --help )      usage 0 ;;
        -v | --version )   brandt_version $_version ;;
        -- )               shift ; break ;;
        * )                usage 1 "${BOLD_RED}$0: Invalid argument!${NORMAL}" ;;
    esac
    shift
done
_command=$( lower "$1" )
shift 1

_basename=$( basename "$0" )
_program=$( readlink -f "$0" )

if [ "$_basename" == "pre-freeze-script" ]; then
	$_program freeze
	exit 0
elif [ "$_basename" == "post-thaw-script" ]; then
	$_program thaw
	exit 0
fi

case "$_command" in
    "freeze" )	freeze || _vmwareTimeout=1
		( sleep ${_vmwareTimeout}s && $_program thaw ) & ;;
    "thaw" )    thaw ;;
    "setup" )   setup ;;
    * )         usage 1 ;;
esac
exit 0
