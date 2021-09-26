import pprint
import re
from typing import Union

from sortedcontainers import SortedDict
from yt_dlp import YoutubeDL
from yt_dlp.postprocessor import FFmpegEmbedSubtitlePP, FFmpegMetadataPP
from yt_dlp.postprocessor.common import PostProcessor

pp = pprint.PrettyPrinter(indent=4, width=178, sort_dicts=False)


class ChaptersFromTimestampsPP(PostProcessor):
    def __init__(self):
        self.timestamp_regex = r"(?:^|\s*>?\s?\[?)((?:\d{1,2}:)?\d{1,2}:\d{2})\]?\s?(.*?)(?=(?:(?:\d{1,2}:)?\d{1,2}:\d{2})|$)"
        self.sorted_comments = SortedDict()

    def convert_timestamp_to_seconds(self, timestamp_list: list[str]) -> int:
        int_timestamp_list = list(map(int, timestamp_list))
        if len(timestamp_list) == 2:
            return int_timestamp_list[0] * 60 + int_timestamp_list[1]
        else:
            return (
                int_timestamp_list[0] * 60 * 60
                + int_timestamp_list[1] * 60
                + int_timestamp_list[2]
            )

    def add_original_video_capters(
        self,
        original_chapters: list[dict[str, Union[str, int]]],
    ):
        if original_chapters:
            for chapter in original_chapters:
                self.sorted_comments[chapter["start_time"]] = chapter["title"]

    def add_to_sorted_comments_dict(self, timestamp_in_sec: int, comment_text: str):
        for i in range(timestamp_in_sec, timestamp_in_sec + 16):
            if i in self.sorted_comments:
                return
        self.sorted_comments[timestamp_in_sec] = comment_text

    def get_ffmpeg_compatible_chapter_list(
        self,
        comments_dict: SortedDict,
    ) -> list[dict[str, Union[int, str]]]:
        comments_list = []

        temp_comments_list = list(comments_dict)
        for index, timestamp in enumerate(temp_comments_list):
            end_time = (
                temp_comments_list[index + 1]
                if index + 1 < len(temp_comments_list)
                else timestamp
            )
            comments_list.append(
                {
                    "start_time": timestamp,
                    "title": comments_dict[timestamp],
                    "end_time": end_time,
                }
            )
        return comments_list

    def run(self, info_dict):
        comments = info_dict["comments"]
        if "chapters" in info_dict and info_dict["chapters"]:
            original_chapters = info_dict["chapters"]
            pp.pprint(original_chapters)
            self.add_original_video_capters(original_chapters)

        # pp.pprint(comments)
        if comments:
            for comment in comments:
                comment_text = comment["text"]
                matches = re.finditer(self.timestamp_regex, comment_text, re.MULTILINE)
                for match in matches:
                    timestamp_list = match.group(1).split(":")
                    timestamp_in_sec = self.convert_timestamp_to_seconds(timestamp_list)
                    comment_text = match.group(2)
                    comment_text = comment_text.replace("/", "")
                    comment_text = comment_text.strip()
                    self.add_to_sorted_comments_dict(timestamp_in_sec, comment_text)

        comments_list = self.get_ffmpeg_compatible_chapter_list(self.sorted_comments)
        info_dict["chapters"] = comments_list
        pp.pprint(comments_list)
        return [], info_dict


ydl_opts = {  # see YoutubeDL.py dosctring
    "writesubtitles": True,
    "writeautomaticsub": True,
    "getcomments": True,
    "merge_output_format": "mkv",
    "getcomments": True,
    "subtitleslangs": ["jpn", "ja", "en", "de"],
    "extractor_args": {
        "youtube": {
            "max_comments": ["300"],
            "max_comment_depth": ["1"],
            "comment_sort": ["top"],
        }
    },
    "format": "worstvideo+worstaudio",
}

url = "https://www.youtube.com/watch?v=yiw6_JakZFc"

with YoutubeDL(ydl_opts) as ydl:
    ydl.add_post_processor(ChaptersFromTimestampsPP())
    ydl.add_post_processor(FFmpegMetadataPP(downloader=None))
    ydl.add_post_processor(FFmpegEmbedSubtitlePP())
    ydl.download([url])
