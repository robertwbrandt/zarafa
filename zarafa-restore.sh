#!/bin/bash


getIndex() {
	_username="$1"

	oldIndex=$( find /srv/backup/brick-level-backup.zarafa1/ -type f -iname "$_username.index.zbk" )
    newIndex=$( find /srv/backup/brick-level-backup/ -type f -iname "$_username.index.zbk" )
    rm /srv/backup/zarafa-core.index

	if [ -n "$oldIndex" ] && [ -n "$newIndex" ]; then
		/usr/share/zarafa-backup/readable-index.pl "$oldIndex" | cut -f 1 | sort > /srv/backup/zarafa1.index
		/usr/share/zarafa-backup/readable-index.pl "$newIndex" | cut -f 1 | sort > /srv/backup/zarafa-core.index
		diff /srv/backup/zarafa1.index /srv/backup/zarafa-core.index | sed -n "s|< ||p"
	fi
}

for file in $( find /srv/backup/brick-level-backup.zarafa1/ -type f -iname "*.index.zbk" -print | sort )
do
	user=$( basename "$file" | sed "s|.index.zbk$||" )
	[ "$user" == "brandtb" ] && continue
	echo "Working on user $user"
	for index in $( getIndex "$user" )
	do
		echo "  $index"
		zarafa-restore -r -u "$user" -f "/srv/backup/brick-level-backup.zarafa1/$user" "$index"
	done
done
