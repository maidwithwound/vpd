import asyncio
import json
from os import mkdir, remove, getcwd
from os.path import exists
from pprint import pp

import aiofiles
import aiohttp
from pathvalidate import sanitize_filename
import vk_api
import demoji

from audio_obj import audio_obj
from tagger import tagger


class megasuperdownloader:
    def __init__(self, config_path):
        self.parse_config(config_path)
        self.tagger = tagger()

        sess = vk_api.VkApi(token=self.token, scope=1073737727, app_id=6463690)
        self.api = sess.get_api()

        self.user_id = self.get_user_id()

        # self.start(my_pl_id)

        # if exists("songs.json"):
        #     db = self.parse_db()
        # else:
        #     db = self.update_json_db(my_pl_id, title)
        #
    def start(self, playlist_id, working_directory="", invert_position=False, download_threads=4):
        playlist_title = self.get_playlist_title(playlist_id, self.user_id)
        if not playlist_title:
            print("cant get playlist title. Strange.")
            playlist_title = "None"
        else:
            print(f"playlist_title: {playlist_title}")

        if not working_directory:
            working_directory = f"{getcwd()}/{sanitize_filename(playlist_title)}"
            if not exists(working_directory):
                mkdir(working_directory)

        if not exists(working_directory):
            print(f"folder {working_directory} is not exists.")
            exit(-1)

        self.current_playlist_id = playlist_id
        db = self.get_db(playlist_id, playlist_title, invert_position)
        try:
            asyncio.run(self.download_playlist(db, working_directory, download_threads))
        except KeyboardInterrupt:
            print("closing..")


    def parse_config(self, config_path):
        config = dict()

        with open(config_path, "r") as config_file:
            config = json.loads(config_file.read())

        if not "token" in config:
            raise Exception("there's no 'token' field in config")

        self.token = config["token"]

    def get_user_id(self):
        return self.api.users.get()[0]["id"]

    def get_db(self, pl_id, playlist_title, invert_position=False):
        zhopa = self.api.audio.get(playlist_id=pl_id)
        db = list()
        position = 0
        offset = 200
        count = 200

        while zhopa["items"] != []:
            for song in zhopa["items"]:
                song_obj = audio_obj(song)
                song_obj.title = demoji.replace(song_obj.title)
                song_obj.artist = demoji.replace(song_obj.artist)

                db.append(song_obj)
            zhopa = self.api.audio.get(playlist_id=pl_id, offset=offset, count=count)
            offset += count
        
        if invert_position:
            db.reverse()

        for song in db:
            song.position = position
            position += 1

        json_db = dict()
        json_db["title"] = playlist_title
        json_db["items"] = db

        return json_db

    def get_playlist_thumbnail_url(self, playlist_id):
        pls = self.api.audio.getPlaylists(owner_id=self.user_id)["items"]

        for playlist in pls:
            if playlist["id"] == playlist_id:
                return playlist["photo"]["photo_1200"]

    def get_playlists(self):
        pls = self.api.audio.getPlaylists(owner_id=self.user_id, count=100)
        print("".join([f"{item['id']} - {item['title']}\n" for item in pls["items"]]))

    def get_playlist_title(self, plid, owner_id):
        pls = self.api.audio.getPlaylists(owner_id=owner_id)
        for item in pls["items"]:
            if item["id"] == int(plid):
                return item["title"]

    async def download_thumbnail(self, path, session):
        thumbnaill_path = f"{path}/cover.jpg"
        try:
            async with session.get(self.get_playlist_thumbnail_url(self.current_playlist_id)) as response:
                async with aiofiles.open(thumbnaill_path, "wb") as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break;
                        await f.write(chunk)
                    print(f"cover downloaded, {thumbnaill_path}")
        except Exception as e:
            print("there's an error, while attempting to download playlists thumbnail.")
            print(e)
            if exists(thumbnaill_path):
                remove(thumbnaill_path)


    def parse_db(self):
        content = dict()

        with open("songs.json", "r", encoding="utf8") as songs_json:
            # content = json.loads(songs_json.read(), object_hook=lambda d: audio_obj(d, restore_obj=True))
            content = json.loads(songs_json.read())

        dick = [audio_obj(item, restore_obj=True) for item in content["items"]]
        content["items"] = dick

        return content

    async def download_playlist(self, db, working_directory, thread_count=4):
        """if working directory is empty, using cwd/playlist_title"""
        semaphore = asyncio.Semaphore(thread_count)
        new_db = list()

        for song in db["items"]:
            fn = f"{working_directory}/{song.generate_file_name()}"
            if exists(fn):
                print(f"{fn} exists")
            else:
                new_db.append(song)
            
        db = new_db

        try:
            async with aiohttp.ClientSession() as session:
                if not exists(f"{working_directory}/cover.jpg"):
                    asyncio.create_task(self.download_thumbnail(working_directory, session))
                tasks = [self.download_song(session, song.url, f"{working_directory}/{song.generate_file_name()}", semaphore, song) for song in db]
                await asyncio.gather(*tasks)
        finally:
            semaphore.release()

    async def download_song(self, session, url, path, semaphore, song):
        try:
            async with semaphore:
                print(f"downloading '{path}'...")
                try:
                    async with session.get(url) as response:
                        async with aiofiles.open(path, "wb") as f:
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break;
                                await f.write(chunk)
                            print(f"{path} is done, tagging now..")
                            asyncio.create_task(self.handle_tagging(path, song))
                except aiohttp.ClientConnectionError:
                    print(f"{path} is failed, client connection error.")
                    await self.handle_error(session, url, path, semaphore)
                except asyncio.exceptions.TimeoutError:
                    print(f"{path} is failed, timeout. retrying..")
                    await self.handle_error(session, url, path, semaphore)
                except asyncio.exceptions.CancelledError:
                    print('removing ', path)
                    if exists(path):
                        remove(path)
                except Exception as e:
                    print("some exception, just deleting file if it exists..\n", str(e))
                    if exists(path):
                        remove(path)
        except asyncio.exceptions.CancelledError as e:
            pass

    async def handle_tagging(self, path, song):
        try:
            self.tagger.process(path, song)
            print(f"{path} is tagged successfully")
        except Exception as e:
            print(f"received an error, while working at '{path}', skipping.\n", e)

    async def handle_error(self, session, url, path, semaphore):
        async with semaphore:
            print(f"trying to download '{path}' again...")
            try:
                async with session.get(url) as response:
                    async with aiofiles.open(path, "wb") as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break;
                            await f.write(chunk)
                        print(f"{path} is done")
            except Exception as e:
                print(str(e))
                if exists(path):
                    remove(path)

