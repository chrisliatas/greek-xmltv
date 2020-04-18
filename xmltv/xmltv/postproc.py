# -*- coding: utf-8 -*-

# Refs:
# https://github.com/XMLTV/xmltv/blob/master/xmltv.dtd
# https://github.com/kgroeneveld/tv_grab_sd_json/blob/master/tv_grab_sd_json

import glob
import json
import os
from datetime import datetime
from pathlib import Path

import lxml.etree as et
from pytz import timezone

COUNTRY = 'GREECE'
JSON_FILE_PATH = 'export/'
JSON_FILE = '*.json'
XMLTV_FILE_PATH = 'export/'
XMLTV_FILE = f'xmltv_{COUNTRY}.xml'
LOCAL_TZ = 'Europe/Athens'
LANG_GR = 'el'
LANG_EN = 'en'


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
    def __init__(self, json_file_path='', json_file='', xmltv_file_path='', xmltv_file='', multi_json=False):
        self.json_data = None
        self.prog_cache = None
        self._project_dir = get_project_root()  # or Path(__file__).parent.parent giving: /home/xxxxxxx/PycharmProjects/greek-xmltv/xmltv
        self.json_file_path = json_file_path or os.path.join(self._project_dir, JSON_FILE_PATH)
        self.multi_json = multi_json
        if not self.multi_json:
            if not json_file:
                # get latest .json file from the directory specified
                self.json_file = max(glob.iglob(os.path.join(self.json_file_path + JSON_FILE)), key=os.path.getctime)
            else:
                self.json_file = os.path.join(self.json_file_path + json_file)
        self.xmltv_file_path = xmltv_file_path or os.path.join(self._project_dir, XMLTV_FILE_PATH)
        self.xmltv_file = xmltv_file or XMLTV_FILE

    def load_data(self):
        if not self.multi_json:
            if not os.path.isfile(self.json_file):
                print('No such file in directory:', self.json_file_path)
                self.json_data = {}
                return
            with open(self.json_file) as fh:
                try:
                    self.json_data = json.load(fh)
                    # json_prettyprint(self.json_data)
                except Exception as ex:
                    print(f'Json read error while processing the file - {ex}')
                    self.json_data = {}
        else:
            # Load and merge all json files from a directory into a single OrderedDict
            self.json_data = []
            for f in glob.glob(os.path.join(self.json_file_path + JSON_FILE)):
                with open(f) as json_file:
                    try:
                        self.json_data += json.load(json_file)
                    except Exception as ex:
                        print(f'Json read error while processing the file - {ex}')
                        self.json_data = []

    def write_xmltv_file(self):
        """
        Write the xmltv.xml EPG file.
        Ref: https://github.com/essandess/sd-py/blob/master/sd_json.py
        :return: None
        """
        self.load_data()

        current_datetime = datetime.now().astimezone(timezone(LOCAL_TZ)).strftime('%Y-%m-%d %H:%M:%S')

        root = et.Element("tv",
                          attrib={"date": current_datetime,
                                  "source-info-name": "Digea.gr-Ert.gr",
                                  "generator-info-name": "greek-xmltv",
                                  "generator-info-url": "https://liatas.com"})
        # channels
        stationID_map_dict = {
            sid["id"][0]: {"id": f'I{k}.{sid["region"][0]}.{sid["id"][0]}.'
                                 f'{"ert.gr" if int(sid["id"][0][8:]) < 100 else "digea.gr"}',
                           "channel": str(int(sid["id"][0][8:]))}
            for k, sid in enumerate(self.json_data)}

        for stn in self.json_data:
            channel = et.SubElement(root, "channel", attrib={"id": stationID_map_dict[stn["id"][0]]["id"]})
            # et.SubElement(channel, "display-name").text = f'{stationID_map_dict[stn["id"][0]]["channel"]} {stn["name"][0]}'
            et.SubElement(channel, "display-name", attrib={"lang": LANG_EN}).text = stn["name"][0]
            # et.SubElement(channel, "display-name").text = stationID_map_dict[stn["id"][0]]["channel"]
            if "img_url" in stn:
                icon = et.SubElement(channel, "icon", attrib={"src": stn["img_url"][0]})

        # programs
        for stn in self.json_data:
            for i, prgm in enumerate(stn["programmes"]):
                attrib_lang = {"lang": LANG_GR}
                # programme
                start = datetime.strptime(prgm["airDateTime"], "%Y%m%d%H%M%S %z")
                #   calculate duration
                try:
                    next_start = datetime.strptime(stn["programmes"][i + 1]["airDateTime"], "%Y%m%d%H%M%S %z")
                except IndexError:
                    next_start = start.replace(hour=6, minute=0)
                duration = next_start - start  # duration is eg. datetime.timedelta(seconds=5400)
                stop = start + duration
                programme_attrib = {
                    "start": start.astimezone(timezone(LOCAL_TZ)).strftime("%Y%m%d%H%M%S %z"),
                    "stop": stop.astimezone(timezone(LOCAL_TZ)).strftime("%Y%m%d%H%M%S %z"),
                    "channel": stationID_map_dict[stn["id"][0]]["id"]}
                programme = et.SubElement(root, "programme", attrib=programme_attrib)
                (rating_value, title) = prgm["title"].split(maxsplit=1)
                # programme title
                et.SubElement(programme, "title", attrib=attrib_lang).text = title
                # description
                et.SubElement(programme, "desc", attrib=attrib_lang).text = prgm["desc"]
                # rating
                rating = et.SubElement(programme, "rating", attrib={"system": "Greek"})
                et.SubElement(rating, "value").text = rating_value.strip('[]')

        # (re-)write the XML file
        f = os.path.join(self.xmltv_file_path + self.xmltv_file)
        with et.xmlfile(f, encoding="UTF-8") as xf:
            xf.write_declaration()
            xf.write_doctype('<!DOCTYPE tv SYSTEM "grxmltv.dtd">')
            xf.write(root, pretty_print=True)

        # print(et.tostring(root, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1", doctype='<!DOCTYPE tv SYSTEM "xmltv.dtd">').decode())


if __name__ == '__main__':
    xmltv_f = JsonToXmltv()
    xmltv_f.write_xmltv_file()


