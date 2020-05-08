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
from typing import Tuple, Optional, Union, List

import lxml.etree as et
from pytz import timezone

COUNTRY = 'GREECE'
LANG_GR = 'el'
LANG_EN = 'en'
JSON_FILE_PATH = 'export/'
JSON_FILE = '*.json'
XMLTV_FILE_PATH = 'export/'
XMLTV_FILE = f'xmltv_{COUNTRY}_{LANG_GR}.xml'
LOCAL_TZ = 'Europe/Athens'
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


def get_project_root() -> str:
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
    Functionality to create a Xmltv-formatted file from a json file with station/programme data for Greece.
    """

    def __init__(self, json_file: Optional[str] = None, xmltv_file: Optional[str] = None,
                 cache_file: Optional[str] = None, use_proj_dir: bool = True, multi_json: bool = False) -> None:
        self._project_dir = Path(get_project_root())  # or Path(__file__).parent.parent giving: /home/xxxxxxx/PycharmProjects/greek-xmltv/xmltv
        self.multi_json = multi_json
        self.json_file = json_file
        self.xmltv_file = (xmltv_file, use_proj_dir)
        self.cache_file = (cache_file, use_proj_dir)
        self.json_data: list = []
        self.chnl_cache: dict = {}
        self._dataloaded: bool = False
        self._newcache: bool = False
        self._create_cachefile: bool = False
        self.tree_loaded = False
        self.root = et.Element("tv", attrib={"date": "placeholder",
                                             "source-info-name": "Digea.gr-Ert.gr",
                                             "generator-info-name": "greek-xmltv",
                                             "generator-info-url": "https://liatas.com"})
        self.xtree = et.ElementTree(self.root)

    @property
    def json_file(self) -> Union[Path, List[str]]:
        return self.__jsonfile

    @json_file.setter
    def json_file(self, jsonf: Optional[str]) -> None:
        if self.multi_json:
            if jsonf and Path(jsonf).parent.is_dir():
                self.__jsonfile = glob.glob(jsonf)
            else:
                self.__jsonfile = glob.glob(str(self._project_dir / JSON_FILE_PATH / JSON_FILE))
        else:
            if jsonf and Path(jsonf).exists():
                self.__jsonfile = Path(jsonf)
            else:
                self.__jsonfile = Path(max(glob.iglob(str(self._project_dir / JSON_FILE_PATH / JSON_FILE)),
                                           key=os.path.getctime))
        self._dataloaded = False

    @property
    def xmltv_file(self) -> Path:
        return self.__xmltvfile

    @xmltv_file.setter
    def xmltv_file(self, values: Tuple[Optional[str], bool]) -> None:
        (xmltvf, use_proj_dir) = values
        if xmltvf and use_proj_dir:
            self.__xmltvfile = self._project_dir / XMLTV_FILE_PATH / xmltvf
        elif xmltvf and Path(xmltvf).parent.exists():
            self.__xmltvfile = Path(xmltvf)
        else:
            self.__xmltvfile = self._project_dir / XMLTV_FILE_PATH / XMLTV_FILE

    @property
    def cache_file(self) -> Path:
        return self.__cachefile

    @cache_file.setter
    def cache_file(self, values: Tuple[Optional[str], bool]) -> None:
        (cachef, use_proj_dir) = values
        if use_proj_dir:
            (self._project_dir / CACHE_DIR).mkdir(parents=True, exist_ok=True)
        if cachef and use_proj_dir:
            self.__cachefile = self._project_dir / CACHE_DIR / cachef
        elif cachef and Path(cachef).parent.exists():
            self.__cachefile = Path(cachef)
        else:
            self.__cachefile = self._project_dir / CACHE_DIR / CACHE_FILE

    def load_data(self) -> None:
        if isinstance(self.__jsonfile, Path):
            with self.__jsonfile.open() as fh:
                try:
                    self.json_data = json.load(fh)
                    self._dataloaded = True
                except Exception as ex:
                    print(f'Json read error while processing the file - {ex}')
                    self.json_data = []
        else:
            # Load and merge all json files from a directory into a single list
            # self.__jsonfile will be a list of file paths
            self.json_data = []
            for f in self.__jsonfile:
                with open(f) as json_file:
                    try:
                        self.json_data += json.load(json_file)
                        self._dataloaded = True
                    except Exception as ex:
                        print(f'Json read error while processing the file - {ex}')
                        self.json_data = []

    def load_cache(self) -> None:
        if self.__cachefile.is_file():
            # if cache file exists load it
            with self.__cachefile.open() as cf:
                try:
                    self.chnl_cache = json.load(cf)
                except Exception as ex:
                    print(f'Json read error while processing the cache file - {ex}')
                    self.chnl_cache = {}
            # validate loaded cache file, else invalidate and create new
            if not self._newcache:
                if len(self.json_data) <= len(self.chnl_cache):
                    for stn in self.json_data:
                        if stn["id"][0] in self.chnl_cache:
                            continue
                        else:
                            self.invalidate_cache()
                            break
                else:
                    self.invalidate_cache()
        else:
            # otherwise mark True to trigger the creation a new cache file
            self._create_cachefile = True
        if self._create_cachefile:
            self.create_channel_cache()

    def invalidate_cache(self) -> None:
        self.chnl_cache = {}
        if self.__cachefile.is_file():
            self.__cachefile.unlink()
        self._create_cachefile = True

    def create_channel_cache(self) -> None:
        # Create dictionary mapping for channel: number(id) and cache file
        hd_cntr = count(start=len(self.json_data) + 1)
        stationID_map = {
            sid["id"][0]: {"id": str(k), "channel": str(int(sid["id"][0][8:])),
                           "hashd": True if sid["name"][0] in HD_CHANNELS else False,
                           "hdid": str(next(hd_cntr)) if sid["name"][0] in HD_CHANNELS else '00'}
            for k, sid in enumerate(self.json_data, start=1)}
        with self.__cachefile.open(mode='w', encoding='utf-8') as fh:
            json.dump(stationID_map, fh, ensure_ascii=False, indent=4)
        self._newcache = True
        self._create_cachefile = False
        self.load_cache()

    def generate_xmltv(self, pref_regions: Optional[Tuple[str, ...]] = None, write_file: bool = True) -> None:
        """
        Generate the xmltv EPG context and optionally write the .xml file.
        Ref: https://github.com/XMLTV/xmltv/blob/master/xmltv.dtd
        Ref: https://github.com/essandess/sd-py/blob/master/sd_json.py
        :return: None
        """
        if not self._dataloaded:
            self.load_data()
        self.load_cache()

        if self.tree_loaded:
            self._clear_doc_root()

        self.root.attrib["date"] = datetime.now().astimezone(timezone(LOCAL_TZ)).strftime('%Y-%m-%d %H:%M:%S')

        _chnl = {"idx": 0}

        def add_channel(station: dict) -> None:
            # add channels
            channel = et.Element("channel", attrib={"id": self.chnl_cache[station["id"][0]]["id"]})
            et.SubElement(channel, "display-name", attrib={"lang": LANG_EN}).text = station["name"][0]
            if "img_url" in station:
                et.SubElement(channel, "icon", attrib={"src": station["img_url"][0]})
            self.root.insert(_chnl["idx"], channel)
            _chnl["idx"] += 1
            # if channel has HD version copy and adjust info
            if self.chnl_cache[station["id"][0]]["hashd"]:
                self.root.insert(_chnl["idx"], deepcopy(channel))
                self.root[_chnl["idx"]].attrib["id"] = self.chnl_cache[station["id"][0]]["hdid"]
                self.root[_chnl["idx"]].getchildren()[0].text = f'{station["name"][0]} HD'
                _chnl["idx"] += 1

        def add_chnl_programmes(station: dict) -> None:
            for i, prgm in enumerate(station["programmes"]):
                attrib_lang = {"lang": LANG_GR}
                # programme
                start = datetime.strptime(prgm["airDateTime"], "%Y%m%d%H%M%S %z")
                #   calculate duration
                try:
                    next_start = datetime.strptime(station["programmes"][i + 1]["airDateTime"], "%Y%m%d%H%M%S %z")
                except IndexError:
                    next_start = start.replace(hour=6, minute=0)
                duration = next_start - start  # duration is eg. datetime.timedelta(seconds=5400)
                stop = start + duration
                programme_attrib = {
                    "start": start.astimezone(timezone(LOCAL_TZ)).strftime("%Y%m%d%H%M%S %z"),
                    "stop": stop.astimezone(timezone(LOCAL_TZ)).strftime("%Y%m%d%H%M%S %z"),
                    "channel": self.chnl_cache[station["id"][0]]["id"]}
                programme = et.SubElement(self.root, "programme", attrib=programme_attrib)
                try:
                    (rating_value, title) = prgm["title"].split(maxsplit=1)
                except ValueError:
                    title = prgm["title"]
                    rating_value = '[K16]'
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
                # if channel has HD version copy and adjust programme info
                if self.chnl_cache[station["id"][0]]["hashd"]:
                    self.root.append(deepcopy(programme))
                    self.root[-1].attrib["channel"] = self.chnl_cache[station["id"][0]]["hdid"]
                    self.root[-1].getchildren()[2].getchildren()[-1].text = 'HDTV'

        for stn in self.json_data:
            if pref_regions:
                if stn["region"][0] in pref_regions:
                    add_channel(stn)
                    add_chnl_programmes(stn)
            else:
                add_channel(stn)
                add_chnl_programmes(stn)

        if write_file:
            self.write_xml_file()
        else:
            print(et.tostring(self.root, pretty_print=True, xml_declaration=True, encoding="UTF-8",
                              doctype='<!DOCTYPE tv SYSTEM "grxmltv.dtd">').decode())
        self.tree_loaded = True

    def write_xml_file(self) -> None:
        with open(str(self.__xmltvfile), 'wb') as xf:
            self.xtree.write(xf, encoding="UTF-8", pretty_print=True, xml_declaration=True,
                            doctype='<!DOCTYPE tv SYSTEM "grxmltv.dtd">')
        # with et.xmlfile(str(self.__xmltvfile), encoding="UTF-8") as xf:
        #     xf.write_declaration()
        #     xf.write_doctype('<!DOCTYPE tv SYSTEM "grxmltv.dtd">')
        #     xf.write(self.root, pretty_print=True)

    def _clear_doc_root(self):
        et.strip_elements(self.xtree, 'channel')
        et.strip_elements(self.xtree, 'programme')


if __name__ == '__main__':
    xmltv_f = JsonToXmltv(multi_json=True)
    xmltv_f.generate_xmltv()
    xmltv_f.xmltv_file = ('grxmltv_nat_el.xml', True)
    xmltv_f.generate_xmltv(pref_regions=('Nationwide', 'Attica-R-Z-9', 'National-public'))
