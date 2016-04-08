#!/bin/bash
#
#     Script to backup Zarafa files to the backup server.
#     Bob Brandt <projects@brandt.ie>
#  

_version=0.4
_brandt_utils=/opt/brandt/common/brandt.sh
_this_conf=/etc/brandt/zarafa-backup-files.conf
_this_script=/opt/brandt/zarafa/zarafa-backup-files.sh
_this_rc=/usr/local/bin/zarafa-backup-files
_this_cron=/etc/cron.hourly/zarafa-backup-files

[ ! -r "$_brandt_utils" ] && echo "Unable to find required file: $_brandt_utils" 1>&2 && exit 6
if [ ! -r "$_this_conf" ]; then
    ( echo -e "#     Configuration file for script to backup Zarafa files to the backup server."
      echo -e "#     Bob Brandt <projects@brandt.ie>\n#"
      echo -e "_backup_veto_hours=$( seq -s ',' 8 17 )"
      echo -e "_backup_user='root'"
      echo -e "_backup_source='/srv/zarafa'"
      echo -e "_backup_dest='zarafa-backup:/srv/zarafa/'" ) > "$_this_conf"
    echo "Unable to find required file: $_this_conf" 1>&2
fi

. "$_brandt_utils"
. "$_this_conf"

function is_workday() {
	# Verify it is not the Mon-Fri during working hours.
	_day_of_week=$( lower "${1:-$( date +%a )}" )
	_hour_of_day=${2:-$( date +%H )}

	if [ "$_day_of_week" != "sat" ] && [ "$_day_of_week" != "sun" ]; then
		for _hour in $( echo "$_backup_veto_hours" | tr "," "\n" ); do
			test "$_hour_of_day" == "$_hour" && return 0
		done
	fi
	return 1
}

function setup() {
    local _status=0
    echo -n "Create CRON Job to run this script "    
    ln -sf "$_this_script" "$_this_cron" > /dev/null 2>&1
    brandt_status setup
    _status=$?

    ln -sf "$_this_script" "$_this_rc" > /dev/null 2>&1
    _status=$(( $_status | $? ))    

    chownmod root:root 644 "$_this_conf" > /dev/null 2>&1
    _status=$(( $_status | $? ))

    exit $(( $_status | $? ))
}

function usage() {
    local _exitcode=${1-0}
    local _output=2
    [ "$_exitcode" == "0" ] && _output=1
    [ "$2" == "" ] || echo -e "$2"
    ( echo -e "Usage: $0 [options]"
	  echo -e "Script to backup Zarafa files to the backup server."
      echo -e "Options:"
      echo -e " -h, --help     display this help and exit"
      echo -e " -v, --version  output version information and exit" ) >&$_output
    exit $_exitcode
}

# Execute getopt
if ! _args=$( getopt -o vh -l "setup,help,version" -n "$0" -- "$@" 2>/dev/null ); then
    _err=$( getopt -o vh -l "setup,help,version" -n "$0" -- "$@" 2>&1 >/dev/null )
    usage 1 "${BOLD_RED}$_err${NORMAL}"
fi

#Bad arguments
#[ $? -ne 0 ] && usage 1 "$0: No arguments supplied!\n"

eval set -- "$_args";
while /bin/true ; do
    case "$1" in
             --setup )     setup ;;
        -h | --help )      usage 0 ;;
        -v | --version )   brandt_version $_version ;;
        -- )               shift ; break ;;
        * )                usage 1 "${BOLD_RED}$0: Invalid argument!${NORMAL}" ;;
    esac
    shift
done

if ! is_workday
then
	if [ -d "$_backup_source" ]; then
		run-one rsync -a ${_backup_source}/* ${_backup_user}@${_backup_dest}
	else
		echo "Unable to find source directory: $_backup_source" 1>&2
	fi 
fi

exit $?