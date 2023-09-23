#!/bin/bash

cd /opt/cryosparc_master/templates/ || (printf "Error: /opt/cryosparc_master/templates/ not found\n" && exit 1)

../bin/cryosparcm start
../bin/cryosparcm createuser --email "a@a.com" --password "a" --username "myuser" --firstname "John" --lastname "Doe"
../bin/cryosparcm cluster connect

