#!/bin/bash
# vim: shiftwidth=4 expandtab
DBUSER=openvpn
DBNAME=openvpn
CADIR=/home/pajukans/Temp/testca
SELINUXENABLED=/usr/sbin/selinuxenabled

set -e
source $(dirname $0)/env.sh

if [ -d "$CADIR" ]; then
        echo "Nuking the CA dir with sudo (it prolly has files owned by the web server"
        sudo rm -rf "$CADIR"
fi

mkdir -p "$CADIR"
chmod a+rwx "$CADIR"

if [ -x $SELINUXENABLED ]; then
    if $SELINUXENABLED; then
        echo "It seems you are running SELinux. Adjusting contexts for CA dir..."
        chcon -R -t httpd_sys_content_rw_t "$CADIR"
    fi
fi

dropdb -U $DBUSER $DBNAME
createdb -U $DBUSER -E UNICODE $DBNAME
python openvpnweb/manage.py syncdb --noinput

echo "Restarting Apache with sudo."
if [ -x /etc/init.d/httpd ]; then
    # Fedora
    sudo /etc/init.d/httpd reload
elif [ -x /etc/init.d/apache2 ]; then
    # Debian
    sudo /etc/init.d/apache2 force-reload
else
    echo "No known init script found for apache. Please restart it yourself."
fi

#python bin/reinit_hard.py
#python bin/reinit_soft.py
