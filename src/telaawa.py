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


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/telaawa_popover.ui')
class TelaawaPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'TelaawaPopover'

    __gsignals__ = {
        'go-to-next-ayah': (GObject.SIGNAL_RUN_LAST, None, ())}

    Gst.init()

    entry = Gtk.Template.Child()
    list_qaree = Gtk.Template.Child()
    list_surah = Gtk.Template.Child()
    progress_qaree = Gtk.Template.Child()
    progress_surah = Gtk.Template.Child()
    scrolledwindow_qaree = Gtk.Template.Child()
    scrolledwindow_surah = Gtk.Template.Child()

    button_seek_backward = Gtk.Template.Child()
    button_toggle_play = Gtk.Template.Child()
    icon_toggle_play = Gtk.Template.Child()
    button_seek_forward = Gtk.Template.Child()
    seek_audio_playback = Gtk.Template.Child()
    button_toggle_loopback = Gtk.Template.Child()

    pipeline: Gst.Element = None

    is_updating: bool = False
    is_playing: bool = False
    play_after_download: bool = False  # request to play after when the user
                                       # decides to play a telaawa while it has
                                       # not been downloaded

    # Optimizers
    telaawa_name: str = ''  # to avoid downloading another telaawa while
                            # downloading a telaawa
    telaawas: List = []  # to store the search results

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
                    if query in telaawa[1].lower() or \
                            query in telaawa[3] \
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

    @Gtk.Template.Callback()
    def on_played(
            self,
            button: Gtk.ToggleButton) -> None:
        if self.is_updating:
            return

        is_playing = button.get_active()
        self.is_playing = is_playing

        if is_playing:
            suraya_no = f'{glob.surah_number:03d}001'
            if not path.isfile(path.join(
                    const.USER_DATA_PATH,
                    f'telaawa/{glob.telaawa_name}/{suraya_no}.mp3')):
                self.play_after_download = True
                self.download()
                return

        self.play(is_playing)

    @Gtk.Template.Callback()
    def scroll_to_selected_row(
            self,
            widget: Gtk.Widget) -> None:
        # Scroll to the selected row, since Gtk has no idea how to set the
        # scrolling before the widget is rendered
        GLib.timeout_add(50, Animation.scroll_to, self.scrolledwindow_qaree,
                         self.list_qaree.get_selected_row())

    def play(
            self,
            state: bool,
            reset: bool = False) -> None:
        def free() -> None:
            self.icon_toggle_play.set_from_icon_name(
                'media-playback-start-symbolic', Gtk.IconSize.BUTTON)

            if not self.pipeline:
                return
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None

        if reset \
                or not self.is_playing:  # stop audio
            free()

        if state \
                and self.is_playing:
            icon_name = 'media-playback-pause-symbolic'

            if not self.pipeline:  # play audio
                telaawa_filepath = path.join(
                    const.USER_DATA_PATH, f'telaawa/{glob.telaawa_name}')

                def execute() -> None:
                    suraya_no = \
                        f'{glob.surah_number:03d}{glob.ayah_number:03d}'
                    # FIXME: changing to a tarajem that has not been downloaded
                    # while playing stops playback and makes a jump to the
                    # selected ayah
                    self.pipeline = Gst.parse_launch(
                        f'playbin uri=file://{telaawa_filepath}/'
                        f'{suraya_no}.mp3')

                    self.pipeline.set_state(Gst.State.PLAYING)

                    bus = self.pipeline.get_bus()
                    message = bus.timed_pop_filtered(
                        Gst.CLOCK_TIME_NONE,
                        Gst.MessageType.ERROR | Gst.MessageType.EOS)

                    free()

                    # Request to play next ayah
                    GLib.idle_add(self.emit, 'go-to-next-ayah')

                Thread(target=execute).start()
            else:  # resume audio
                self.pipeline.set_state(Gst.State.PLAYING)
        else:  # pause audio
            icon_name = 'media-playback-start-symbolic'

            self.is_updating = True
            self.button_toggle_play.set_active(False)
            self.is_updating = False

            self.is_playing = False

            if self.pipeline:
                self.pipeline.set_state(Gst.State.PAUSED)

        self.icon_toggle_play.set_from_icon_name(
            icon_name, Gtk.IconSize.BUTTON)

    def download(self) -> bool:
        """Download the selected telaawa for current surah from the internet

        Data related to the selected telaawa will be downloaded from the URL
        stored in the SQLite database and then will be placed in the user data
        directory.
        """
        if self.telaawa_name:
            return
        row = self.list_qaree.get_selected_row()
        self.telaawa_name = glob.telaawa_name

        row.icon_status.hide()
        row.spinner.start()
        row.spinner.show()

        telaawa_dir = path.join(const.USER_DATA_PATH, f'telaawa/{glob.telaawa_name}')

        def is_downloaded() -> bool:
            with Metadata() as metadata:
                telaawa = metadata.get_telaawa(self.telaawa_name)
                if not telaawa:
                    return False

                # Open connection and look for content length in its header
                filepath = telaawa[2].replace('http', 'https') \
                    + f'{glob.surah_number:03d}.zip'
                response = urlopen(filepath)
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

                    f.seek(0)
                    with ZipFile(BytesIO(f.read()), 'r') as fz:
                        makedirs(telaawa_dir, exist_ok=True)
                        for filename in fz.namelist():
                            image = fz.open(filename)
                            filepath = path.join(
                                telaawa_dir, path.basename(filename))
                            with open(filepath, 'wb') as fi:
                                copyfileobj(image, fi)

            self.progress_qaree.set_fraction(1)  # in case there is no content
                                                 # length in its header

            return True

        def execute() -> None:
            self.progress_qaree.show()

            if is_downloaded():
                if self.play_after_download:
                    self.play_after_download = False
                    GLib.idle_add(self.play, True)

            row.spinner.hide()
            row.spinner.stop()
            row.icon_status.show()
            self.progress_qaree.hide()
            self.progress_qaree.set_fraction(0)
            self.telaawa_name = ''

            Animation.scroll_to(self.scrolledwindow, row, 200)

        Thread(target=execute).start()


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
