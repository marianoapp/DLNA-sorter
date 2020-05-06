import os
import re
import config
from logger import logger
import thumbnails
import subtitles
import imdb


def get_series_episode_title(file_name):
    series = ""
    episode = ""
    title = ""
    general_pattern = r"(.+S\d{2}E\d{2,3}.+?)(720p|1080p|2160p|webrip|repack|hdr|proper|rerip)"
    general_matches = re.match(general_pattern, file_name, re.IGNORECASE)
    if general_matches:
        pattern = r"(.+)\.(S\d{2}E\d{2,3})\.(.+)?"
        matches = re.match(pattern, general_matches[1], re.IGNORECASE)
        if matches:
            series = matches[1].replace(".", " ").title()
            episode = matches[2].upper()
            if matches[3] is not None:
                title = matches[3].replace(".", " ").strip().title()
            else:
                title = imdb.get_episode_title(series, episode)
    return series, episode, title


def create_series_folder(series, episode):
    # create series folder
    series_path = os.path.join(config.series_root_path, series)
    if not os.path.exists(series_path):
        os.makedirs(series_path)
    # extract season number from the "S##E##" formatted episode string
    season_number = episode[1:3].lstrip("0")
    # create season folder
    season_path = os.path.join(series_path, "Season " + season_number)
    if not os.path.exists(season_path):
        os.makedirs(season_path)
    return season_path


def create_video_link(video_path, folder_path, formatted_name):
    video_extension = os.path.splitext(video_path)[1]
    video_link_path = os.path.abspath(os.path.join(folder_path, formatted_name + video_extension))
    if not os.path.lexists(video_link_path):
        os.symlink(video_path, video_link_path)
    if not os.path.exists(video_link_path):
        return ""
    return video_link_path


def check_episode_exists(season_path, formatted_name):
    # use the thumbnail existence as proxy for processed files
    thumbnail_path = thumbnails.get_thumbnail_path(season_path, formatted_name)
    if os.path.exists(thumbnail_path):
        return True
    else:
        return False


def process_series(video_path):
    video_path = os.path.abspath(video_path)
    file_name = os.path.basename(video_path)
    series, episode, title = get_series_episode_title(file_name)
    # abort the process if the name couldn't be extracted
    if not series or not episode or not title:
        return
    formatted_name = series + " - " + episode + " - " + title
    season_path = create_series_folder(series, episode)
    # abort the process if the episode already exists
    # this can happen when a torrent contains multiple episodes
    if check_episode_exists(season_path, formatted_name):
        return
    create_video_link(video_path, season_path, formatted_name)
    thumbnails.extract_thumbnail(video_path, season_path, formatted_name)
    subtitles.extract_subtitle(video_path, season_path, formatted_name)


def process_movie(video_path):
    video_path = os.path.abspath(video_path)
    file_name = os.path.basename(video_path)
    matches = re.match(r"([a-z0-9.\-]+)\.\d{4}\.", file_name, re.IGNORECASE)
    if matches:
        formatted_name = matches[1].replace(".", " ").title()
    else:
        formatted_name = os.path.splitext(file_name)[0].title()
    thumbnails.extract_thumbnail(video_path, config.movies_root_path, formatted_name)
    # TODO: extract subtitle?
    create_video_link(video_path, config.movies_root_path, formatted_name)


def validate_video_file(file_path):
    valid_extensions = [".mkv", ".mp4", ".m4v", ".avi"]
    extension = os.path.splitext(file_path)[1]
    if extension in valid_extensions:
        return [file_path, os.path.getsize(file_path)]


def get_video_files_in_path(content_path):
    if os.path.isdir(content_path):
        file_list = [os.path.join(content_path, x) for x in os.listdir(content_path)]
    else:
        file_list = [content_path]
    videos = []
    for file_path in file_list:
        video_file_info = validate_video_file(file_path)
        if video_file_info is not None:
            videos.append(video_file_info)
    return videos


def process_series_content_path(content_path):
    videos = get_video_files_in_path(content_path)
    if len(videos) > 0:
        # find all the files bigger than 200MB
        valid_video_files = [x[0] for x in videos if x[1] > 200e6]
        # process the video files
        for video_path in valid_video_files:
            process_series(video_path)


def process_movie_content_path(content_path):
    video_files = get_video_files_in_path(content_path)
    if len(video_files) > 0:
        # find the biggest file
        video_path = sorted(video_files, key=lambda vf: vf[1], reverse=True)[0][0]
        # process the video file
        process_movie(video_path)


def process(category_name, content_path):
    try:
        # validate category
        valid_categories = ["Series", "Movies"]
        if category_name not in valid_categories:
            logger.error("Invalid category: %s", category_name)
            exit(1)
        # validate path
        if not os.path.exists(content_path):
            logger.error("File does not exist: %s", content_path)
            exit(1)
        # process path
        if category_name == "Series":
            process_series_content_path(content_path)
        elif category_name == "Movies":
            process_movie_content_path(content_path)
    except:
        logger.exception("Uncaught error")

