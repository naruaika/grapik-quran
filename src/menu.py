# menu.py
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

from gi.repository import GObject
from gi.repository import Gtk

from . import constants as const
from . import globals as glo
from .about import AboutDialog


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/menu.ui')
class MainMenu(Gtk.PopoverMenu):
    __gtype_name__ = 'Menu'

    __gsignals__ = {
        'nightmode-toggled': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'dualpage-toggled': (GObject.SIGNAL_RUN_FIRST, None, ())}

    button_check_dual = Gtk.Template.Child('button_check_dual')
    button_check_nightmode = Gtk.Template.Child('button_check_nightmode')
    button_open_musshaf = Gtk.Template.Child('button_open_musshaf')
    button_open_preferences = Gtk.Template.Child('button_open_preferences')
    button_open_shortcut = Gtk.Template.Child('button_open_shortcut')
    button_open_help = Gtk.Template.Child('button_open_help')
    button_about = Gtk.Template.Child('button_about')
    button_quit = Gtk.Template.Child('button_quit')

    def __init__(
            self,
            **kwargs) -> None:
        super().__init__(**kwargs)

        self.button_check_dual.props.role = Gtk.ButtonRole.CHECK
        self.button_check_nightmode.props.role = Gtk.ButtonRole.CHECK

        self.button_check_dual.props.active = glo.dual_page

    @Gtk.Template.Callback()
    def toggle_dualpage(
            self,
            button: Gtk.Button) -> None:
        button.props.active = not button.props.active
        self.emit('dualpage-toggled')

    @Gtk.Template.Callback()
    def toggle_nightmode(
            self,
            button: Gtk.Button) -> None:
        button.props.active = not button.props.active
        self.emit('nightmode-toggled')

    @Gtk.Template.Callback()
    def change_musshaf(
            self,
            button: Gtk.Button) -> None:
        window = self.get_toplevel()
        window.get_application().switch_to('musshaf_dialog')
        window.destroy()

    @Gtk.Template.Callback()
    def show_about(
            self,
            button: Gtk.Button) -> None:
        dialog = AboutDialog()
        dialog.set_logo_icon_name(const.APPLICATION_ID)
        dialog.set_version(const.APPLICATION_VERSION)
        dialog.set_transient_for(self.get_toplevel())
        dialog.present()

    @Gtk.Template.Callback()
    def on_quit(
            self,
            button: Gtk.Button) -> None:
        self.get_toplevel().destroy()
