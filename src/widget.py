# widget.py
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

from gi.repository import Gtk, GLib


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/about.ui')
class AboutDialog(Gtk.AboutDialog):
    __gtype_name__ = 'dialog_about'


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/navigation.ui')
class NavPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'popover_nav'

    # TODO: select all text on focus
    spin_page_no = Gtk.Template.Child('spin_page_no')
    spin_aya_no = Gtk.Template.Child('spin_aya_no')
    spin_juz_no = Gtk.Template.Child('spin_juz_no')
    spin_hizb_no = Gtk.Template.Child('spin_hizb_no')
    page_length = Gtk.Template.Child('page_length')
    aya_length = Gtk.Template.Child('aya_length')

    # FIXME: list items is too long
    combo_sura_name = Gtk.Template.Child('combo_sura_name')
    entry_sura_name = Gtk.Template.Child('entry_sura_name')

    # TODO: connect completion to entry
    complete_sura_name = Gtk.Template.Child('complete_sura_name')
    adjust_aya_no = Gtk.Template.Child('adjust_aya_no')


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/translation.ui')
class TarajemPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'popover_tarajem'

    entry = Gtk.Template.Child('entry')
    listbox = Gtk.Template.Child('listbox')


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/main_menu.ui')
class MenuPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'popover_menu'

    btn_preferences = Gtk.Template.Child('btn_preferences')
    btn_shortcut = Gtk.Template.Child('btn_shortcut')
    btn_help = Gtk.Template.Child('btn_help')
    btn_about = Gtk.Template.Child('btn_about')
    btn_quit = Gtk.Template.Child('btn_quit')


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/message.ui')
class ToastMessage(Gtk.Revealer):
    __gtype_name__ = 'revealer_message'

    message = Gtk.Template.Child('message')

    def notify(self, message, timeout=3):
        self.message.set_text(message)
        self.set_reveal_child(True)

        def hide():
            self.set_reveal_child(False)

        if timeout > 0:
            GLib.timeout_add(timeout * 1000, hide)
