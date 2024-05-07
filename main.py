import argparse
from os.path import exists
import sys
from megasuperdownloader import megasuperdownloader


if __name__ == "__main__":
    parser_help = """
    Python script, that can download playlist into tagged mp3 files.\n
    config.json syntax is pretty simple:\n\n

    {\n
        "token": "*token here*",\n
    }\n
    """
    parser = argparse.ArgumentParser( prog="VK Playlist Downloader",
        description=parser_help)
    parser.add_argument("--playlist_id", "-p", type=int, 
                        help="your playlist id here. You can check 'em using --show-playlist-ids")
    parser.add_argument("--config", "-c", default="config.json", type=str, 
                        help="path to your config where your tokens are stored.")
    parser.add_argument("--output-folder", "-o", default="", type=str, 
                        help="folder where playlist will be downloaded. By default is 'pwd/playlist_title'")
    parser.add_argument("--show-playlist-ids", "-s", action="store_true", 
                        help="you can see what playlists are avaible and get their ids.")
    parser.add_argument("--invserse_playlist", "-r", action="store_true", 
                        help="inverse playlist order")
    parser.add_argument("--download-threads", "-t", default=4, type=int, 
                        help="how many songs will be downloaded in parralel")

    args = parser.parse_args(sys.argv[1:])

    if not exists(args.config):
        print("config does not exists")
        exit(-1)

    shit = megasuperdownloader(args.config)

    if args.show_playlist_ids:
        shit.get_playlists()
        exit()

    if not args.playlist_id:
        print("playlist_id is empty. Use '--show-playlist-ids' option.")
        exit(-1)

    if args.download_threads <= 0:
        print("invalid download threads count.")
        exit()

    shit.start(args.playlist_id, args.output_folder, args.invserse_playlist,
               args.download_threads)
