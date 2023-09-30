import re
import json
import requests

from .config import Config
from .tools import *

class VideoInfo:
    url = aid = bvid = cid = None

    title = cover = duration = type = resolution = None

    pages = episodes = resolution_id = resolution_desc = []

    sections = {}

class VideoParser:
    def __init__(self, onError):
        self.onError = onError
    
    def get_aid(self, url):
        aid = re.findall(r"av([0-9]+)", url)

        if not aid: self.onError(101)

        bvid = convert_to_bvid(int(aid[0]))
        self.save_bvid(bvid)

    def get_bvid(self, url):
        bvid = re.findall(r"BV\w+", url)

        if not bvid: self.onError(101)

        self.save_bvid(bvid[0])

    def get_video_info(self):
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={VideoInfo.bvid}"
        
        req = requests.get(url, headers = get_header(VideoInfo.url, cookie = Config.User.sessdata), proxies = get_proxy(), auth = get_auth(), timeout = 8)
        resp = json.loads(req.text)

        self.check_json(resp, 101)

        info = resp["data"]

        VideoInfo.title = info["title"]
        VideoInfo.cover = info["pic"]
        VideoInfo.duration = info["duration"]
        VideoInfo.aid = info["aid"]
        VideoInfo.cid = info["cid"]
        VideoInfo.pages = info["pages"]

        if len(VideoInfo.pages) == 1:
            VideoInfo.type = 1
        else:
            VideoInfo.type = 2
        
        if "ugc_season" in info:
            VideoInfo.type = 3

            info_ugc_season = info["ugc_season"]
            info_section = info_ugc_season["sections"]
                
            VideoInfo.title = info_ugc_season["title"]

            VideoInfo.episodes = info_section[0]["episodes"]
            VideoInfo.sections["正片"] = VideoInfo.episodes
                
            if Config.Misc.show_sections:
                for section in info_section:
                    section_title = section["title"]
                    section_episodes = section["episodes"]

                    for index, value in enumerate(section_episodes):
                        value["title"] = str(index + 1)

                        VideoInfo.sections[section_title] = section_episodes

    def get_video_resolution(self):
        url = f"https://api.bilibili.com/x/player/playurl?bvid={VideoInfo.bvid}&cid={VideoInfo.cid}&qn=0&fnver=0&fnval=4048&fourk=1"
                
        req = requests.get(url, headers = get_header(cookie = Config.User.sessdata), proxies = get_proxy(), auth = get_auth(), timeout = 8)
        resp = json.loads(req.text)

        self.check_json(resp, 102)

        info = resp["data"]

        VideoInfo.resolution_id = info["accept_quality"]
        VideoInfo.resolution_desc = info["accept_description"]

    def parse_url(self, url):
        if "av" in url:
            self.get_aid(url)
        else:
            self.get_bvid(url)

        self.get_video_info()

        self.get_video_resolution()

    def save_bvid(self, bvid):
        VideoInfo.bvid, VideoInfo.url = bvid, f"https://www.bilibili.com/video/{bvid}"

    def check_json(self, json, err_code):
        if json["code"] != 0:
            self.onError(err_code)