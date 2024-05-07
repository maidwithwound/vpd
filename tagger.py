from requests import exceptions
from audio_obj import audio_obj
import music_tag

class tagger:
    def __init__(self):
        pass

    def process(self, path, song: audio_obj):
        obj = music_tag.load_file(path)
        if obj is not None:
            if song.subtitle:
                obj["tracktitle"] = f"{song.title} [{song.subtitle}]"
            else:
                obj["tracktitle"] = song.title
            obj["artist"] = song.artist
            obj["album"] = song.album

            if song.check_thumbnail():
                obj["artwork"] = song.download_thumbnail()

            obj.save()
