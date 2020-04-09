#!/usr/bin/env bash
# Run this script from the directory it is in with the Dockerfile and docker-compose.yml

timestamp() {
  date '+%d-%m-%Y %H:%M:%S'
}

appdir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
compose_file="${appdir}/docker-compose.yml"
export_dir="${appdir}/scrapy_export"
target_dir="/mnt/storage/Downloads/xmltv"

echo "$(timestamp): getxmltv - Starting docker-compose services"
echo ""
/usr/local/bin/docker-compose -f "$compose_file" up -d && sleep 300; /usr/local/bin/docker-compose -f "$compose_file" stop
echo ""
echo "$(timestamp): getxmltv - Stopped docker-compose services"
[ ! -d "$target_dir" ] && mkdir -p "$target_dir" && chmod 777 "$target_dir"
cp "${export_dir}"/* "${target_dir}"/
rm -f "${export_dir}"/*
chmod 666 "$target_dir"/*
# remove json files older than 7 days.
find "${target_dir}"/*.json -mtime +7 -type f -delete
echo "$(timestamp): getxmltv - Finished"