#!/bin/bash
# git config credential.helper store
set -x

SVNDIR="/root/myevo_odoo_addons"

ABSSCRIPT="`readlink -f $0`"
HERE="`dirname $ABSSCRIPT`"
TIMESTAMP="`date +'%Y%m%d%H%M%S'`"

#TODO use diff3 please
ln -s $SVNDIR/install/etc/odoo /etc/init.d/odoo
ln -s $SVNDIR/install/etc/odoo_api /etc/init.d/odoo_api
ln -s $SVNDIR/install/etc/odoo-server.conf /etc/odoo-server.conf

# Start API
/etc/init.d/odoo_api start

# Restart Odoo server
/etc/init.d/odoo start

