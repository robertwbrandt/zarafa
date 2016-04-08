#!/bin/bash
#
#     Script to run the z-push fixstates command and record to output in a log file.
#     Bob Brandt <projects@brandt.ie>
#  

_version=0.4
_brandt_utils=/opt/brandt/common/brandt.sh
_this_conf=/etc/brandt/z-push-fixstates.conf
_this_script=/opt/brandt/zarafa/z-push-fixstates.sh
_this_rc=/usr/local/bin/z-push-fixstates
_this_cron=/etc/cron.daily/z-push-fixstates

[ ! -r "$_brandt_utils" ] && echo "Unable to find required file: $_brandt_utils" 1>&2 && exit 6
if [ ! -r "$_this_conf" ]; then
    ( echo -e "#     Configuration file for z-push fixstates command script"
      echo -e "#     Bob Brandt <projects@brandt.ie>\n#"
      echo -e "_z_push_admin=/usr/share/z-push/z-push-admin.php"      
      echo -e "_log_file=/var/log/z-push/fixstates.log" ) > "$_this_conf"
    echo "Unable to find required file: $_this_conf" 1>&2
fi

. "$_brandt_utils"
. "$_this_conf"

function fixstate_cmd() {
	_z_push_admin -a fixstates
	return $?
}

function date_code() {
	_tmp=$( date "+%d/%m/%Y %H:%M:%S [INFO]" )" $@"
	echo $_tmp
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

[ ! -x "$_z_push_admin" ] && echo "Unable to find required file: $_z_push_admin" 1>&2 && exit 6

touch "$_log_file" > /dev/null 2>&1
test -w "$_log_file" || echo "Unable to write to log file: $_log_file" 1>&2
fixstate_cmd | (
while read _line
do
	if [ -n "$_line" ]; then
		_line=$( date_code "$_line" )
		test -w "$_log_file" && echo "$_line" >> "$_log_file"
		echo "$_line" 1>&2
	else
		echo "" 1>&2
	fi
done	
)

exit $?
