#!/usr/bin/env bash
#
# Karl Keusgen
# 2020-12-16
#
#
# Setup not directly from the cratch, but a prepared installation
#
# for setup from the scratch have a look at: MakeItRunAfterClone.txt

# do an update
git pull

sudo rm -f /etc/logrotate.d/multuslogs

sudo cp /multus/share/Configs/logrotate.d/multuslogs /etc/logrotate.d/
sudo cp /multus/share/Configs/systemd/system/multusd.service /etc/systemd/system/
# option
#sudo systemctl enable multusd

#delete unsufficient and old files
rm -f /multus/etc/multusd_d/*
rm -f /multus/lib/proto/*.py
sudo rm -f /multus/lib/proto/__pycache__/*
sudo rm -f /multus/lib/__pycache__/*

## put configs into place
cp -r /multus/share/Configs/etc /multus/

# make dir writable by http
mkdir /multus/openvpn
sudo chmod -R a+w /multus/openvpn

mkdir /multus/tmp
chmod -R a+w /multus/tmp

mkdir /multus/log
mkdir /multus/run

chmod a+x /multus/bin/*.py
chmod a+x /multus/bin/*.sh

chmod a+w /multus/etc/multusd_d/*

/multus/share/DoAllProtoFiles.sh

echo "Erfolgreich installiert .. configure VPN-Connection by http and reboot then" 
