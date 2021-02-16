# window.py
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

gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gdk, GdkPixbuf, Gtk
from .widget.dialog import About
from .widget.popover import Navigation, Menu


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/window.ui')
class MainWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'main_window'

    # Constants
    PAGE_SIZE_WIDTH = 552
    PAGE_SIZE_HEIGHT = 683
    PAGE_INDEX_MIN = 1
    PAGE_INDEX_MAX = 604

    # Globals
    page_index = 1

    # Components
    popover_nav = Navigation()
    btn_nav = Gtk.Template.Child('btn_nav')

    popover_menu = Menu()
    btn_menu = Gtk.Template.Child('btn_menu')

    page_left = Gtk.Template.Child('page_left')
    page_right = Gtk.Template.Child('page_right')
    page_left_no = Gtk.Template.Child('page_left_no')
    page_right_no = Gtk.Template.Child('page_right_no')

    btn_next_page = Gtk.Template.Child('btn_next_page')
    btn_previous_page = Gtk.Template.Child('btn_previous_page')

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Set properties
        self.set_title('Quran')
        self.set_wmclass('Quran', 'Quran')

        # Set stylesheet
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        provider.load_from_resource('/org/naruaika/Quran/res/css/main.css')
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Add signal handlers
        self.btn_previous_page.connect('clicked', self.go_previous_page)
        self.btn_next_page.connect('clicked', self.go_next_page)

        self.btn_nav.set_popover(self.popover_nav)
        self.popover_nav.spin_page_no.connect('value-changed', self.go_to_page)

        self.btn_menu.set_popover(self.popover_menu)
        self.popover_menu.btn_about.connect('clicked', self.show_about)

        self.view()

    def view(self, page_index: int = 1) -> None:
        if page_index % 2 == 0:
            page_index -= 1

        # Set image corresponding to the page
        def set_page(page: Gtk.Image, index: int) -> None:
            pixbuf = GdkPixbuf.Pixbuf.new_from_resource_at_scale(
                f'/org/naruaika/Quran/res/pages/{index}.png',
                self.PAGE_SIZE_WIDTH, self.PAGE_SIZE_HEIGHT, True)
            page.set_from_pixbuf(pixbuf)

        set_page(self.page_right, page_index)
        self.page_right_no.set_text(str(page_index))

        set_page(self.page_left, page_index + 1)
        self.page_left_no.set_text(str(page_index + 1))

        self.btn_previous_page.set_visible(self.page_index != self.PAGE_INDEX_MIN)
        self.btn_next_page.set_visible(self.page_index != self.PAGE_INDEX_MAX)

        # Update current page info
        self.popover_nav.spin_page_no.set_value(self.page_index)

    def go_previous_page(self, button: Gtk.Button) -> None:
        self.page_index = max(self.page_index - 2, self.PAGE_INDEX_MIN)
        self.view(self.page_index)

    def go_next_page(self, button: Gtk.Button) -> None:
        self.page_index = min(self.page_index + 2, self.PAGE_INDEX_MAX)
        self.view(self.page_index)

    def go_to_page(self, spin: Gtk.SpinButton) -> None:
        self.page_index = int(spin.get_value())
        self.view(self.page_index)

    def show_about(self, button: Gtk.Button) -> None:
        About().show_all()
