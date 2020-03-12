# -*- coding: utf-8 -*-

# Refs:
# https://github.com/XMLTV/xmltv/blob/master/xmltv.dtd
# https://github.com/kgroeneveld/tv_grab_sd_json/blob/master/tv_grab_sd_json

import os
from pathlib import Path
import json
import lxml.etree as et
from collections import OrderedDict

COUNTRY = 'GREECE'
JSON_FILE_PATH = 'export/'
JSON_FILE = 'digea_2020-03-11T14-48-30.json'
XMLTV_FILE_PATH = 'export/'
XMLTV_FILE = f'xmltv_{COUNTRY}.xml'


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


class JsonToXmltv:
    """
    Functionality to create a Xmltv-formatted file from a json file with station/programme data
    """
    def __init__(self,
                 json_file_path=JSON_FILE_PATH,
                 json_file=JSON_FILE,
                 xmltv_file_path=XMLTV_FILE_PATH,
                 xmltv_file=XMLTV_FILE):
        self.json_data = None
        self.prog_cache = None
        self.project_dir = Path(__file__).parent.parent  # /home/xxxxxxx/PycharmProjects/greek-xmltv/xmltv
        self.json_file_path = json_file_path
        self.json_file = json_file
        self.xmltv_file_path = xmltv_file_path
        self.xmltv_file = xmltv_file

    def load_data(self):
        f = os.path.join(self.project_dir, self.json_file_path + self.json_file)
        if not os.path.isfile(f):
            print('No such file in directory:', self.json_file_path)
            self.json_data = {}
        with open(f) as fh:
            try:
                self.json_data = json.load(fh, object_pairs_hook=OrderedDict)
                # json_prettyprint(self.json_data)
            except Exception as e:
                print(f'Json read error while processing the file - {e}')
                self.json_data = {}

    def write_xmltv_file(self):
        """
        Write the xmltv.xml EPG file.
        :return: None
        """
        self.load_data()

        root = et.Element("tv",
                          attrib={"source-info-name": "Digea.gr", "generator-info-name": "greek-xmltv",
                                  "generator-info-url": "https://liatas.com"})
        # channels
        stationID_map_dict = {
            sid["id"][0]: {"id": f'I{k}.{sid["region"][0]}.{sid["id"][0]}.digea.gr', "channel": str(int(sid["id"][0][8:]))}
            for k, sid in enumerate(self.json_data)}

        for stn in self.json_data:
            channel = et.SubElement(root, "channel", attrib={"id": stationID_map_dict[stn["id"][0]]["id"]})
            et.SubElement(channel, "display-name").text = f'{stationID_map_dict[stn["id"][0]]["channel"]} {stn["name"][0]}'
            et.SubElement(channel, "display-name").text = stn["name"][0]
            et.SubElement(channel, "display-name").text = stationID_map_dict[stn["id"][0]]["channel"]
            if "img_url" in stn:
                icon = et.SubElement(channel, "icon", attrib={"src": stn["img_url"][0]})

        # programs
        for stn in self.json_data:
            for prgm in stn["programmes"]:
                attrib_lang = None
                # programme


        print(et.tostring(root, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1", doctype='<!DOCTYPE tv SYSTEM "xmltv.dtd">').decode())


if __name__ == '__main__':
    xmltv_f = JsonToXmltv()
    xmltv_f.write_xmltv_file()


