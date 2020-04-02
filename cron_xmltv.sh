#!/bin/bash

command="/bin/bash /home/$USER/greek-xmltv/getxmltv.sh"
job="0 45 5 ? * * * $command"
cat <(fgrep -i -v "$command" <(crontab -l)) <(echo "$job") | crontab -