#!/usr/bin/env bash
# Run this script from the directory it is in with the Dockerfile and docker-compose.yml

timestamp() {
  date '+%d-%m-%Y %H:%M:%S'
}

appdir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
compose_file="${appdir}/docker-compose.yml"
export_dir="${appdir}/scrapy_export"
target_dir="/mnt/storage/Downloads/xmltv"
generated_xmltv_dir="${appdir}/generated_xmltv"

echo "$(timestamp): getxmltv - Starting docker-compose services"
echo ""
/usr/local/bin/docker-compose -f "$compose_file" up -d && sleep 300; /usr/local/bin/docker-compose -f "$compose_file" stop
echo ""
echo "$(timestamp): getxmltv - Stopped docker-compose services"
[ ! -d "$target_dir" ] && mkdir -p "$target_dir" && chmod 777 "$target_dir"
[ ! -d "$generated_xmltv_dir" ] && mkdir -p "$generated_xmltv_dir" && chmod 777 "$generated_xmltv_dir"
cp "${export_dir}"/* "${target_dir}"/
cp "${export_dir}"/*.xml "${generated_xmltv_dir}"/
rm -f "${export_dir}"/*
chmod 666 "${target_dir}"/*
chmod 666 "${generated_xmltv_dir}"/*
# remove json files older than 7 days.
find "${target_dir}"/*.json -mtime +7 -type f -delete
# Commit new generated xmltv file and git push
cd "$appdir" && /usr/bin/git add --all && /usr/bin/git commit -m "Auto generated xmltv files for $(timestamp)"
cd "$appdir" && /usr/bin/git push origin master
echo "$(timestamp): getxmltv - Finished"
