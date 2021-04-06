# navigation.py
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
from os import listdir
from os import path

from . import globals as glo
from .constants import APPLICATION_NAME
from .constants import RESOURCE_PATH
from .constants import USER_DATA_PATH
from .model import Metadata
from .model import Musshaf


@Gtk.Template(resource_path=f'{RESOURCE_PATH}/ui/navigation.ui')
class NavigationPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'NavigationPopover'

    __gsignals__ = {
        'reload-musshaf-viewer': (GObject.SIGNAL_NO_RECURSE, None, ()),
        'reload-tarajem-viewer': (GObject.SIGNAL_NO_RECURSE, None, ()),
        'reload-telaawa-player': (GObject.SIGNAL_NO_RECURSE, None, ()),
        'change-win-title': (GObject.SIGNAL_NO_RECURSE, None, (str,))}

    # TODO: select all text on focus
    spin_page_no = Gtk.Template.Child('spin_page_no')
    spin_ayah_no = Gtk.Template.Child('spin_ayah_no')
    spin_juz_no = Gtk.Template.Child('spin_juz_no')
    spin_hizb_no = Gtk.Template.Child('spin_hizb_no')
    page_length = Gtk.Template.Child('page_length')
    surah_length = Gtk.Template.Child('surah_length')

    # TODO: list items is too long
    combo_surah_name = Gtk.Template.Child('combo_surah_name')
    entry_surah_name = Gtk.Template.Child('entry_surah_name')
    complete_surah_name = Gtk.Template.Child('complete_surah_name')
    adjust_ayah_no = Gtk.Template.Child('adjust_ayah_no')
    adjust_page_no = Gtk.Template.Child('adjust_page_no')
    container_quarter = Gtk.Template.Child('container_quarter')

    container = Gtk.Template.Child('container')

    # To adjust the page numbering in the page navigation system based on the
    # page image index
    page_no_start: int = None
    page_no_end: int = None

    # Optimizers
    is_updating: bool = False  # to stop unwanted signal triggering

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.setup_form()

    def setup_form(self) -> None:
        with Metadata() as metadata, \
             Musshaf() as musshaf:
            # Set all initial values of the form according to the opened
            # Musshaf ID
            self.page_no_start = musshaf.get_page_no(1, 1)
            self.page_no_end = musshaf.get_page_no(114, 6)
            musshaf_dir = \
                path.join(USER_DATA_PATH, f'musshaf/{glo.musshaf_name}')
            self.page_length.set_text(
                f'(1–{self.page_no_end - self.page_no_start + 1})')
            page_count = len(listdir(musshaf_dir))
            self.adjust_page_no.set_lower(1 - self.page_no_start + 1)
            self.adjust_page_no.set_upper(page_count - self.page_no_start + 1)

            # Populate a list of surah names
            liststore = Gtk.ListStore(str, str)
            for surah in metadata.get_surahs():
                surah_no = str(surah[0])
                liststore.append([surah_no, f'{surah_no}. {surah[5]}'])
                self.combo_surah_name.append(
                    surah_no, f'{surah_no}. {surah[4]}')
            self.complete_surah_name.set_model(liststore)
            self.complete_surah_name.set_text_column(1)

        def search_surah(
                completion: Gtk.EntryCompletion,
                query: str,
                iter: Gtk.TreeIter,
                *user_data) -> bool:
            surah_name = completion.get_model()[iter][1]
            return query in surah_name.lower()

        # Set the search function for surah name
        self.complete_surah_name.set_match_func(search_surah, None)

    @Gtk.Template.Callback()
    def go_to_page(
            self,
            button: Gtk.SpinButton) -> None:
        if self.is_updating:
            return
        glo.page_number = int(button.get_value()) + self.page_no_start - 1
        self.update('page-number')

    @Gtk.Template.Callback()
    def go_to_surah(self, box: Gtk.ComboBoxText) -> None:
        text = box.get_child().get_text()
        if len(text) < 3:
            return
        try:
            glo.surah_number = int(text.split('.')[0])
            self.update('surah-number')
        except:
            return

    @Gtk.Template.Callback()
    def go_to_ayah(
            self,
            button: Gtk.SpinButton) -> None:
        if self.is_updating:
            return
        glo.ayah_number = int(button.get_value())
        self.update('ayah-number')

    @Gtk.Template.Callback()
    def go_to_juz(
            self,
            button: Gtk.SpinButton) -> None:
        if self.is_updating:
            return
        glo.juz_number = int(button.get_value())
        self.update('juz-number')

    @Gtk.Template.Callback()
    def go_to_hizb(
            self,
            button: Gtk.SpinButton) -> None:
        if self.is_updating:
            return
        glo.hizb_number = int(button.get_value())
        self.update('hizb-number')

    @Gtk.Template.Callback()
    def go_to_quarter(
            self,
            button: Gtk.RadioButton) -> None:
        if self.is_updating \
                or not button.get_active():
            return
        radio_quarters = self.container_quarter.get_children()
        for index, radio in enumerate(radio_quarters):
            if button == radio:
                glo.quarter_number = index
                self.update('quarter-number')
                break

    def go_to_previous_page(
            self,
            button: Gtk.Button) -> None:
        self.spin_page_no.set_value(self.spin_page_no.get_value() - 1)

    def go_to_next_page(
            self,
            button: Gtk.Button) -> None:
        self.spin_page_no.set_value(self.spin_page_no.get_value() + 1)

    def go_to_next_ayah(
            self,
            button: Gtk.Button) -> None:
        ayah_no = self.spin_ayah_no.get_value() + 1
        if self.adjust_ayah_no.get_upper() < ayah_no:
            self.emit('reload-telaawa-player')
        else:
            self.spin_ayah_no.set_value(ayah_no)

    def update(
            self,
            keyword: str = None) -> None:
        """Synchronise the change to other variables."""
        if self.is_updating:
            return

        with Musshaf() as musshaf, \
             Metadata() as metadata:
            if keyword == 'page-number':
                glo.surah_number = musshaf.get_surah_no(glo.page_number)
                glo.ayah_number = musshaf.get_ayah_no(glo.page_number)
                glo.juz_number = \
                    metadata.get_juz_no(glo.surah_number, glo.ayah_number)
                hizb_no = \
                    metadata.get_hizb_no(glo.surah_number, glo.ayah_number)
                glo.hizb_number = hizb_no//4 + (hizb_no%4 > 0)
                glo.quarter_number = hizb_no%4 - 1
            elif keyword == 'surah-number':
                glo.ayah_number = 1
                glo.page_number = \
                    musshaf.get_page_no(glo.surah_number, glo.ayah_number)
                glo.juz_number = \
                    metadata.get_juz_no(glo.surah_number, glo.ayah_number)
                hizb_no = \
                    metadata.get_hizb_no(glo.surah_number, glo.ayah_number)
                glo.hizb_number = hizb_no//4 + (hizb_no%4 > 0)
                glo.quarter_number = hizb_no%4 - 1
            elif keyword == 'juz-number':
                glo.surah_number = metadata.get_surah_no(juz_no=glo.juz_number)
                glo.ayah_number = metadata.get_ayah_no(juz_no=glo.juz_number)
                glo.page_number = \
                    musshaf.get_page_no(glo.surah_number, glo.ayah_number)
                hizb_no = \
                    metadata.get_hizb_no(glo.surah_number, glo.ayah_number)
                glo.hizb_number = hizb_no//4 + (hizb_no%4 > 0)
                glo.quarter_number = 0
            elif keyword == 'hizb-number':
                hizb_no = (glo.hizb_number-1)*4 + 1
                glo.surah_number = metadata.get_surah_no(hizb_no=hizb_no)
                glo.ayah_number = metadata.get_ayah_no(hizb_no=hizb_no)
                glo.page_number = \
                    musshaf.get_page_no(glo.surah_number, glo.ayah_number)
                glo.juz_number = \
                    metadata.get_juz_no(glo.surah_number, glo.ayah_number)
                glo.quarter_number = 0
            elif keyword == 'quarter-number':
                hizb_no = (glo.hizb_number-1)*4 + 1 + glo.quarter_number
                glo.surah_number = metadata.get_surah_no(hizb_no=hizb_no)
                glo.ayah_number = metadata.get_ayah_no(hizb_no=hizb_no)
                glo.page_number = \
                    musshaf.get_page_no(glo.surah_number, glo.ayah_number)
                glo.juz_number = \
                    metadata.get_juz_no(glo.surah_number, glo.ayah_number)
            else:
                # if the `keyword` is not specified, it is assumed that the
                # ayah number has been changed
                glo.page_number = \
                    musshaf.get_page_no(glo.surah_number, glo.ayah_number)
                glo.juz_number = \
                    metadata.get_juz_no(glo.surah_number, glo.ayah_number)
                hizb_no = \
                    metadata.get_hizb_no(glo.surah_number, glo.ayah_number)
                glo.quarter_number = hizb_no%4 - 1
                glo.hizb_number = hizb_no//4 + (hizb_no%4 > 0)
            surah_length = metadata.get_surah_length(glo.surah_number)

        self.is_updating = True

        # Update all widget values
        self.spin_page_no.set_value(
            glo.page_number - self.page_no_start + 1)
        if self.page_no_start <= glo.page_number <= self.page_no_end:
            self.surah_length.set_text(f'(1–{surah_length})')
            self.adjust_ayah_no.set_upper(surah_length)
            self.combo_surah_name.set_active_id(str(glo.surah_number))
            self.spin_ayah_no.set_value(glo.ayah_number)
            self.spin_juz_no.set_value(glo.juz_number)
            self.spin_hizb_no.set_value(glo.hizb_number)
            radio_quarters = self.container_quarter.get_children()
            radio_quarters[glo.quarter_number].set_active(True)

        self.is_updating = False

        # Request updates to the headerbar
        if glo.surah_number > 0:
            surah_name = self.entry_surah_name.get_text()
            self.emit('change-win-title', f'{surah_name.split()[1]} '
                                          f'({glo.surah_number}) : '
                                          f'{glo.ayah_number:.0f}')
        else:
            glo.page_focused = -1  # to hide tarajem viewer if it is being
                                   # displayed
            self.emit('change-win-title', APPLICATION_NAME)

        # Request updates to the Musshaf, tarajem, and telawa
        self.emit('reload-musshaf-viewer')
        self.emit('reload-tarajem-viewer')
        self.emit('reload-telaawa-player')
