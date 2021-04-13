# bookmark.py
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

from . import globals as glob
from . import constants as const
from .model import Musshaf

@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/bookmark_popover.ui')
class BookmarkPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'BookmarkPopover'

    __gsignals__ = {
        'go-to-page': (GObject.SIGNAL_RUN_CLEANUP, None, (int,))}

    entry = Gtk.Template.Child()
    listbox = Gtk.Template.Child()
    scrolledwindow = Gtk.Template.Child()

    # To adjust the page numbering in the page navigation system based on the
    # page image index
    page_no_start: int = None

    def __init__(
            self,
            **kwargs) -> None:
        super().__init__(**kwargs)

        with Musshaf() as musshaf:
            # Set all initial values of the form according to the opened
            # Musshaf ID
            self.page_no_start = musshaf.get_page_no(1, 1)

    def populate(self) -> bool:
        """Display user bookmark list

        Basically, it is a list of strings that must be parsed in the format
        `{musshaf_name:s};{page_number:d};{notes:s}`.
        """
        # Reset the display
        def reset(row: Gtk.ListBoxRow) -> None:
            self.listbox.remove(row)
        self.listbox.foreach(reset)

        for bookmark in glob.bookmark_names:
            musshaf_name, page_number, notes = bookmark.split(';')
            page_number = int(page_number)

            if musshaf_name != glob.musshaf_name:
                continue

            label = Gtk.Label()
            label.set_halign(Gtk.Align.START)
            markup = \
                '<span weight="bold">' \
                    f'Page No. {page_number - self.page_no_start + 1} ' \
                '</span>\n' \
                '<span size="small">' \
                    f'{notes}' \
                '</span>'
            label.set_markup(markup)

            hbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            hbox.pack_start(label, True, True, 0)

            row = Gtk.ListBoxRow()
            row.id = page_number
            row.add(hbox)
            self.listbox.add(row)

        self.listbox.show_all()

        if self.listbox.get_children():
            return True
        return False

    @Gtk.Template.Callback()
    def select(
            self,
            listbox: Gtk.ListBox,
            listboxrow: Gtk.ListBoxRow) -> None:
        if not listboxrow:
            return
        self.emit('go-to-page', listboxrow.id)

    @Gtk.Template.Callback()
    def on_shown(
            self,
            widget: Gtk.Widget) -> None:
        self.populate()
