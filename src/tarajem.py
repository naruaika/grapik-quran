# tarajem.py
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
from tempfile import TemporaryFile
from threading import Thread
from typing import List
from urllib.request import urlopen

from . import globals as glo
from .animation import Animation
from .constants import RESOURCE_PATH
from .model import Metadata
from .model import Tarajem


@Gtk.Template(resource_path=f'{RESOURCE_PATH}/ui/tarajem_viewer.ui')
class TarajemViewer(Gtk.Overlay):
    __gtype_name__ = 'TarajemViewer'

    scrolledwindow = Gtk.Template.Child('scrolledwindow')
    listbox = Gtk.Template.Child('listbox')

    def populate(
            self,
            bboxes: List,
            bboxes_hovered: List,
            bboxes_focused: List,
            regenerate: bool) -> bool:
        uniques = set()  # for removing duplicate surah-ayah pairs
        bboxes = [bbox[:2] for bbox in bboxes]
        bboxes = [bbox for bbox in bboxes
                  if not (bbox in uniques or uniques.add(bbox))]

        if bboxes_focused:
            bboxes_focused = bboxes_focused[0][:2]  # get surah-ayah numbers
                                                    # only
        if bboxes_hovered:
            bboxes_hovered = bboxes_hovered[0][:2]

        if regenerate:
            # Reset the display
            def reset(row: Gtk.ListBoxRow) -> None:
                self.listbox.remove(row)
            self.listbox.foreach(reset)

        with Metadata() as metadata, \
             Tarajem() as model:
            row_focused = None
            row_hovered = None
            for idx_bbox, bbox in enumerate(bboxes):
                if regenerate:
                    label = Gtk.Label(
                        label=f'{metadata.get_surah_name(bbox[0])} '
                            f'({bbox[0]}) : {bbox[1]}', xalign=0)
                    label.set_can_focus(False)

                    hbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    hbox.set_can_focus(False)
                    hbox.pack_start(label, True, True, 0)

                    for tid in glo.tarajem_names:
                        textview = Gtk.TextView()
                        textview.set_editable(False)
                        textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
                        textview.set_can_focus(False)
                        textview.set_hexpand(True)
                        tarajem = metadata.get_tarajem(tid)
                        translator = tarajem[1]
                        language = tarajem[2].title()
                        markup = \
                            '<span foreground="#444444" size="small">' \
                                f'{language} - {translator}' \
                            '</span>\n' \
                            '<span>' \
                                f'{model.get_tarajem_text(tid, *bbox)[2]}' \
                            '</span>'
                        buffer = Gtk.TextBuffer()
                        buffer.insert_markup(
                            buffer.get_start_iter(), markup, -1)
                        textview.set_buffer(buffer)
                        hbox.pack_start(textview, True, True, 1)

                    row = Gtk.ListBoxRow()
                    row.set_can_focus(False)
                    row.add(hbox)
                    self.listbox.add(row)

                row = self.listbox.get_row_at_index(idx_bbox)
                if bbox == bboxes_focused:
                    row_focused = row
                    row.set_name('row-focused')
                elif bbox == bboxes_hovered:
                    row_hovered = row
                    row.set_name('row-hovered')
                else:
                    row.set_name('row')

        self.listbox.show_all()

        # Add a delay to make sure all the listboxrow has been rendered
        # and then animate the scroll
        # FIXME: find better solution to make sure all its children are ready
        if bboxes_focused:
            GLib.timeout_add(50, Animation.scroll_to, self.scrolledwindow,
                             row_hovered if row_hovered else row_focused)

        if self.listbox.get_children():
            return True
        return False


