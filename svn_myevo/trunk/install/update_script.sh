#!/bin/bash
# git config credential.helper store
set -x
SVNDIR="/root/myevo_odoo_addons"

ABSSCRIPT="`readlink -f $0`"
HERE="`dirname $ABSSCRIPT`"
TIMESTAMP="`date +'%Y%m%d%H%M%S'`"

cd $SVNDIR
SVNROOT="`svn info | grep \"Repository Root:\" | cut -d' ' -f3 `"
read -p "Please enter TAG (enter for trunk):"  TAG
if [ "x$TAG" = "x" ];
then
 SVN_SWITCH="svn switch $SVNROOT/trunk/" 
else
 SVN_SWITCH="svn switch $SVNROOT/tags/$TAG"
fi




# Stoping API
/etc/init.d/odoo_api stop

# Saving last Code
echo "Saving the code"
cd /root/
tar -cvf ${TIMESTAMP}_myevo_odoo_addons.tar repo

echo "Pulling the latest commit at $TAG"
set -x
cd $SVNDIR
$SVN_SWITCH
svn update
CODE=$?
if [ $CODE -ne 0 ];
then
  echo "SVN pb"
  exit $CODE
fi


# Replace Bug in odoo 9
MD5TRANS="`md5sum /opt/odoo/addons/web_editor/static/src/js/transcoder.js | cut  -d' ' -f1`"
if [ "$MD5TRANS" = "fccab8d343bdefaa3aa87095f45257ca" ];
then
   echo "Old transcoder. Replace with new one"
   cp -p $SVNDIR/soupese_base/static/src/js/transcoder.js /opt/odoo/addons/web_editor/static/src/js/transcoder.js
fi

# 
if [ ! -d /var/spool/odoo_json ];
then
   mkdir /var/spool/odoo_json
   chmod a+rwx /var/spool/odoo_json
fi


cd $HERE

for DB in `su - postgres -c "psql -c \"SELECT '--> '||datname FROM pg_database WHERE datistemplate = false;\" | grep '^\s*--> ' | cut -d' ' -f3"` ;
do
   echo "`date`:Backup $DB "
   su - postgres -c "pg_dump -Fp -b -c -C --if-exist -o  ${DB} > ${TIMESTAMP}_${DB}.dump"

   if [[ $DB == db* ]];
   then
      CMD="/home/odoo/odoo/bin/python /opt/odoo/openerp-server -c /etc/odoo-server.conf -u soupese_base -d $DB --stop-after-init --xmlrpc-port 8090 --logfile=/var/log/odoo/odoo-server-update.log"
      echo "`date`: $DB is a odoo database, will refresh the db"
      su - odoo -c "$CMD"
   fi

done



# Start API
/etc/init.d/odoo_api start

# Restart Odoo server
/etc/init.d/odoo stop
sleep 5
/etc/init.d/odoo start

