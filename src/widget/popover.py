# popover.py
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

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/popover/navigation.ui')
class Navigation(Gtk.PopoverMenu):
    __gtype_name__ = 'popover_nav'

    spin_page_no = Gtk.Template.Child('spin_page_no')


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/popover/menu.ui')
class Menu(Gtk.PopoverMenu):
    __gtype_name__ = 'popover_menu'

    btn_preferences = Gtk.Template.Child('btn_preferences')
    btn_shortcut = Gtk.Template.Child('btn_shortcut')
    btn_help = Gtk.Template.Child('btn_help')
    btn_about = Gtk.Template.Child('btn_about')
    btn_quit = Gtk.Template.Child('btn_quit')