@Gtk.Template(resource_path=f'{RESOURCE_PATH}/ui/tarajem_popover.ui')
class TarajemPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'TarajemPopover'

    __gsignals__ = {
        'tarajem-names-updated': (GObject.SIGNAL_RUN_FIRST, None, ())}

    entry = Gtk.Template.Child('entry')
    listbox = Gtk.Template.Child('listbox')
    progressbar = Gtk.Template.Child('progressbar')
    scrolledwindow = Gtk.Template.Child('scrolledwindow')

    # Optimizers
    tarajem_name: str = ''  # to avoid downloading another tarajem while
                            # downloading a tarajem
    tarajems: List = []  # to store the search results

    def populate(
            self,
            query: str = '') -> bool:
        """Populate a list of all available tarajem/tafaser

        Contains metadata of all supported tarajem/tafaser to be downloaded and
        opened, the data is retrieved from the SQLite database. Returns True if
        the list is successfully generated, otherwise False. It should always
        returns True if the installation of application has done smoothly.
        """
        with Metadata() as metadata, \
             Tarajem() as model:
            if query:
                # Filter tarajem list based on a query from user
                tarajems = []
                query = query.lower()
                for tarajem in metadata.get_tarajems():
                    if query in tarajem[1].lower() \
                            or query in tarajem[2]:
                        tarajems.append(tarajem)

                # Compare to the previous displayed list
                # if they are the same, do not update the display.
                # Otherwise, save current filtered list.
                if self.tarajems == tarajems:
                    return
                self.tarajems = tarajems
            else:
                self.tarajems = metadata.get_tarajems()

            # Reset the display
            def reset(row: Gtk.ListBoxRow) -> None:
                self.listbox.remove(row)
            self.listbox.foreach(reset)

            for tarajem in self.tarajems:
                label = f'<b>{tarajem[2].title()}</b> - {tarajem[1]}'
                row = TarajemListBoxRow(label)

                row.id = tarajem[0]
                row.is_downloaded = model.is_tarajem_exist(row.id)

                if row.is_downloaded:
                    icon_name = 'object-select-symbolic'
                else:
                    icon_name = 'folder-download-symbolic'
                row.icon_status.set_from_icon_name(icon_name,
                                                   Gtk.IconSize.BUTTON)

                if not row.is_downloaded \
                        or row.id in glo.tarajem_names:
                    row.icon_status.set_opacity(1)
                else:
                    row.icon_status.set_opacity(0)

                self.listbox.add(row)

        self.listbox.show_all()

        if self.listbox.get_children():
            return True
        return False

    @Gtk.Template.Callback()
    def search(
            self,
            entry: Gtk.SearchEntry) -> None:
        query = entry.get_text()
        self.populate(query)

    @Gtk.Template.Callback()
    def select(
            self,
            listbox: Gtk.ListBox,
            listboxrow: Gtk.ListBoxRow) -> None:
        if not listboxrow:
            return

        if not listboxrow.is_downloaded:
            self.download(listboxrow)
            return

        listboxrow.icon_status.set_opacity(
            not listboxrow.id in glo.tarajem_names)

        if listboxrow.id in glo.tarajem_names:
            glo.tarajem_names.remove(listboxrow.id)
        else:
            glo.tarajem_names.append(listboxrow.id)
        self.emit('tarajem-names-updated')

    def download(
            self,
            row: Gtk.ListBoxRow) -> None:
        """Download selected tarajem from the internet

        Data related to the selected tarajem will be downloaded from the URL
        stored in the SQLite database and then will be placed in a new created
        table.
        """
        if self.tarajem_name:
            return
        tarajem_id = row.id
        self.tarajem_name = tarajem_id

        row.icon_status.hide()
        row.spinner.start()
        row.spinner.show()

        def is_downloaded() -> bool:
            with Metadata() as metadata, \
                 Tarajem() as model:
                tarajem = metadata.get_tarajem(tarajem_id)
                if not tarajem:
                    return False

                # Open connection and look for content length in its header
                response = urlopen(tarajem[-1])
                total_length = response.getheader('Content-Length')
                total_length = (0 if not total_length else int(total_length))

                downloaded_length = 0
                chunk_size = 1024

                # Download SQL query file
                with TemporaryFile() as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        downloaded_length += len(chunk)
                        if total_length:
                            self.progressbar.set_fraction(
                                downloaded_length / total_length)
                        f.write(chunk)

                    f.seek(0)
                    query = \
                        f'''CREATE TABLE {tarajem_id} (
                            id   INT(4) PRIMARY KEY
                                        NOT NULL,
                            sura INT(3) NOT NULL,
                            aya  INT(3) NOT NULL,
                            text TEXT   NOT NULL
                        );'''
                    model.cursor.execute(query)
                    model.cursor.execute('PRAGMA encoding="UTF-8";')
                    model.cursor.executescript(
                        '\n'.join(f.read().decode('utf-8')
                                  .replace('index', 'id')
                                  .replace(r"\'),", "'),").replace(r"\'", "''")
                                  .split('\n')[46:]))
                    model.connection.commit()

            self.progressbar.set_fraction(1)  # in case there is no content
                                              # length in its header

            return True

        def execute() -> None:
            self.progressbar.show()

            if is_downloaded():
                row.is_downloaded = True
                row.icon_status.set_from_icon_name(
                    'object-select-symbolic', Gtk.IconSize.BUTTON)
                row.icon_status.set_opacity(0)

            row.spinner.hide()
            row.spinner.stop()
            row.icon_status.show()
            self.progressbar.hide()
            self.progressbar.set_fraction(0)
            self.tarajem_name = ''

            Animation.scroll_to(self.scrolledwindow, row, 200)

        Thread(target=execute).start()


@Gtk.Template(resource_path=f'{RESOURCE_PATH}/ui/tarajem_listboxrow.ui')
class TarajemListBoxRow(Gtk.ListBoxRow):
    __gtype_name__ = 'TarajemListBoxRow'

    icon_status = Gtk.Template.Child('icon_status')
    spinner = Gtk.Template.Child('spinner')
    label = Gtk.Template.Child('label')

    def __init__(
            self,
            label: str,
            **kwargs) -> None:
        super().__init__(**kwargs)

        self.label.set_markup(label)

        self.icon_status.set_no_show_all(True)
        self.spinner.set_no_show_all(True)
