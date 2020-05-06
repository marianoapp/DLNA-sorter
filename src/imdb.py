import os.path
import re
import json
import json_utils
import config

cache_path = os.path.join(config.series_root_path, "imdb_cache.json")
cache_data = {}
is_dirty = False


def read_cache():
    global cache_data
    if cache_data == {}:
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding='utf-8') as read_file:
                cache_data = json.load(read_file)
        else:
            cache_data = {"series": []}


def write_cache():
    if is_dirty:
        with open(cache_path, "w", encoding='utf-8') as write_file:
            json.dump(cache_data, write_file, indent=4)
        set_dirty(False)


def set_dirty(dirty_flag):
    global is_dirty
    is_dirty = dirty_flag


def create_series_node(imdb_id, title):
    return {"id": imdb_id, "title": title, "seasons": []}


def create_season_node(season_number):
    return {"number": season_number, "episodes": []}


def create_episode_node(episode_number, title):
    return {"number": episode_number, "title": title}


def append_series_node(series_node):
    series_root = cache_data["series"]
    if series_root is not None:
        series_root.append(series_node)
        set_dirty(True)


def append_season_node(series_node, season_node):
    series_node["seasons"].append(season_node)
    set_dirty(True)


def append_episode_node(season_node, episode_node):
    season_node["episodes"].append(episode_node)
    set_dirty(True)


def get_series_node(series):
    data_path = str.format("series[title='{0}']", series)
    series_node = json_utils.get_json_path(cache_data, data_path)
    # if there's no series data then fill the cache from imdb
    if not series_node:
        imdb_id = get_series_imdb_id(series)
        if imdb_id:
            series_node = create_series_node(imdb_id, series)
            append_series_node(series_node)
    return series_node


def get_season_node(series_node, season_number):
    data_path = str.format("seasons[number='{0}']", season_number)
    season_node = json_utils.get_json_path(series_node, data_path)
    # if there's no season data then fill the cache from imdb
    if not season_node:
        episode_list = get_season_episodes_imdb(series_node["id"], season_number)
        if episode_list:
            season_node = create_season_node(season_number)
            append_season_node(series_node, season_node)
            for number, title in enumerate(episode_list, start=1):
                episode_node = create_episode_node(number, title)
                append_episode_node(season_node, episode_node)
    return season_node


def get_series_imdb_id(series):
    # get the imdb id from the series title
    keys = ["f", "t", "u"]
    for key in keys:
        search_link = str.format("https://v2.sg.media-imdb.com/suggestion/{0}/{1}.json",
                                 key, series.lower().replace(" ", "_"))
        search_data = json_utils.get_json(search_link)
        if search_data:
            imdb_id = json_utils.get_json_path(search_data, "d[0].id")
            return imdb_id


def get_season_episodes_imdb(imdb_id, season_number):
    page_link = str.format("https://www.imdb.com/title/{0}/episodes?season={1}&ref_=tt_eps_sn_{1}",
                           imdb_id, season_number)
    base_page_content = json_utils.get_content(page_link)
    try:
        page_content = base_page_content.decode('utf8')
    except:
        page_content = str(base_page_content)
    pattern = r"<a[^>]+itemprop=\"name\"[^>]*>([^>]+)</a>"
    return re.findall(pattern, page_content)


def get_episode_title(series, episode):
    title = None
    # load the cache
    read_cache()
    # get season and episode numbers
    matches = re.search(r"S(\d+)E(\d+)", episode)
    season_number = matches[1].lstrip('0')
    episode_number = matches[2].lstrip('0')
    # get title
    series_node = get_series_node(series)
    if series_node:
        season_node = get_season_node(series_node, season_number)
        if season_node:
            data_path = str.format("episodes[number='{0}'].title", episode_number)
            title = json_utils.get_json_path(season_node, data_path)
    # save the cache
    write_cache()
    return title
