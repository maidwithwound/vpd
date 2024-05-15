import requests
from pathvalidate import sanitize_filename

class audio_obj:
    def __init__(self, audio_obj, position=-1, restore_obj=False):
        self.position = position 
        self.audio_id = audio_obj["id"]
        self.title = audio_obj["title"]
        self.subtitle = audio_obj["subtitle"] if "subtitle" in audio_obj else ""
        self.artist = audio_obj["artist"]
        self.owner_id = audio_obj["owner_id"]
        self.url = audio_obj["url"]
        if not restore_obj:
            if "album" in audio_obj:
                self.album = audio_obj["album"]["title"]
                self.thumb_url = audio_obj["album"]["thumb"]["photo_1200"]
            else:
                self.album = ""
                self.thumb_url = ""
        else:
            self.thumb_url = audio_obj["thumb_url"]
            self.position = audio_obj["position"]
            self.album = audio_obj["album"]



    def parse(self):
        return {
            "position": self.position,
            "id": self.audio_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "artist": self.artist,
            "album": self.album,
            "owner_id": self.owner_id,
            "url": self.url,
            "thumb_url": self.thumb_url
        }

    def generate_file_name(self):
        if self.position != -1:
            return sanitize_filename(f"[{str(self.position).rjust(4, '0')}] {self.artist} - {self.title}.mp3")
        else:
            return sanitize_filename(f"{self.artist} - {self.title}.mp3")


    def check_thumbnail(self) -> bool:
        return True if self.thumb_url else False

    def download_thumbnail(self) -> bytes:
        return requests.get(self.thumb_url).content

    def __str__(self): return str(self.parse())
    def __repr__(self): return self.__str__()
