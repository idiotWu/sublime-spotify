# encoding: utf-8
from __future__ import unicode_literals

import sublime
import random
import time

sublime3 = int(sublime.version()) >= 3000
if sublime3:
    set_timeout_async = sublime.set_timeout_async
else:
    set_timeout_async = sublime.set_timeout

class MusicPlayerStatusUpdater():
    def __init__(self, player):
        self.player = player

        s = sublime.load_settings("Spotify.sublime-settings")
        self.display_duration = int(s.get("status_duration"))
        self.status_format = s.get("status_format")

        self._curr_pos = None
        self._cached_song = None
        self._cached_artist = None
        self._cached_album = None
        self._cached_duration = None

        self._update_delay = int(s.get("polling"))
        self._cycles_left = self.display_duration * 1000 // self._update_delay

        self.bars = ["▁","▂","▄","▅"]

        self._is_displaying = False
        if self.display_duration < 0: self.run()

    def _get_min_sec_string(self,seconds):
        m = seconds//60
        s = seconds - 60*m
        return "%d:%.02d" % (m,s)

    def _refresh_cache(self):
        # Simple caching. Relies on the odds of two consecutive
        # songs having the same title being very low.
        # Should limit scripting calls.
        curr_song = self.player.get_song()
        if self._cached_song != curr_song:
            print("refreshed")
            self._cached_song = curr_song
            self._cached_artist = self.player.get_artist()
            self._cached_album = self.player.get_album()
            self._cached_duration_secs = self.player.get_duration()
            self._cached_duration = self._get_min_sec_string(self._cached_duration_secs)

    def _refresh_pos(self):
        if self.player.is_paused() and self._curr_pos:
            return self._curr_pos

        self._refresh_cache()
        self._curr_pos = self._get_min_sec_string(self.player.get_position())

    def _get_message(self):
        if self.player.is_playing():
            icon = "▶"
            random.shuffle(self.bars)
        else:
            icon = "||"

        self._refresh_pos()

        if self._cached_duration_secs >= 29 and self._cached_duration_secs <= 31:
            return "Spotify Advertisement"

        return self.status_format.format(
            equalizer="".join(self.bars),
            icon=icon,
            time=self._curr_pos,
            duration=self._cached_duration,
            song=self._cached_song,
            artist=self._cached_artist,
            album=self._cached_album)

    def run(self):
        if not self._is_displaying:
            self._is_displaying = True
            self._run()

    def _run(self):
        start = time.time()

        if self._cycles_left == 0:
            sublime.status_message("")
            self._cycles_left = self.display_duration * 1000 / self._update_delay
            self._is_displaying = False
            return
        elif self._cycles_left > 0:
            self._cycles_left -= 1

        if self.player.is_running():
            sublime.status_message(self._get_message())
        else:
            self._is_displaying = False

        end = time.time()
        duration = (end - start) * 1000
        delay = max(100, self._update_delay - duration)
        set_timeout_async(lambda: self._run(), delay)
