import pprint
import re
from typing import Any, Union, cast

import yt_dlp
from sortedcontainers import SortedDict

url = "https://www.youtube.com/watch?v=5_LOB-_WhJI"


def convert_timestamp_to_seconds(timestamp_list: list[str]) -> int:
    print(timestamp_list)
    int_timestamp_list = list(map(int, timestamp_list))
    if len(timestamp_list) == 2:
        return int_timestamp_list[0] * 60 + int_timestamp_list[1]
    else:
        return (
            int_timestamp_list[0] * 60 * 60
            + int_timestamp_list[1] * 60
            + int_timestamp_list[2]
        )


timestamp_regex = r"(?:^|\s*>?\s?\[?)((?:\d{1,2}:)?\d{1,2}:\d{2})\]?\s?(.*?)(?=(?:(?:\d{1,2}:)?\d{1,2}:\d{2})|$)"

sorted_comments = SortedDict()


def add_original_video_capters(original_chapters: list[dict[str, Union[str, int]]]):
    if original_chapters:
        for chapter in original_chapters:
            sorted_comments[chapter["start_time"]] = chapter["title"]


def add_to_sorted_comments_dict(timestamp_in_sec: int, comment_text: str):
    print("added comment")
    for i in range(timestamp_in_sec, timestamp_in_sec + 16):
        if i in sorted_comments:
            return
    sorted_comments[timestamp_in_sec] = comment_text


def get_ffmpeg_compatible_chapter_list(
    comments_dict: SortedDict,
) -> list[dict[str, Union[int, str]]]:
    comments_list = []

    temp_comments_list = list(comments_dict)
    for index, timestamp in enumerate(temp_comments_list):
        end_time = (
            temp_comments_list[index + 1]
            if index + 1 < len(temp_comments_list)
            else duration
        )
        comments_list.append(
            {
                "start_time": timestamp,
                "title": comments_dict[timestamp],
                "end_time": end_time,
            }
        )
    return comments_list


ytdl_metadata = yt_dlp.YoutubeDL(
    {
        "getcomments": True,
        "extractor_args": {
            "youtube": {
                "max_comments": "3000",
                "max_comment_depth": "2",
                "comment_sort": "top",
            }
        },
        "skip_download": True,
    }
)
pp = pprint.PrettyPrinter(indent=4, width=178, sort_dicts=False)

info_dict = cast(dict[str, Any], ytdl_metadata.extract_info(url))

comments = info_dict["comments"]
duration = info_dict["duration"]
if "chapters" in info_dict and info_dict["chapters"]:
    original_chapters = info_dict["chapters"]
    add_original_video_capters(original_chapters)

pp.pprint(comments)
if comments:
    for comment in comments:
        comment_text = comment["text"]
        matches = re.finditer(timestamp_regex, comment_text, re.MULTILINE)
        for match in matches:
            timestamp_list = match.group(1).split(":")
            timestamp_in_sec = convert_timestamp_to_seconds(timestamp_list)
            comment_text = match.group(2)
            add_to_sorted_comments_dict(timestamp_in_sec, comment_text)

comments_list = get_ffmpeg_compatible_chapter_list(sorted_comments)
info_dict["chapters"] = comments_list

ytdl_downloader = yt_dlp.YoutubeDL(
    {
        "merge_output_format": "mp4",
        "embedsubtitles": True
    }
)

pp.pprint(info_dict)
