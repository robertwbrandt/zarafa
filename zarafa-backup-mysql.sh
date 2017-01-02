#!/bin/bash
#
#     Script to backup Zarafa files to the backup server.
#     Bob Brandt <projects@brandt.ie>
#  

_version=0.4
_brandt_utils=/opt/brandt/common/brandt.sh
_this_conf=/etc/brandt/zarafa-backup-mysql.conf
_this_script=/opt/brandt/zarafa/zarafa-backup-mysql.sh
_this_rc=/usr/local/bin/zarafa-backup-mysql
_this_cron=/etc/cron.hourly/zarafa-backup-mysql

[ ! -r "$_brandt_utils" ] && echo "Unable to find required file: $_brandt_utils" 1>&2 && exit 6
if [ ! -r "$_this_conf" ]; then
    ( echo -e "#     Configuration file for script to backup Zarafa MySQL databases."
      echo -e "#     Bob Brandt <projects@brandt.ie>\n#"
      echo -e "_backup_mysql_type='SLAVE'"
      echo -e "_backup_mysql_slave='SLAVE'"
      echo -e "_backup_mysql_credentials='/etc/mysql/debian.cnf'"
      echo -e "_backup_mysql_dest='/srv/backup/sql-backup/zarafa-mysql-backup.sql'"
      echo -e "_backup_mysql_log='/srv/backup/sql-backup/zarafa-mysql-backup.log'" ) > "$_this_conf"
    echo "Unable to find required file: $_this_conf" 1>&2
fi

. "$_brandt_utils"
. "$_this_conf"


function setup() {
    local _status=0
    # echo -n "Create CRON Job to run this script "    
    # ln -sf "$_this_script" "$_this_cron" > /dev/null 2>&1
    # brandt_status setup
    # _status=$?

    ln -sf "$_this_script" "$_this_rc" > /dev/null 2>&1
    _status=$(( $_status | $? ))    

    chownmod root:root 644 "$_this_conf" > /dev/null 2>&1
    _status=$(( $_status | $? ))

    exit $(( $_status | $? ))
}

function MySQL_Server_Properties() {
	_SlaveThreadCount=$( mysql --defaults-file=$_backup_mysql_credentials -e "SELECT COUNT(1) SlaveThreadCount FROM information_schema.processlist WHERE user='system user'\G" | sed -n "s|SlaveThreadCount:\s*||p" )

	if [ "$_SlaveThreadCount" == "0" ]; then
		echo "Server_Type: MASTER"
		return 0
	elif [ "$_SlaveThreadCount" == "1" ]; then
		echo "Server_Type: SLAVE (Replication is broken)"
		_status=1
	elif [ "$_SlaveThreadCount" == "2" ]; then
		echo "Server_Type: SLAVE (Replication is running)"
		_status=0		
	else
		if [ -n "$_SlaveThreadCount" ]; then
			echo "Server_Type: ERROR "
		else
			echo "Server_Type: ERROR ($_SlaveThreadCount)"
		fi
		return 2
	fi

	_slave_output=$( mysql --defaults-file=$_backup_mysql_credentials -e "SHOW SLAVE STATUS\G" )

	_Slave_IO_Running=$( echo "$_slave_output" | sed -n "s|\s*Slave_IO_Running:\s*||p" )
	_Slave_SQL_Running=$( echo "$_slave_output" | sed -n "s|\s*Slave_SQL_Running:\s*||p" )
	_Seconds_Behind_Master=$( echo "$_slave_output" | sed -n "s|\s*Seconds_Behind_Master:\s*||p" )
	_Last_IO_Errno=$( echo "$_slave_output" | sed -n "s|\s*Last_IO_Errno:\s*||p" )
	_Last_SQL_Errno=$( echo "$_slave_output" | sed -n "s|\s*Last_SQL_Errno:\s*||p" )
	_SQL_Remaining_Delay=$( echo "$_slave_output" | sed -n "s|\s*SQL_Remaining_Delay:\s*||p" )
	_Slave_SQL_Running_State=$( echo "$_slave_output" | sed -n "s|\s*Slave_SQL_Running_State:\s*||p" )

	echo "Slave_IO_Running: $_Slave_IO_Running"
	echo "Slave_SQL_Running: $_Slave_SQL_Running"
	echo "Seconds_Behind_Master: $_Seconds_Behind_Master"
	echo "Last_IO_Errno: $_Last_IO_Errno"
	echo "Last_SQL_Errno: $_Last_SQL_Errno"
	echo "SQL_Remaining_Delay: $_SQL_Remaining_Delay"
	echo "Slave_SQL_Running_State: $_Slave_SQL_Running_State"
	return $_status
}

function printLog() {
	echo -e "$1"
	echo -e "$(date +%Y/%m/%d-%H:%m:%S)\t$1"
}

function convertSeconds() {
	declare -i _seconds=$1
  declare -i _minutes=0
  declare -i _hours=0
  declare -i _days=0

  [[ "$_seconds" -ne "$1" ]] && _seconds=-1
	
  if (( _seconds > 59 )); then
    _minutes=$(( _seconds/60 ))
    _seconds=$(( _seconds%60 ))
  fi
  if (( _minutes > 59 )); then
    _hours=$(( _minutes/60 ))
    _minutes=$(( _minutes%60 ))
  fi
  if (( _hours > 23 )); then
    _days=$(( _hours/24 ))
    _hours=$(( _hours%24 ))
  fi

  if (( _days < 1 )); then
  	if (( _hours < 1 )); then
  		if (( _minutes < 1 )); then
	  		printf "%02d\n" $_seconds  			
  		else
	  		printf "%02d:%02d\n" $_minutes $_seconds
  		fi
  	else
  		printf "%02d:%02d:%02d\n" $_hours $_minutes $_seconds
  	fi
  else
  	printf "%02d:%02d:%02d:%02d\n" $_days $_hours $_minutes $_seconds
  fi
  return 0
}


function usage() {
    local _exitcode=${1-0}
    local _output=2
    [ "$_exitcode" == "0" ] && _output=1
    [ "$2" == "" ] || echo -e "$2"
    ( echo -e "Usage: $0 [options]"
	  echo -e "Script to backup Zarafa MySQL Databases to $_backup_mysql_dest."
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

convertSeconds $1

#MySQL_Server_Properties


exit $?