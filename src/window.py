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

from .process import Process
from .widget.dialog import About
from .widget.popover import Navigation, Menu


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/window.ui')
class MainWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'main_window'

    PAGE_SIZE_WIDTH = 456
    PAGE_SIZE_HEIGHT = 672

    PAGE_NO_MIN = 1
    PAGE_NO_MAX = 604
    page_no: int = 1

    SURA_NO_MIN = 1
    SURA_NO_MAX = 30
    sura_no: int = 1

    AYAH_NO_MIN = 1
    AYAH_NO_MAX = None
    ayah_no: int = 1

    JUZ_NO_MIN = 1
    JUZ_NO_MAX = 30
    juz_no: int = 1

    HIZB_NO_MIN = 1
    HIZB_NO_MAX = 7
    hizb_no: int = 1

    process = Process()

    popover_nav = Navigation()
    btn_open_nav = Gtk.Template.Child('btn_open_nav')

    popover_menu = Menu()
    btn_open_menu = Gtk.Template.Child('btn_open_menu')

    page_left = Gtk.Template.Child('page_left')
    page_right = Gtk.Template.Child('page_right')

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

        self.btn_open_nav.set_popover(self.popover_nav)
        self.popover_nav.spin_page_no.connect('value-changed', self.go_to_page)

        self.btn_open_menu.set_popover(self.popover_menu)
        self.popover_menu.btn_about.connect('clicked', self.show_about)

        self.view()

    def view(self, page_no: int = 1) -> None:
        if page_no % 2 == 0:
            page_no -= 1

        # Set image corresponding to the page
        def set_page(page: Gtk.Image, index: int) -> None:
            pixbuf = GdkPixbuf.Pixbuf.new_from_resource_at_scale(
                f'/org/naruaika/Quran/res/pages/{index}.png',
                self.PAGE_SIZE_WIDTH, self.PAGE_SIZE_HEIGHT, True)
            page.set_from_pixbuf(pixbuf)

        set_page(self.page_right, page_no)
        set_page(self.page_left, page_no + 1)

        self.btn_previous_page.set_visible(page_no != self.PAGE_NO_MIN)
        self.btn_next_page.set_visible(page_no != self.PAGE_NO_MAX - 1)

        # Update current page info
        self.popover_nav.spin_page_no.set_value(self.page_no)

    def go_previous_page(self, button: Gtk.Button) -> None:
        self.page_no = max(self.page_no - 2, self.PAGE_NO_MIN)
        self.view(self.page_no)

    def go_next_page(self, button: Gtk.Button) -> None:
        self.page_no = min(self.page_no + 2, self.PAGE_NO_MAX)
        self.view(self.page_no)

    def go_to_page(self, spin: Gtk.SpinButton) -> None:
        self.page_no = int(spin.get_value())
        self.view(self.page_no)

    def show_about(self, button: Gtk.Button) -> None:
        About().show_all()
