# search.py
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

from gi.repository import Gtk
from gi.repository import GObject
from typing import List

from . import constants as const
from .model import Metadata

@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/search_popover.ui')
class SearchPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'SearchPopover'

    __gsignals__ = {
        'go-to-suraya': (GObject.SIGNAL_RUN_LAST, None, (int, int))}

    entry = Gtk.Template.Child()
    listbox = Gtk.Template.Child()
    progressbar = Gtk.Template.Child()
    scrolledwindow = Gtk.Template.Child()

    results: List = []  # store the search results to avoid unneeded
                        # refreshment of search results

    def populate(
            self,
            query: str) -> bool:
        """Display search results

        Search everything including Musshaf unicode texts and tarajem/tafaser
        based on the user's search query. The search query should contain at
        least three characters.
        """
        if len(query) < 3:
            return

        with Metadata() as metadata:
            query = query.lower()
            results = metadata.get_ayah_texts(query)

            # Compare to the previous displayed list. If they are the same,
            # do not update the display. Otherwise, save current list.
            if self.results == results:
                return
            self.results = results

            # Reset the display
            def reset(row: Gtk.ListBoxRow) -> None:
                self.listbox.remove(row)
            self.listbox.foreach(reset)

            for result in self.results:
                text = \
                    '<span>' \
                        f'{result[-1]}' \
                    '</span>'
                label =  \
                    '<span size="small">' \
                        f'Found in Surah {metadata.get_surah_name(result[0])} ' \
                        f'({result[0]}) Ayah {result[1]}' \
                    '</span>'
                row = SearchListBoxRow(text, label)
                row.id = (result[0], result[1])
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
        self.emit('go-to-suraya', *listboxrow.id)


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/search_listboxrow.ui')
class SearchListBoxRow(Gtk.ListBoxRow):
    __gtype_name__ = 'SearchListBoxRow'

    textview = Gtk.Template.Child()
    label = Gtk.Template.Child()
    textbuffer = Gtk.Template.Child()

    def __init__(
            self,
            text: str,
            label: str,
            **kwargs) -> None:
        super().__init__(**kwargs)

        self.textbuffer.insert_markup(
            self.textbuffer.get_start_iter(), text, -1)
        self.label.set_markup(label)
