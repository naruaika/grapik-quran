# headerbar.py
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

from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Handy

from . import constants as const
from . import globals as glob
from .menu import MainMenu
from .navigation import NavigationPopover
from .tarajem import TarajemPopover
from .telaawa import TelaawaPopover


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/headerbar_hdy.ui')
class HeaderBar(Handy.HeaderBar):
    __gtype_name__ = 'HeaderBar'

    __gsignals__ = {
        'tarajem-toggled': (GObject.SIGNAL_RUN_CLEANUP, None, ()),
        'mobileview-toggled': (GObject.SIGNAL_RUN_CLEANUP, None, ())}

    Handy.init()

    squeezer = Gtk.Template.Child()
    headerbar_switcher = Gtk.Template.Child()
    button_open_search = Gtk.Template.Child()
    button_open_tarajem = Gtk.Template.Child()
    button_tarajem_option = Gtk.Template.Child()
    button_telaawa_playback = Gtk.Template.Child()
    icon_telaawa_playback = Gtk.Template.Child()
    button_telaawa_option = Gtk.Template.Child()
    button_open_mainmenu = Gtk.Template.Child()

    window_title = Gtk.Template.Child()
    window_title_alt = Gtk.Template.Child()

    button_open_navigation = Gtk.Template.Child()
    button_open_navigation_alt = Gtk.Template.Child()

    is_updating: bool = False  # to prevent unwanted widget triggering

    def __init__(
            self,
            **kwargs) -> None:
        super().__init__(**kwargs)

        child = self.squeezer.get_visible_child()
        glob.mobile_view = child != self.headerbar_switcher
        print(glob.mobile_view)

        self.setup_tarajem_popover()
        self.setup_navigation_popover()
        self.setup_telaawa_popover()
        self.setup_main_menu()

        # Watch the squeezer when it starts to hide some of its children
        self.squeezer.connect('notify::visible-child', self.on_squeezed)

    def setup_tarajem_popover(self) -> None:
        self.popover_tarajem = TarajemPopover()
        self.button_tarajem_option.set_popover(self.popover_tarajem)

    def setup_navigation_popover(self) -> None:
        self.popover_nav = NavigationPopover(0)
        self.button_open_navigation.set_popover(self.popover_nav)

        self.popover_nav_alt = NavigationPopover(1)
        self.popover_nav_alt.container.set_orientation(
            Gtk.Orientation.VERTICAL)
        self.popover_nav_alt.container.set_spacing(8)
        self.button_open_navigation_alt.set_popover(self.popover_nav_alt)

        # Whenever focused ayah changed, change the window title to the newly
        # selected ayah
        self.popover_nav.connect('change-win-title', self.change_title)
        self.popover_nav_alt.connect('change-win-title', self.change_title)

    def setup_telaawa_popover(self) -> None:
        self.popover_telaawa = TelaawaPopover()
        self.button_telaawa_option.set_popover(self.popover_telaawa)

        self.popover_telaawa.connect('telaawa-playback', self.telaawa_toggled)

    def setup_main_menu(self) -> None:
        self.popover_menu = MainMenu()
        self.button_open_mainmenu.set_popover(self.popover_menu)

    @Gtk.Template.Callback()
    def toggle_tarajem(
            self,
            button: Gtk.ToggleButton) -> None:
        glob.show_tarajem = button.get_active()
        self.emit('tarajem-toggled')

    @Gtk.Template.Callback()
    def toggle_telaawa(
            self,
            button: Gtk.ToggleButton) -> None:
        if self.is_updating:
            return

        is_activated = button.get_active()
        if is_activated:
            self.icon_telaawa_playback.set_from_icon_name(
                'media-playback-pause-symbolic', Gtk.IconSize.BUTTON)
        else:
            self.icon_telaawa_playback.set_from_icon_name(
                'media-playback-start-symbolic', Gtk.IconSize.BUTTON)

        button_playback_telaawa = self.popover_telaawa.button_toggle_playback
        button_playback_telaawa.set_active(is_activated)

    def telaawa_toggled(
            self,
            button: Gtk.ToggleButton,
            state: bool) -> None:
        self.is_updating = True
        self.button_telaawa_playback.set_active(state)
        self.is_updating = False

        if state:
            self.icon_telaawa_playback.set_from_icon_name(
                'media-playback-pause-symbolic', Gtk.IconSize.BUTTON)
        else:
            self.icon_telaawa_playback.set_from_icon_name(
                'media-playback-start-symbolic', Gtk.IconSize.BUTTON)

    def on_squeezed(
            self,
            squeezer: Handy.Squeezer,
            event: Gdk.Event) -> None:
        child = squeezer.get_visible_child()
        glob.mobile_view = child != self.headerbar_switcher
        self.emit('mobileview-toggled')

    def change_title(
            self,
            widget: Gtk.Widget,
            title: str) -> None:
        if not glob.mobile_view:
            self.window_title.set_text(title)
        else:
            self.window_title_alt.set_text(title)
