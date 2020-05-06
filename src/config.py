import os.path
import configparser
import utils

series_root_path = ""
movies_root_path = ""
ffmpeg_path = ""
ffprobe_path = ""
zscale_available = False


def load_settings():
    global series_root_path, movies_root_path, ffmpeg_path, ffprobe_path, zscale_available
    config = configparser.ConfigParser()
    config_path = os.path.join(utils.get_base_folder(), "config.ini")
    config.read(config_path)
    settings = config["Settings"]
    series_root_path = settings["SeriesRootPath"]
    movies_root_path = settings["MoviesRootPath"]
    ffmpeg_path = settings["ffmpegPath"]
    ffprobe_path = settings["ffprobePath"]
    zscale_available = (settings["zscaleAvailable"] == "True")


load_settings()
