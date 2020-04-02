#!/bin/bash

appdir="/home/$USER/greek-xmltv/"
compose_file="${appdir}docker-compose.yml"
export_dir="${appdir}scrapy_export/"
target_dir="/mnt/storage/Downloads/xmltv/"

/usr/local/bin/docker-compose -f "$compose_file" up -d & sleep 300; /usr/local/bin/docker-compose stop
cp "${export_dir}"*.xml "${target_dir}"
rm -r "${export_dir}"*.xml
# remove json files older thatn 7 days.
find "${export_dir}"*.json -mtime +7 -type f -delete