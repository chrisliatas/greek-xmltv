#!/usr/bin/env bash
# Run this with `sudo` to install a new cron for root that runs the daily job for greek-xmltv.

appdir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
command="/bin/bash ${appdir}/getxmltv.sh >> /var/log/cron.log"
job="45 5 * * * $command"
cat <(fgrep -i -v "$command" <(crontab -l)) <(echo "$job") | crontab -