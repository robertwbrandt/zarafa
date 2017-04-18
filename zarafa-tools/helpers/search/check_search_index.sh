#!/usr/bin/env bash
# Note : Even when the kyoto files are consistent this is not a guarantee that the keys have been written directly.

if [ ! -e /etc/zarafa/search.cfg ]
    then
        echo No zarafa search.cfg found
        exit 1
fi

SEARCHFOL=$(grep ^index_path /etc/zarafa/search.cfg | awk '{print $3}')

if ( ! which kctreemgr > /dev/null 2>&1  )
     then
        echo Cannot find kctreemgr.
        echo Please install the Zarafa provided kyotocabinet-bin package
        exit 1
fi
for a in ${SEARCHFOL}*.kct
do
    echo Checking file ${a}
    if ( ! kctreemgr check -onr ${a}  > /dev/null 2>&1 )  
    then
        if ( echo {$a} | grep "-" )
            then
                echo Warning: user index \"${a}\" is corrupt.
        else
                echo Warning: global index \"${a}\" is corrupt.
        fi
    else
        echo Check of ${a} okay 
    fi
   echo " "
done
