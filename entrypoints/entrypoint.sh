#!/bin/bash

# Because of cluster_info.json and cluster_script.sh
cd /opt/cryosparc_master/entrypoints/ || (printf "Error: /opt/cryosparc_master/templates/ not found\n" && exit 1)
../bin/cryosparcm start
#../bin/cryosparcm createuser --email "a@a.com" --password "a" --username "myuser" --firstname "John" --lastname "Doe"
../bin/cryosparcm cluster connect

