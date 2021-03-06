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

from . import constants as const
from . import globals as glob
from .model import Metadata
from .model import Musshaf


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/navigation.ui')
class NavigationPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'NavigationPopover'

    __gsignals__ = {
        'reload-musshaf-viewer': (GObject.SIGNAL_NO_RECURSE, None, ()),
        'reload-tarajem-viewer': (GObject.SIGNAL_NO_RECURSE, None, ()),
        'reload-telaawa-player': (GObject.SIGNAL_NO_RECURSE, None, ()),
        'change-win-title': (GObject.SIGNAL_NO_RECURSE, None, (str,))}

    spin_page_no = Gtk.Template.Child()
    spin_ayah_no = Gtk.Template.Child()
    spin_juz_no = Gtk.Template.Child()
    spin_hizb_no = Gtk.Template.Child()
    spin_manzil_no = Gtk.Template.Child()
    spin_ruku_no = Gtk.Template.Child()
    page_length = Gtk.Template.Child()
    surah_length = Gtk.Template.Child()
    combo_surah_name = Gtk.Template.Child()
    entry_surah_name = Gtk.Template.Child()
    complete_surah_name = Gtk.Template.Child()
    adjust_ayah_no = Gtk.Template.Child()
    adjust_page_no = Gtk.Template.Child()
    container_quarter = Gtk.Template.Child()

    main_container = Gtk.Template.Child()
    secondary_container = Gtk.Template.Child()

    # To adjust the page numbering in the page navigation system based on the
    # page image index
    page_no_start: int = None
    page_no_end: int = None

    # Optimizers
    is_updating: bool = False  # to stop unwanted signal triggering

    def __init__(
            self,
            navigator_id: int,
            **kwargs) -> None:
        super().__init__(**kwargs)

        self.id = navigator_id  # 0 for the main navigator panel

        self.setup_form()

    def setup_form(self) -> None:
        with Metadata() as metadata, \
             Musshaf() as musshaf:
            # Set all initial values of the form according to the opened
            # Musshaf ID
            self.page_no_start = musshaf.get_page_no(1, 1)
            self.page_no_end = musshaf.get_page_no(114, 6)
            musshaf_dir = \
                path.join(const.USER_DATA_PATH, f'musshaf/{glob.musshaf_name}')
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
        glob.page_number = int(button.get_value()) + self.page_no_start - 1
        self.update('page-number')

    @Gtk.Template.Callback()
    def go_to_surah(self, box: Gtk.ComboBoxText) -> None:
        text = box.get_child().get_text()
        if len(text) < 3:
            return
        try:
            glob.surah_number = int(text.split('.')[0])
            self.update('surah-number')
        except:
            return

    @Gtk.Template.Callback()
    def go_to_ayah(
            self,
            button: Gtk.SpinButton) -> None:
        if self.is_updating:
            return
        glob.ayah_number = int(button.get_value())
        self.update('ayah-number')

    @Gtk.Template.Callback()
    def go_to_juz(
            self,
            button: Gtk.SpinButton) -> None:
        if self.is_updating:
            return
        glob.juz_number = int(button.get_value())
        self.update('juz-number')

    @Gtk.Template.Callback()
    def go_to_hizb(
            self,
            button: Gtk.SpinButton) -> None:
        if self.is_updating:
            return
        glob.hizb_number = int(button.get_value())
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
                glob.quarter_number = index
                self.update('quarter-number')
                break

    @Gtk.Template.Callback()
    def go_to_manzil(
            self,
            button: Gtk.SpinButton) -> None:
        if self.is_updating:
            return
        glob.manzil_number = int(button.get_value())
        self.update('manzil-number')

    @Gtk.Template.Callback()
    def go_to_ruku(
            self,
            button: Gtk.SpinButton) -> None:
        if self.is_updating:
            return
        glob.ruku_number = int(button.get_value())
        self.update('ruku-number')

    def go_to_previous_page(
            self,
            *args) -> None:
        if not self.in_focus():
            return
        self.spin_page_no.set_value(self.spin_page_no.get_value() - 1)

    def go_to_next_page(
            self,
            *args) -> None:
        if not self.in_focus():
            return
        self.spin_page_no.set_value(self.spin_page_no.get_value() + 1)

    def go_to_defined_page(
            self,
            widget: Gtk.Widget,
            page_no: int) -> None:
        if not self.in_focus():
            return

        glob.page_number = page_no
        self.update('page-number')

    def go_to_previous_ayah(
            self,
            *args,
            fixed_surah_no: bool = True) -> None:
        if not self.in_focus():
            return

        ayah_no = glob.ayah_number - 1
        if self.adjust_ayah_no.get_lower() > ayah_no:
            if not fixed_surah_no \
                    and not (glob.surah_number == 1
                             and glob.ayah_number == 1):
                glob.surah_number = max(1, glob.surah_number - 1)
                with Metadata() as metadata:
                    glob.ayah_number = metadata.get_surah_length(
                        glob.surah_number)
                self.update('ayah-number')
            else:
                self.emit('reload-telaawa-player')
        else:
            self.spin_ayah_no.set_value(ayah_no)

    def go_to_next_ayah(
            self,
            *args,
            fixed_surah_no: bool = True) -> None:
        if not self.in_focus():
            return

        ayah_no = glob.ayah_number + 1
        if self.adjust_ayah_no.get_upper() < ayah_no:
            if glob.playback_loop:
                self.spin_ayah_no.set_value(1)
            elif not fixed_surah_no \
                    and not (glob.surah_number == 114
                             and glob.ayah_number == 6):
                glob.surah_number = min(114, glob.surah_number + 1)
                self.update('surah-number')
            else:
                self.emit('reload-telaawa-player')
        else:
            self.spin_ayah_no.set_value(ayah_no)

    def go_to_suraya(
            self,
            widget: Gtk.Widget,
            surah_no: int,
            ayah_no: int) -> None:
        if not self.in_focus():
            return

        glob.surah_number = surah_no
        glob.ayah_number = ayah_no
        self.update('ayah-number')

    def update(
            self,
            keyword: str = None) -> None:
        """Synchronise the change to other variables."""
        if self.is_updating:
            return

        if not self.in_focus():
            return

        with Musshaf() as musshaf, \
             Metadata() as metadata:
            if keyword == 'page-number':
                glob.surah_number = musshaf.get_surah_no(glob.page_number)
                glob.ayah_number = musshaf.get_ayah_no(glob.page_number)
                glob.juz_number = metadata.get_juz_no(glob.surah_number, glob.ayah_number)
                hizb_no = metadata.get_hizb_no(glob.surah_number, glob.ayah_number)
                glob.hizb_number = hizb_no//4 + (hizb_no%4 > 0)
                glob.quarter_number = hizb_no%4 - 1
                glob.manzil_number = metadata.get_manzil_no(glob.surah_number, glob.ayah_number)
                glob.ruku_number = metadata.get_ruku_no(glob.surah_number, glob.ayah_number)
            elif keyword == 'surah-number':
                glob.ayah_number = 1
                glob.page_number = musshaf.get_page_no(glob.surah_number, glob.ayah_number)
                glob.juz_number = metadata.get_juz_no(glob.surah_number, glob.ayah_number)
                hizb_no = metadata.get_hizb_no(glob.surah_number, glob.ayah_number)
                glob.hizb_number = hizb_no//4 + (hizb_no%4 > 0)
                glob.quarter_number = hizb_no%4 - 1
                glob.manzil_number = metadata.get_manzil_no(glob.surah_number, glob.ayah_number)
                glob.ruku_number = metadata.get_ruku_no(glob.surah_number, glob.ayah_number)
            elif keyword == 'juz-number':
                glob.surah_number = metadata.get_surah_no(juz_no=glob.juz_number)
                glob.ayah_number = metadata.get_ayah_no(juz_no=glob.juz_number)
                glob.page_number = musshaf.get_page_no(glob.surah_number, glob.ayah_number)
                hizb_no = metadata.get_hizb_no(glob.surah_number, glob.ayah_number)
                glob.hizb_number = hizb_no//4 + (hizb_no%4 > 0)
                glob.quarter_number = 0
                glob.manzil_number = metadata.get_manzil_no(glob.surah_number, glob.ayah_number)
                glob.ruku_number = metadata.get_ruku_no(glob.surah_number, glob.ayah_number)
            elif keyword == 'hizb-number':
                hizb_no = (glob.hizb_number-1)*4 + 1
                glob.surah_number = metadata.get_surah_no(hizb_no=hizb_no)
                glob.ayah_number = metadata.get_ayah_no(hizb_no=hizb_no)
                glob.page_number = musshaf.get_page_no(glob.surah_number, glob.ayah_number)
                glob.juz_number = metadata.get_juz_no(glob.surah_number, glob.ayah_number)
                glob.quarter_number = 0
                glob.manzil_number = metadata.get_manzil_no(glob.surah_number, glob.ayah_number)
                glob.ruku_number = metadata.get_ruku_no(glob.surah_number, glob.ayah_number)
            elif keyword == 'quarter-number':
                hizb_no = (glob.hizb_number-1)*4 + 1 + glob.quarter_number
                glob.surah_number = metadata.get_surah_no(hizb_no=hizb_no)
                glob.ayah_number = metadata.get_ayah_no(hizb_no=hizb_no)
                glob.page_number = musshaf.get_page_no(glob.surah_number, glob.ayah_number)
                glob.juz_number = metadata.get_juz_no(glob.surah_number, glob.ayah_number)
                glob.manzil_number = metadata.get_manzil_no(glob.surah_number, glob.ayah_number)
                glob.ruku_number = metadata.get_ruku_no(glob.surah_number, glob.ayah_number)
            elif keyword == 'manzil-number':
                glob.surah_number = metadata.get_surah_no(manzil_no=glob.manzil_number)
                glob.ayah_number = metadata.get_ayah_no(manzil_no=glob.manzil_number)
                glob.page_number = musshaf.get_page_no(glob.surah_number, glob.ayah_number)
                glob.juz_number = metadata.get_juz_no(glob.surah_number, glob.ayah_number)
                hizb_no = metadata.get_hizb_no(glob.surah_number, glob.ayah_number)
                glob.hizb_number = hizb_no//4 + (hizb_no%4 > 0)
                glob.quarter_number = 0
                glob.ruku_number = metadata.get_ruku_no(glob.surah_number, glob.ayah_number)
            elif keyword == 'ruku-number':
                glob.surah_number = metadata.get_surah_no(ruku_no=glob.ruku_number)
                glob.ayah_number = metadata.get_ayah_no(ruku_no=glob.ruku_number)
                glob.page_number = musshaf.get_page_no(glob.surah_number, glob.ayah_number)
                glob.juz_number = metadata.get_juz_no(glob.surah_number, glob.ayah_number)
                hizb_no = metadata.get_hizb_no(glob.surah_number, glob.ayah_number)
                glob.hizb_number = hizb_no//4 + (hizb_no%4 > 0)
                glob.quarter_number = 0
                glob.manzil_number = metadata.get_manzil_no(glob.surah_number, glob.ayah_number)
            else:
                # if the `keyword` is not specified, it is assumed that the
                # ayah number has been changed
                glob.page_number = musshaf.get_page_no(glob.surah_number, glob.ayah_number)
                glob.juz_number = metadata.get_juz_no(glob.surah_number, glob.ayah_number)
                hizb_no = metadata.get_hizb_no(glob.surah_number, glob.ayah_number)
                glob.hizb_number = hizb_no//4 + (hizb_no%4 > 0)
                glob.quarter_number = hizb_no%4 - 1
                glob.manzil_number = metadata.get_manzil_no(glob.surah_number, glob.ayah_number)
                glob.ruku_number = metadata.get_ruku_no(glob.surah_number, glob.ayah_number)
            surah_length = metadata.get_surah_length(glob.surah_number)

        self.is_updating = True

        # Update all widget values
        self.spin_page_no.set_value(
            glob.page_number - self.page_no_start + 1)
        if self.page_no_start <= glob.page_number <= self.page_no_end:
            self.surah_length.set_text(f'(1–{surah_length})')
            self.adjust_ayah_no.set_upper(surah_length)
            self.combo_surah_name.set_active_id(str(glob.surah_number))
            self.spin_ayah_no.set_value(glob.ayah_number)
            self.spin_juz_no.set_value(glob.juz_number)
            self.spin_hizb_no.set_value(glob.hizb_number)
            self.spin_manzil_no.set_value(glob.manzil_number)
            self.spin_ruku_no.set_value(glob.ruku_number)
            radio_quarters = self.container_quarter.get_children()
            radio_quarters[glob.quarter_number].set_active(True)

        self.is_updating = False

        # Request updates to the headerbar
        if glob.surah_number > 0:
            surah_name = self.entry_surah_name.get_text()
            self.emit('change-win-title', f'{surah_name.split()[1]} '
                                          f'({glob.surah_number}) : '
                                          f'{glob.ayah_number:.0f}')
        else:
            glob.page_focused = -1  # to hide tarajem viewer if it is being
                                    # displayed
            self.emit('change-win-title', const.APPLICATION_NAME)

        # Request updates to the Musshaf, tarajem, and telawa
        self.emit('reload-musshaf-viewer')
        self.emit('reload-tarajem-viewer')
        self.emit('reload-telaawa-player')

    def in_focus(self) -> bool:
        if (glob.mobile_view and self.id == 0) \
                or (not glob.mobile_view and self.id > 0):
            return False
        return True
