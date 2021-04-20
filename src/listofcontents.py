# listofcontents.py
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
from gi.repository import Pango

from . import constants as const
from .model import Metadata

@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/listofcontents_popover.ui')
class ListofContentsPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'ListofContentsPopover'

    __gsignals__ = {
        'go-to-suraya': (GObject.SIGNAL_RUN_CLEANUP, None, (int, int))}

    entry = Gtk.Template.Child()
    listbox = Gtk.Template.Child()
    scrolledwindow = Gtk.Template.Child()

    def populate(self) -> bool:
        """Display a list of contents

        Basically, the list of contents is a grouping of ayahs according to
        scholars."""
        with Metadata() as metadata:
            for sura, aya, title in metadata.get_titles():
                label = Gtk.Label()
                label.set_halign(Gtk.Align.START)
                label.set_ellipsize(Pango.EllipsizeMode.END)
                label.set_justify(Gtk.Justification.FILL)

                if title.isupper():
                    markup = \
                        '<span weight="bold">' \
                            f'{title}' \
                        '</span>'
                else:
                    markup = \
                        '<span>' \
                            f'{title}' \
                        '</span>'
                label.set_markup(markup)

                row = Gtk.ListBoxRow()
                row.id = (sura, aya)
                row.add(label)
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
        self.emit('go-to-suraya', *listboxrow.id)
