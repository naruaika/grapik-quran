# telaawa.py
#
# Copyright 2021 Naufan Rusyda Faikar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from enum import Enum
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gst
from io import BytesIO
from os import makedirs
from os import path
from shutil import copyfileobj
from tempfile import TemporaryFile
from threading import Thread
from typing import List
from urllib.request import urlopen
from zipfile import ZipFile

from . import constants as const
from . import globals as glob
from .animation import Animation
from .model import Metadata


class TelaawaPlayer(Enum):
    STOP = 0
    PLAY = 1
    PAUSE = 2
    RESUME = 3


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/telaawa_popover.ui')
class TelaawaPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'TelaawaPopover'

    __gsignals__ = {
        'telaawa-playback': (GObject.SIGNAL_RUN_CLEANUP, None, (bool,)),
        'go-to-previous-ayah': (GObject.SIGNAL_RUN_CLEANUP, None, ()),
        'go-to-next-ayah': (GObject.SIGNAL_RUN_CLEANUP, None, ())}

    Gst.init()

    entry = Gtk.Template.Child()
    list_qaree = Gtk.Template.Child()
    list_surah = Gtk.Template.Child()
    progress_qaree = Gtk.Template.Child()
    progress_surah = Gtk.Template.Child()
    scrolledwindow_qaree = Gtk.Template.Child()
    scrolledwindow_surah = Gtk.Template.Child()

    button_seek_backward = Gtk.Template.Child()
    button_toggle_playback = Gtk.Template.Child()
    icon_toggle_playback = Gtk.Template.Child()
    button_seek_forward = Gtk.Template.Child()
    slider_playback = Gtk.Template.Child()
    button_toggle_loopback = Gtk.Template.Child()
    icon_toggle_loopback = Gtk.Template.Child()

    playbin: Gst.Element = None
    playbin_state: TelaawaPlayer = None
    playbin_seeker: int = None
    ready_to_play: bool = False

    # Optimizers
    is_updating: bool = False  # to prevent unwanted widget triggering
    telaawa_name: str = ''  # store a being downloaded telaawa ID to prevent
                            # from downloading another telaawa when the current
                            # download is not finished
    telaawas: List = []  # store the search results to avoid unneeded
                         # refreshment of Qaree list

    def __init__(
            self,
            **kwargs) -> None:
        super().__init__(**kwargs)

        self.playbin = Gst.ElementFactory.make('playbin', 'playbin')
        self.playbin_state = TelaawaPlayer.STOP

        self.button_toggle_loopback.props.active = glob.playback_loop

    def populate(
            self,
            query: str = '') -> bool:
        """Populate a list of all available telaawas

        Contains metadata of all supported telaawas to be downloaded and listen
        to, the data is retrieved from the SQLite database. Returns True if the
        telaawas list is successfully generated, otherwise False. It should
        always returns True if the installation of application has done
        smoothly."""
        with Metadata() as metadata:
            if query:
                # Filter telaawa list based on a query from user
                telaawas = []
                query = query.lower()
                for telaawa in metadata.get_telaawas():
                    if query in telaawa[1].lower() \
                            or query in telaawa[3] \
                            or query in telaawa[3]:
                        telaawas.append(telaawa)

                # Compare to the previous displayed list
                # if they are the same, do not update the display
                # otherwise, save current filtered list
                if self.telaawas == telaawas:
                    return
                self.telaawas = telaawas
            else:
                self.telaawas = metadata.get_telaawas()

            # Reset the display
            def reset(row: Gtk.ListBoxRow) -> None:
                self.list_qaree.remove(row)
            self.list_qaree.foreach(reset)

            for telaawa in self.telaawas:
                name = \
                    '<span weight="bold">' \
                        f'{telaawa[1]}' \
                    '</span>'
                description = \
                    '<span size="small">' \
                        f"Qira\'at: {telaawa[3].title()} - " \
                        f'Style: {telaawa[5].title()} - ' \
                        f'Bitrate: {telaawa[4]}Kbps' \
                    '</span>'
                row = TelaawaListBoxRow(name, description)

                row.id = telaawa[0]

                if row.id == glob.telaawa_name:
                    self.list_qaree.select_row(row)
                else:
                    row.icon_status.set_opacity(0)

                self.list_qaree.add(row)

        self.list_qaree.show_all()

        if self.list_qaree.get_children():
            return True
        return False

    @Gtk.Template.Callback()
    def search(
            self,
            entry: Gtk.SearchEntry) -> None:
        query = entry.get_text()
        self.populate(query)

    @Gtk.Template.Callback()
    def on_qaree_selected(
            self,
            listbox: Gtk.ListBox,
            listboxrow: Gtk.ListBoxRow) -> None:
        if not listboxrow:
            return

        if glob.telaawa_name == listboxrow.id:
            return
        glob.telaawa_name = listboxrow.id

        # Reset the display
        def reset(listboxrow: Gtk.ListBoxRow) -> None:
            listboxrow.icon_status.set_opacity(0)
        listbox.foreach(reset)

        listboxrow.icon_status.set_opacity(1)

        # Interrupt the telaawa playback if it is playing
        if self.ready_to_play:
            self.playback(TelaawaPlayer.PLAY)

    @Gtk.Template.Callback()
    def on_seek_backward(
            self,
            button: Gtk.Button) -> None:
        self.emit('go-to-previous-ayah')

    @Gtk.Template.Callback()
    def on_seek_forward(
            self,
            button: Gtk.Button) -> None:
        self.emit('go-to-next-ayah')

    @Gtk.Template.Callback()
    def on_played(
            self,
            button: Gtk.ToggleButton) -> None:
        self.ready_to_play = button.get_active()
        self.emit('telaawa-playback', self.ready_to_play)

        if self.ready_to_play:
            self.icon_toggle_playback.set_from_icon_name(
                'media-playback-pause-symbolic', Gtk.IconSize.BUTTON)
        else:
            self.icon_toggle_playback.set_from_icon_name(
                'media-playback-start-symbolic', Gtk.IconSize.BUTTON)

        if self.is_updating:
            return

        if self.ready_to_play:
            if self.playbin_state == TelaawaPlayer.STOP:
                self.playback(TelaawaPlayer.PLAY)
            else:
                self.playback(TelaawaPlayer.RESUME)
        else:
            self.playback(TelaawaPlayer.PAUSE)

    @Gtk.Template.Callback()
    def on_looped(
            self,
            button: Gtk.ToggleButton) -> None:
        glob.playback_loop = button.get_active()
        if glob.playback_loop:
            self.icon_toggle_loopback.set_from_icon_name(
                'media-playlist-repeat-symbolic', Gtk.IconSize.BUTTON)
        else:
            self.icon_toggle_loopback.set_from_icon_name(
                'media-playlist-consecutive-symbolic', Gtk.IconSize.BUTTON)

    @Gtk.Template.Callback()
    def on_seek(
            self,
            range: Gtk.Range) -> None:
        if self.is_updating:
            return

        seek_time_secs = self.slider_playback.get_value()
        self.playbin.seek_simple(Gst.Format.TIME,
                                 Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                 seek_time_secs * Gst.SECOND)

    @Gtk.Template.Callback()
    def on_shown(
            self,
            widget: Gtk.Widget) -> None:
        selected_row = self.list_qaree.get_selected_row()
        if not selected_row:
            return

        # Scroll to the selected row, since Gtk has no idea how to set the
        # scrolling before the widget is rendered
        GLib.timeout_add(50, Animation.scroll_to, self.scrolledwindow_qaree,
                         selected_row, 200)

    def playback(
            self,
            state: TelaawaPlayer) -> None:
        self.playbin_state = state

        if state == TelaawaPlayer.PAUSE:
            self.playbin.set_state(Gst.State.PAUSED)

            self.is_updating = True
            self.button_toggle_playback.set_active(False)
            self.is_updating = False

        elif state == TelaawaPlayer.RESUME:
            self.playbin.set_state(Gst.State.PLAYING)

        elif state == TelaawaPlayer.STOP:
            self.ready_to_play = False
            self.playbin.set_state(Gst.State.READY)

            self.is_updating = True
            self.button_toggle_playback.set_active(False)
            self.is_updating = False

        else:
            self.playbin.set_state(Gst.State.NULL)  # reset the playback first

            telaawa_filepath = path.join(
                const.USER_DATA_PATH, f'telaawa/{glob.telaawa_name}')
            suraya_no = f'{glob.surah_number:03d}{glob.ayah_number:03d}'

            def play() -> None:
                # Check if the audio to play is already downloaded
                if not path.isfile(f'{telaawa_filepath}/{suraya_no}.mp3'):
                    is_downloaded = self.download()
                    # Check if the download was successful and the user still
                    # wants to play the telaawa
                    if not is_downloaded \
                            or self.playbin_state != TelaawaPlayer.PLAY:
                        GLib.idle_add(self.playback, TelaawaPlayer.STOP)
                        return

                self.playbin.set_property(
                    'uri', f'file://{telaawa_filepath}/{suraya_no}.mp3')
                self.playbin.set_state(Gst.State.PLAYING)

                if not self.playbin_seeker:
                    # Update the playback slider every 0.2 second
                    self.playbin_seeker = GLib.timeout_add(200, self.seek)

                message = self.playbin.get_bus().timed_pop_filtered(
                    Gst.CLOCK_TIME_NONE,
                    Gst.MessageType.ERROR | Gst.MessageType.EOS)

                self.is_updating = True
                self.slider_playback.set_value(0)
                self.is_updating = False

                if message.type == Gst.MessageType.EOS:
                    self.playbin.set_state(Gst.State.READY)
                    GLib.idle_add(self.emit, 'go-to-next-ayah')
                else:
                    self.playbin.set_state(Gst.State.NULL)

            Thread(target=play, daemon=True).start()

    def seek(self) -> bool:
        if self.playbin_state == TelaawaPlayer.STOP:
            GLib.source_remove(self.playbin_seeker)
            self.playbin_seeker = None
            return False
        if self.playbin_state == TelaawaPlayer.PAUSE:
            return True

        is_fetched, duration = self.playbin.query_duration(Gst.Format.TIME)
        if not is_fetched:
            return True
        self.slider_playback.set_range(0, duration / Gst.SECOND)

        is_fetched, position = self.playbin.query_position(Gst.Format.TIME)
        if not is_fetched:
            return True

        self.is_updating = True
        self.slider_playback.set_value(position / Gst.SECOND)
        self.is_updating = False

        return True

    def download(self) -> bool:
        """Download the selected telaawa for current surah from the internet

        Data related to the selected telaawa will be downloaded from the URL
        stored in the SQLite database and then will be placed in the user data
        directory.
        """
        if self.telaawa_name:
            return
        self.telaawa_name = glob.telaawa_name

        # FIXME: lock all the listboxrows from being selectable while
        # downloading
        row = self.list_qaree.get_selected_row()
        row.icon_status.hide()
        row.spinner.start()
        row.spinner.show()
        self.progress_qaree.show()

        def close() -> None:
            row.spinner.hide()
            row.spinner.stop()
            row.icon_status.show()
            self.progress_qaree.hide()
            self.progress_qaree.set_fraction(0)
            self.telaawa_name = ''

            GLib.timeout_add(50, Animation.scroll_to, self.scrolledwindow_qaree,
                            row, 100)

        with Metadata() as metadata:
            telaawa = metadata.get_telaawa(self.telaawa_name)
            if not telaawa:
                print(f'The telaawa ID `{self.telaawa_name}` is no longer '
                      'valid. Make sure you have downloaded the latest version'
                      f' of {const.APPLICATION_NAME}. Please contact the '
                      'developers to get a help.')
                close()
                return False

            # Open network connection
            fileurl = telaawa[2].replace('http', 'https') \
                + f'{glob.surah_number:03d}.zip'
            try:
                response = urlopen(fileurl)
            except:
                print(f'The file for the telaawa ID `{self.telaawa_name}` is '
                      'no longer available to be downloaded. Please contact '
                      'the developers to get a help.')
                close()
                return False

            # Look for content length in its header
            total_length = response.getheader('Content-Length')
            total_length = (0 if not total_length else int(total_length))

            downloaded_length = 0
            chunk_size = 1024

            # Download archive file
            with TemporaryFile() as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    downloaded_length += len(chunk)
                    if total_length:
                        self.progress_qaree.set_fraction(
                            downloaded_length / total_length)
                    f.write(chunk)

                # Extract the archive file
                f.seek(0)
                with ZipFile(BytesIO(f.read()), 'r') as fz:
                    telaawa_dir = path.join(const.USER_DATA_PATH,
                                            f'telaawa/{glob.telaawa_name}')
                    makedirs(telaawa_dir, exist_ok=True)
                    for filename in fz.namelist():
                        image = fz.open(filename)
                        filepath = path.join(
                            telaawa_dir, path.basename(filename))
                        with open(filepath, 'wb') as fi:
                            copyfileobj(image, fi)

        self.progress_qaree.set_fraction(1)  # in case there is no content
                                             # length in its header

        close()

        return True


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/telaawa_listboxrow.ui')
class TelaawaListBoxRow(Gtk.ListBoxRow):
    __gtype_name__ = 'TelaawaListBoxRow'

    icon_status = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    label_name = Gtk.Template.Child()
    label_description = Gtk.Template.Child()
    button_open_settings = Gtk.Template.Child()

    def __init__(
            self,
            name: str,
            description: str,
            **kwargs) -> None:
        super().__init__(**kwargs)

        self.label_name.set_markup(name)
        self.label_description.set_markup(description)

        self.icon_status.set_no_show_all(True)
        self.spinner.set_no_show_all(True)
