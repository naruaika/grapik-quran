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

from gi.repository import Gdk, GdkPixbuf, Gtk

from .model import Model
from .dialog import About
from .popover import Navigation, Help


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/window.ui')
class MainWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'main_window'

    PAGE_SIZE_WIDTH = 456  # in pixels
    PAGE_SIZE_HEIGHT = 672  # in pixels
    PAGE_SCALE = 1.0
    PAGE_MARGIN = 44  # in pixels
    PAGE_NO_MIN = 1
    PAGE_NO_MAX = 604
    AYA_NO_MIN = 1
    AYA_NO_MAX = -1
    HIZB_NO_MIN = 1

    page_no: int = 1
    sura_no: int = 1
    aya_no: int = 1
    juz_no: int = 1
    hizb_no: int = 1

    model = Model()
    popover_help = Help()
    popover_nav = Navigation()

    on_update: bool = False  # to stop unwanted signal triggering

    btn_open_menu = Gtk.Template.Child('btn_open_menu')
    btn_open_nav = Gtk.Template.Child('btn_open_nav')
    btn_back_page = Gtk.Template.Child('btn_back_page')
    btn_next_page = Gtk.Template.Child('btn_next_page')
    page_left = Gtk.Template.Child('page_left')
    page_right = Gtk.Template.Child('page_right')
    win_title = Gtk.Template.Child('win_title')

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Set window properties
        self.set_title('Quran')
        self.set_wmclass('Quran', 'Quran')

        # Set window style
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        provider.load_from_resource('/org/naruaika/Quran/res/css/main.css')
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Set signal handlers
        self.btn_open_menu.set_popover(self.popover_help)
        self.btn_open_nav.set_popover(self.popover_nav)
        self.btn_back_page.connect('clicked', self.go_previous_page)
        self.btn_next_page.connect('clicked', self.go_next_page)
        self.popover_nav.spin_page_no.connect('value-changed', self.go_to_page)
        self.popover_nav.combo_sura_name.connect('changed', self.go_to_sura)
        self.popover_nav.spin_aya_no.connect('value-changed', self.go_to_aya)
        self.popover_nav.spin_juz_no.connect('value-changed', self.go_to_juz)
        # self.popover_nav.spin_hizb_no.connect('value-changed', self.go_to_hizb)
        self.popover_help.btn_about.connect('clicked', self.show_about)

        # Set default views
        for sura in self.model.get_suras():
            sura_id = str(sura[0])
            sura_name = f'{sura_id}. {sura[4]}'
            self.popover_nav.combo_sura_name.append(sura_id, sura_name)

        # TODO: get last read page
        self.popover_nav.combo_sura_name.set_active_id(str(self.sura_no))

    def update(self, updated: str = None) -> None:
        if self.on_update:
            return

        # Sync other navigation variables
        if updated == 'page':
            self.sura_no = self.model.get_sura_no_by_page(self.page_no)
            self.aya_no = self.model.get_aya_no_by_page(self.page_no)
            self.juz_no = self.model.get_juz_no(self.sura_no, self.aya_no)
            self.hizb_no = self.model.get_hizb_no(self.sura_no, self.aya_no)
            self.AYA_NO_MAX = self.model.get_aya_no_max(self.sura_no)
        elif updated == 'sura':
            self.aya_no = self.AYA_NO_MIN
            self.page_no = self.model.get_page_no(self.sura_no, self.aya_no)
            self.juz_no = self.model.get_juz_no(self.sura_no, self.aya_no)
            self.hizb_no = self.model.get_hizb_no(self.sura_no, self.aya_no)
            self.AYA_NO_MAX = self.model.get_aya_no_max(self.sura_no)
        elif updated == 'aya':
            self.page_no = self.model.get_page_no(self.sura_no, self.aya_no)
            self.juz_no = self.model.get_juz_no(self.sura_no, self.aya_no)
            self.hizb_no = self.model.get_hizb_no(self.sura_no, self.aya_no)
        elif updated == 'juz':
            self.sura_no = self.model.get_sura_no_by_juz(juz_no=self.juz_no)
            self.aya_no = self.model.get_aya_no_by_juz(juz_no=self.juz_no)
            self.page_no = self.model.get_page_no(self.sura_no, self.aya_no)
            self.hizb_no = self.HIZB_NO_MIN
            self.AYA_NO_MAX = self.model.get_aya_no_max(self.sura_no)
        elif updated == 'hizb':
            ...

        # Always set odd page numbers for right pages
        page_right_no = self.page_no
        if self.page_no % 2 == 0:
            page_right_no -= 1

        def set_image(page: Gtk.Image, page_no: int) -> None:
            pixbuf = GdkPixbuf.Pixbuf.new_from_resource_at_scale(
                f'/org/naruaika/Quran/res/pages/{page_no}.png',
                self.PAGE_SIZE_WIDTH * self.PAGE_SCALE,
                self.PAGE_SIZE_HEIGHT * self.PAGE_SCALE, True)
            page.set_from_pixbuf(pixbuf)

        # Set the image corresponding to each page
        set_image(self.page_right, page_right_no)
        set_image(self.page_left, page_right_no + 1)

        self.on_update = True

        # Sync navigation widget's attributes
        self.popover_nav.spin_page_no.set_value(self.page_no)
        self.popover_nav.combo_sura_name.set_active_id(str(self.sura_no))
        self.popover_nav.adjust_aya_no.set_upper(self.AYA_NO_MAX)
        self.popover_nav.spin_aya_no.set_value(self.aya_no)
        self.popover_nav.spin_juz_no.set_value(self.juz_no)
        self.popover_nav.spin_hizb_no.set_value(self.hizb_no)
        sura_name = self.popover_nav.combo_sura_name.get_active_text()
        self.win_title.set_text(f'{sura_name.split()[1]} ({self.sura_no}) : '
                                f'{self.aya_no}')
        self.btn_back_page.set_visible(page_right_no > self.PAGE_NO_MIN)
        self.btn_next_page.set_visible(page_right_no + 1 < self.PAGE_NO_MAX)

        self.on_update = False

    def go_previous_page(self, button: Gtk.Button) -> None:
        self.page_no = max(self.page_no - 2, self.PAGE_NO_MIN)
        self.update('page')

    def go_next_page(self, button: Gtk.Button) -> None:
        self.page_no = min(self.page_no + 2, self.PAGE_NO_MAX)
        self.update('page')

    def go_to_page(self, button: Gtk.SpinButton) -> None:
        self.page_no = int(button.get_value())
        self.update('page')

    def go_to_sura(self, box: Gtk.ComboBoxText) -> None:
        self.sura_no = int(box.get_active_id())
        self.update('sura')

    def go_to_aya(self, button: Gtk.SpinButton) -> None:
        self.aya_no = int(button.get_value())
        self.update('aya')

    def go_to_juz(self, button: Gtk.SpinButton) -> None:
        self.juz_no = int(button.get_value())
        self.update('juz')

    # def go_to_hizb(self, button: Gtk.SpinButton) -> None:
    #     self.hizb_no = int(button.get_value())
    #     self.update('hizb')

    def show_about(self, button: Gtk.Button) -> None:
        # TODO: modal attach to window
        About().show_all()
