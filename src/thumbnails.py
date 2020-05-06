import os
import subprocess
import re
import config


def get_thumbnail_path(season_path, formatted_name):
    return os.path.join(season_path, formatted_name + ".jpg")


def extract_thumbnail(video_path, season_path, formatted_name):
    thumbnail_path = get_thumbnail_path(season_path, formatted_name)
    if os.path.exists(thumbnail_path):
        return thumbnail_path
    create_thumbnail(video_path, thumbnail_path)
    return thumbnail_path


def get_video_duration(video_path):
    parameters = [config.ffprobe_path, "-loglevel", "error", "-show_entries", "format=duration",
                  "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    output = subprocess.run(parameters, stdout=subprocess.PIPE, universal_newlines=True)
    if output.returncode == 0:
        try:
            return float(output.stdout)
        except ValueError:
            return 0
    return 0


def video_is_hdr(video_path):
    parameters = [config.ffprobe_path, "-loglevel", "error", "-select_streams", "v:0", "-show_entries",
                  "stream=color_space:stream=color_transfer:stream=color_primaries",
                  "-of", "csv=p=0", video_path]
    output = subprocess.run(parameters, stdout=subprocess.PIPE, universal_newlines=True)
    if output.returncode == 0:
        c_space, c_transfer, c_primaries = output.stdout.replace("\n", "").split(",")
        if c_space == "bt2020nc" and c_transfer == "smpte2084" and c_primaries == "bt2020":
            return True
    return False


def create_thumbnail(video_path, thumbnail_path):
    filters = ["scale=(160*dar):160", "crop=out_w=160"]
    hdr_to_sdr_filters = ["zscale=t=linear:npl=100",
                          "format=gbrpf32le",
                          "zscale=p=bt709",
                          "tonemap=tonemap=hable:desat=0",
                          "zscale=t=bt709:m=bt709:r=tv",
                          "format=yuv420p"]
    # add additional filters if the video is HDR
    if config.zscale_available and video_is_hdr(video_path):
        filters.extend(hdr_to_sdr_filters)
    filter_string = ",".join(filters)
    # get the video duration to extract the thumbnail at about 25% of the runtime
    video_duration = get_video_duration(video_path)
    if video_duration > 0:
        thumbnail_time_code = str(video_duration * 0.25)
    else:
        thumbnail_time_code = "00:15:00"
    # create the thumbnail
    parameters = [config.ffmpeg_path, "-y", "-ss", thumbnail_time_code, "-i", video_path, "-vframes", "1",
                  "-vf", filter_string, "-loglevel", "error", thumbnail_path]
    subprocess.call(parameters)


def rebuild_thumbnails(base_path):
    if not os.path.exists(base_path):
        return
    rx = re.compile(r'\.(mkv|mp4)')
    r = []
    for path, dnames, fnames in os.walk(base_path):
        r.extend([os.path.join(path, x) for x in fnames if rx.search(x)])
    for video_path in r:
        thumbnail_path = os.path.splitext(video_path)[0] + "_new.jpg"
        create_thumbnail(video_path, thumbnail_path)
