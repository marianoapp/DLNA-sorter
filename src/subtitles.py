import os.path
import subprocess
import collections
import re
import config


def valid_file(file_path):
    return os.path.exists(file_path) and (os.path.getsize(file_path) > 0)


def get_english_subtitle_index(video_path):
    SubEntry = collections.namedtuple("SubEntry", "index, lang, size")
    parameters = [config.ffprobe_path, "-loglevel", "error", "-select_streams", "s", "-show_entries",
                  "stream=index:stream_tags=language:stream_tags=number_of_bytes-eng", "-of", "csv=p=0", video_path]
    output = subprocess.run(parameters, stdout=subprocess.PIPE, universal_newlines=True)
    if output.returncode == 0:
        # split the output into lines keeping only the lines that contain a ","
        output_lines = [x for x in output.stdout.split("\n") if "," in x]
        # split the lines into an array of fields
        line_fields = [x.split(",") for x in output_lines]
        # create a SubEntry object for every line
        subs = [SubEntry._make([int(x[0]), x[1], int(x[2])]) for x in line_fields if len(x) == 3]
        # keep only the english subtitles
        english_subs = [x for x in subs if x.lang == "eng"]
        if len(english_subs) == 0:
            return None
        elif len(english_subs) == 1:
            # if there's only one english subtitle then return it
            return english_subs[0].index
        else:
            # sort the subtitles by size in descending order
            sorted_subs = sorted(english_subs, key=lambda x: x.size, reverse=True)
            # use the biggest subtitle as reference, this one usually contains SDH info
            reference_sub = sorted_subs[0]
            # search for subtitles with a size that's an 80% or more than the reference one
            found_sub = next((x for x in sorted_subs[1:] if x.size > 0.8*reference_sub.size), None)
            # if found return it, if not return the reference one
            if found_sub is not None:
                return found_sub.index
            else:
                return reference_sub.index


def extract_subtitle(video_path, season_path, formatted_name):
    subtitle_path = os.path.join(season_path, formatted_name + ".srt")
    if valid_file(subtitle_path):
        return subtitle_path
    # try to extract an english subtitle stream
    stream_index = get_english_subtitle_index(video_path)
    if stream_index is not None:
        parameters = [config.ffmpeg_path, "-y", "-i", video_path, "-map", "0:%s" % stream_index, "-map", "-v",
                      "-map", "-a", "-c", "copy", "-loglevel", "error", subtitle_path]
        subprocess.call(parameters)
    # if that fails try to extract the first subtitle stream
    if not valid_file(subtitle_path):
        parameters = [config.ffmpeg_path, "-y", "-i", video_path, "-map", "0:s:0",
                      "-c", "copy", "-loglevel", "error", subtitle_path]
        subprocess.call(parameters)
    if valid_file(subtitle_path):
        remove_sdh(subtitle_path)
    else:
        return None
    return subtitle_path


def remove_sdh(subtitle_path):
    # open the file
    with open(subtitle_path, "r") as f:
        file_text = f.read()
    # replace CRLF with LF
    file_text = file_text.replace("\r\n", "\n")
    # regex patterns
    patterns = [[r"^-?\[.+\] *\n", r""],
                [r"^-?\[.+\n.+\]\n", r""],
                [r"\[.+\] *", r""],
                [r"^-?\(.+\) *\n", r""],
                [r"^-?\(.+\n.+\)\n", r""],
                [r"\(.+\) *", r""],
                [r"^(-)?[A-Z][A-Z0-9.,' ]+:\n", r"\1"],
                [r"^(-)?[A-Z][A-Z0-9.,' ]+: *", r"\1"],
                [r"^(-)?[A-Z][a-z0-9]+ *:\n", r"\1"],
                [r"^(-)?[A-Z][a-z0-9]+ *: *", r"\1"],
                [r"^(-)?[:\n ]+", r"\1"],
                [r" {2,}", r" "],
                [r"^ +", r""],
                [r" +$", r""],
                [r"^-+([0-9]+\n)", r"\1"],
                [r"(.\n)([0-9]+\n)", r"\1\n\2"]]
    # apply the replacements
    for p in patterns:
        file_text = re.sub(p[0], p[1], file_text, flags=re.MULTILINE)
    # save the modified text
    with open(subtitle_path, "w") as f:
        f.write(file_text)
