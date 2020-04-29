# -*- coding: utf-8 -*-

# Refs:
# https://github.com/XMLTV/xmltv/blob/master/xmltv.dtd
# https://github.com/kgroeneveld/tv_grab_sd_json/blob/master/tv_grab_sd_json

import glob
import json
import os
from copy import deepcopy
from datetime import datetime
from itertools import count
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
CACHE_DIR = 'cache/'
CACHE_FILE = 'channels_id.json'
HD_CHANNELS = (
    # 'ERT SPORTS',   # ERT SPORTS HD
    'ALPHA',          # ALPHA HD
    'ANT1',           # ANT1 HD
    'OPEN BEYOND',    # OPEN BEYOND HD
    'M.tv',           # m.tv HD
    'SKAI',           # SKAI HD
    'STAR'            # STAR HD
)
# HD_CHANNELS = {
#     # 'ERT SPORTS',   # ERT SPORTS HD
#     'ALPHA': '41',        # ALPHA HD
#     'ANT1': '51',         # ANT1 HD
#     'OPEN BEYOND': '61',  # OPEN BEYOND HD
#     'M.tv': '71',         # m.tv HD
#     'SKAI': '81',         # SKAI HD
#     'STAR': '91'          # STAR HD
# }


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
        self.chnl_cache = None
        self._newcache = False
        self._create_cachefile = False
        self._project_dir = Path(get_project_root())  # or Path(__file__).parent.parent giving: /home/xxxxxxx/PycharmProjects/greek-xmltv/xmltv
        self.json_file_path = json_file_path or self._project_dir/JSON_FILE_PATH
        self.multi_json = multi_json
        if not self.multi_json:
            if not json_file:
                # get latest .json file from the directory specified
                self.json_file = max(glob.iglob(str(self.json_file_path/JSON_FILE)), key=os.path.getctime)
            else:
                self.json_file = self.json_file_path/json_file
        self.xmltv_file_path = xmltv_file_path or self._project_dir/XMLTV_FILE_PATH
        self.xmltv_file = xmltv_file or XMLTV_FILE
        self._cache_path = self._project_dir/CACHE_DIR
        self._cache_file = None

    def load_data(self):
        if not self.multi_json:
            if not self.json_file.is_file():
                print('No such file in directory:', self.json_file_path)
                self.json_data = {}
                return
            with self.json_file.open() as fh:
                try:
                    self.json_data = json.load(fh)
                    # json_prettyprint(self.json_data)
                except Exception as ex:
                    print(f'Json read error while processing the file - {ex}')
                    self.json_data = {}
        else:
            # Load and merge all json files from a directory into a single OrderedDict
            self.json_data = []
            for f in glob.glob(str(self.json_file_path/JSON_FILE)):
                with open(f) as json_file:
                    try:
                        self.json_data += json.load(json_file)
                    except Exception as ex:
                        print(f'Json read error while processing the file - {ex}')
                        self.json_data = []

    def load_cache(self, cache_file=''):
        if not cache_file:
            self._cache_path.mkdir(parents=True, exist_ok=True)
            self._cache_file = self._cache_path/CACHE_FILE
        else:
            self._cache_file = Path(cache_file)
        if self._cache_file.is_file():
            with self._cache_file.open() as cf:
                try:
                    self.chnl_cache = json.load(cf)
                except Exception as ex:
                    print(f'Json read error while processing the cache file - {ex}')
                    self.chnl_cache = {}
            # validate loaded cache file, else invalidate and create new
            if not self._newcache:
                if len(self.json_data) == len(self.chnl_cache):
                    for stn in self.json_data:
                        if stn["id"][0] in self.chnl_cache:
                            continue
                        else:
                            self.invalidate_cache()
                            break
                else:
                    self.invalidate_cache()
        else:
            self._create_cachefile = True
        if self._create_cachefile:
            self.create_channel_cache()

    def invalidate_cache(self):
        self.chnl_cache = {}
        if self._cache_file.is_file():
            self._cache_file.unlink()
        self._create_cachefile = True

    def create_channel_cache(self):
        # Create dictionary mapping for channel: number(id) and cache file
        hd_cntr = count(start=len(self.json_data) + 1)
        stationID_map_dict = {
            sid["id"][0]: {"id": str(k), "channel": str(int(sid["id"][0][8:])),
                           "hashd": True if sid["name"][0] in HD_CHANNELS else False,
                           "hdid": str(next(hd_cntr)) if sid["name"][0] in HD_CHANNELS else '00'}
            for k, sid in enumerate(self.json_data, start=1)}
        with self._cache_file.open(mode='w', encoding='utf-8') as fh:
            json.dump(stationID_map_dict, fh, ensure_ascii=False, indent=4)
        self._newcache = True
        self._create_cachefile = False
        self.load_cache()

    def write_xmltv_file(self):
        """
        Write the xmltv.xml EPG file.
        Ref: https://github.com/essandess/sd-py/blob/master/sd_json.py
        :return: None
        """
        self.load_data()
        self.load_cache()

        current_datetime = datetime.now().astimezone(timezone(LOCAL_TZ)).strftime('%Y-%m-%d %H:%M:%S')

        root = et.Element("tv",
                          attrib={"date": current_datetime,
                                  "source-info-name": "Digea.gr-Ert.gr",
                                  "generator-info-name": "greek-xmltv",
                                  "generator-info-url": "https://liatas.com"})

        for stn in self.json_data:
            channel = et.SubElement(root, "channel", attrib={"id": self.chnl_cache[stn["id"][0]]["id"]})
            et.SubElement(channel, "display-name", attrib={"lang": LANG_EN}).text = stn["name"][0]
            if "img_url" in stn:
                icon = et.SubElement(channel, "icon", attrib={"src": stn["img_url"][0]})
            if self.chnl_cache[stn["id"][0]]["hashd"]:
                channel = et.SubElement(root, "channel", attrib={"id": self.chnl_cache[stn["id"][0]]["hdid"]})
                et.SubElement(channel, "display-name", attrib={"lang": LANG_EN}).text = f'{stn["name"][0]} HD'

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
                    "channel": self.chnl_cache[stn["id"][0]]["id"]}
                programme = et.SubElement(root, "programme", attrib=programme_attrib)
                (rating_value, title) = prgm["title"].split(maxsplit=1)
                # programme title
                et.SubElement(programme, "title", attrib=attrib_lang).text = title
                # description
                et.SubElement(programme, "desc", attrib=attrib_lang).text = prgm["desc"]
                # video
                video = et.SubElement(programme, "video")
                et.SubElement(video, "present").text = 'yes'
                et.SubElement(video, "colour").text = 'yes'
                et.SubElement(video, "aspect").text = '16:9'
                et.SubElement(video, "quality").text = 'SDTV'
                # audio
                audio = et.SubElement(programme, "audio")
                et.SubElement(audio, "present").text = 'yes'
                et.SubElement(audio, "stereo").text = 'stereo'
                # rating
                rating = et.SubElement(programme, "rating", attrib={"system": "Greek"})
                et.SubElement(rating, "value").text = rating_value.strip('[]')
                if self.chnl_cache[stn["id"][0]]["hashd"]:
                    root.append(deepcopy(programme))
                    root[-1].attrib["channel"] = self.chnl_cache[stn["id"][0]]["hdid"]
                    root[-1].getchildren()[-3].getchildren()[-1].text = 'HDTV'

        # (re-)write the XML file
        with et.xmlfile(str(self.xmltv_file_path/self.xmltv_file), encoding="UTF-8") as xf:
            xf.write_declaration()
            xf.write_doctype('<!DOCTYPE tv SYSTEM "grxmltv.dtd">')
            xf.write(root, pretty_print=True)

        # print(et.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8", doctype='<!DOCTYPE tv SYSTEM "xmltv.dtd">').decode())


if __name__ == '__main__':
    xmltv_f = JsonToXmltv(multi_json=True)
    xmltv_f.write_xmltv_file()


