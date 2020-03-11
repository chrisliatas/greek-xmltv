# -*- coding: utf-8 -*-

# Refs:
# https://github.com/XMLTV/xmltv/blob/master/xmltv.dtd
# https://github.com/kgroeneveld/tv_grab_sd_json/blob/master/tv_grab_sd_json

import os
from pathlib import Path
import json
import lxml.etree as et
from collections import OrderedDict


def json_prettyprint(j, *args, **kwargs):
    print(json.dumps(j, indent=4, sort_keys=True, ensure_ascii=False), *args, **kwargs)


def get_project_root():
    """
    There is no way in python to get project root. This function uses a trick.
    We know that the function that is currently running is in the project.
    We know that the root project path is in the list of PYTHONPATH
    look for any path in PYTHONPATH list that is contained in this function's path
    Lastly we filter and take the shortest path because we are looking for the root.
    :return: path to project root
    """
    apth = str(Path().absolute())
    ppth = os.environ['PYTHONPATH'].split(':')
    matches = [x for x in ppth if x in apth]
    project_root = min(matches, key=len)
    return project_root


def from_json_file(fname):
    if not fname:
        return {}
    project_dir = Path(__file__).parent.parent  # /home/xxxxxxx/PycharmProjects/greek-xmltv/xmltv
    data_dir = 'export/'
    f = os.path.join(project_dir, data_dir + fname)
    if not os.path.isfile(f):
        print('No such file in directory:', data_dir)
        return {}
    with open(f) as fh:
        try:
            data = json.load(fh, object_pairs_hook=OrderedDict)
        except Exception as e:
            print(f'Json read error while processing the file - {e}')
            data = {}
    return data


if __name__ == '__main__':
    data = from_json_file('digea_2020-03-11T14-48-30.json')
    # json_prettyprint(data)
    root = et.Element("tv",
                      attrib={"source-info-name": "Digea.gr", "generator-info-name": "greek-xmltv",
                              "generator-info-url": "https://liatas.com"})
    # channels
    # stationID_map_dict = {
    #     sid["stationID"]: {"id": f'I{k}.{sid["stationID"]}.schedulesdirect.org', "channel": str(int(sid["channel"]))}
    #     for k, sid in enumerate(self.api_channel_mapping_json["map"])}
    stationID_map_dict = {
        sid["id"][0]: {"id": f'I{k}.{sid["region"][0]}.{sid["id"][0]}.digea.gr', "channel": str(int(sid["id"][0][8:]))}
        for k, sid in enumerate(data)}

    for stn in data:
        channel = et.SubElement(root, "channel", attrib={"id": stationID_map_dict[stn["id"][0]]["id"]})
        # "mythtv seems to assume that the first three display-name elements are
        # name, callsign and channel number. We follow that scheme here."
        et.SubElement(channel, "display-name").text = f'{stationID_map_dict[stn["id"]]["channel"]} {stn["name"]}'
        et.SubElement(channel, "display-name").text = stn["name"]
        et.SubElement(channel, "display-name").text = stationID_map_dict[stn["id"]]["channel"]
        if "img_url" in stn:
            icon = et.SubElement(channel, "icon", attrib={"src": stn["img_url"]})

    print(et.tostring(root, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1", doctype='<!DOCTYPE tv SYSTEM "xmltv.dtd">').decode())
