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

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Pango
from threading import Thread
import cairo
import copy
import os

from .model import Reader, ResourceManager
from .widget import AboutDialog, MusshafBox, NavPopover, TarajemPopover, \
    MenuPopover, ToastMessage


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/window.ui')
class MainWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'main_window'

    PAGE_SIZE_WIDTH = None  # in pixels
    PAGE_SIZE_HEIGHT = None  # in pixels
    PAGE_SCALE = 1.0
    PAGE_NO_MIN = 1
    PAGE_NO_MAX = None
    PAGE_NO_SHIFT = 0
    SURA_LENGTH = -1

    page_no: int = 1
    sura_no: int = 1
    aya_no: int = 1
    juz_no: int = 1
    hizb_no: int = 1

    # Support multiple ayah selections across two current opened pages
    # by providing both `page_right` and `page_left`.
    # For now, there's no intention of making selections across other pages. It
    # should be done using a special facility instead, if needed.
    bboxes = {'page_right': [], 'page_left': []}
    bboxes_hovered = {'page_right': [], 'page_left': []}
    bboxes_focused = {'page_right': [], 'page_left': []}
    tarajem_filtered = []

    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    is_updating: bool = False  # to stop unwanted signal triggering
    is_downloading: bool = False  # to limit download thread
    is_shift_pressed: bool = False
    is_tarajem_opened: bool = False
    is_welcome_opened: bool = True

    model = Reader()

    box_musshaf = MusshafBox()
    popover_menu = MenuPopover()
    popover_nav = NavPopover()
    popover_tarajem = TarajemPopover()
    toast_message = ToastMessage()

    btn_open_nav = Gtk.Template.Child('btn_open_nav')
    btn_open_more = Gtk.Template.Child('btn_open_more')
    btn_open_tarajem = Gtk.Template.Child('btn_open_tarajem')
    btn_open_tarajem = Gtk.Template.Child('btn_open_tarajem')
    btn_tarajem_option = Gtk.Template.Child('btn_tarajem_option')
    btn_back_page = Gtk.Template.Child('btn_back_page')
    btn_next_page = Gtk.Template.Child('btn_next_page')
    box_navbar = Gtk.Template.Child('box_navbar')
    page_left = Gtk.Template.Child('page_left')
    page_right = Gtk.Template.Child('page_right')
    page_left_evbox = Gtk.Template.Child('page_left_evbox')
    page_right_evbox = Gtk.Template.Child('page_right_evbox')
    page_left_drawarea = Gtk.Template.Child('page_left_drawarea')
    page_right_drawarea = Gtk.Template.Child('page_right_drawarea')
    page_left_scroll = Gtk.Template.Child('page_left_scroll')
    page_right_scroll = Gtk.Template.Child('page_right_scroll')
    page_left_listbox = Gtk.Template.Child('page_left_listbox')
    page_right_listbox = Gtk.Template.Child('page_right_listbox')
    main_overlay = Gtk.Template.Child('main_overlay')
    musshaf_viewer = Gtk.Template.Child('musshaf_viewer')
    win_title = Gtk.Template.Child('win_title')

    prev_card_focused = None
    prev_page_focused = None
    prev_mouse_event = None
    prev_scroll_y = None

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
        self.btn_back_page.connect('clicked', self.go_previous_page)
        self.btn_next_page.connect('clicked', self.go_next_page)
        self.page_left_evbox.connect('motion-notify-event', self.hover_on_aya)
        self.page_right_evbox.connect('motion-notify-event', self.hover_on_aya)
        self.page_left_evbox.connect('button-press-event', self.focus_on_aya)
        self.page_right_evbox.connect('button-press-event', self.focus_on_aya)
        self.page_left_drawarea.connect('draw', self.draw_on_aya)
        self.page_right_drawarea.connect('draw', self.draw_on_aya)
        self.popover_nav.spin_page_no.connect('value-changed', self.go_to_page)
        self.popover_nav.combo_sura_name.connect('changed', self.go_to_sura)
        self.popover_nav.spin_aya_no.connect('value-changed', self.go_to_aya)
        self.popover_nav.spin_juz_no.connect('value-changed', self.go_to_juz)
        # self.popover_nav.spin_hizb_no.connect('value-changed', self.go_to_hizb)
        self.popover_menu.btn_about.connect('clicked', self.show_about)
        self.btn_open_tarajem.connect('clicked', self.toggle_tarajem)
        self.popover_tarajem.listbox.connect('row-activated',
                                             self.select_tarajem)
        self.popover_tarajem.entry.connect('search-changed',
                                           self.filter_tarajem)
        self.box_musshaf.listbox.connect('row-activated',
                                         self.select_musshaf)
        self.box_musshaf.btn_ok.connect('clicked', self.show_musshaf)
        self.connect('key-press-event', self.on_key_press)
        self.connect('key-release-event', self.on_key_release)
        self.connect('focus-out-event', self.on_loses_focus)

        # Set widget behaviours
        self.btn_open_nav.set_popover(self.popover_nav)
        self.btn_open_more.set_popover(self.popover_menu)
        self.btn_tarajem_option.set_popover(self.popover_tarajem)
        self.main_overlay.add_overlay(self.toast_message)
        self.main_overlay.add_overlay(self.box_musshaf)

        # Populate static data
        # for musshaf
        # TODO: implements user-settings
        musshaf_dir = os.path.join(GLib.get_user_data_dir(),
                                   'grapik-quran/musshaf')
        if not os.path.isdir(musshaf_dir):
            os.makedirs(os.path.join(GLib.get_user_data_dir(),
                                     f'grapik-quran/musshaf'), exist_ok=True)
        for musshaf in self.model.get_musshafs():
            musshaf_id, musshaf_name = musshaf[:2]
            musshaf_desc = musshaf[4]
            row = Gtk.ListBoxRow()
            row.id = musshaf_id
            is_musshafdir_exist = os.path.isdir(os.path.join(musshaf_dir,
                                                             musshaf_id))
            is_musshafbbox_exist = self.model.check_musshaf(musshaf_id)
            row.is_downloaded = is_musshafdir_exist and is_musshafbbox_exist
            name_label = Gtk.Label()
            name_label.set_markup(f'<span weight="bold">{musshaf_name}</span>')
            name_label.set_halign(Gtk.Align.START)
            desc_label = Gtk.Label()
            desc_label.set_halign(Gtk.Align.START)
            desc_label.set_line_wrap(True)
            desc_label.set_markup('<span size="small" foreground="#cccccc">'
                              f'{musshaf_desc}</span>')
            desc_label.set_justify(Gtk.Justification.FILL)
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            vbox.pack_start(name_label, True, True, 0)
            vbox.pack_start(desc_label, True, True, 1)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            icon_name = ('object-select-symbolic' if row.is_downloaded else
                         'folder-download-symbolic')
            image = Gtk.Image.new_from_icon_name(icon_name,
                                                 Gtk.IconSize.BUTTON)
            image.set_margin_end(5)
            image.set_valign(Gtk.Align.START)
            hbox.pack_start(image, False, True, 0)
            hbox.pack_end(vbox, True, True, 0)
            if row.is_downloaded and musshaf_id != \
                    self.model.get_selected_musshaf:
                image.set_opacity(0)
            else:
                image.set_opacity(1)
            row.add(hbox)
            self.box_musshaf.listbox.add(row)

        # for surah names
        liststore = Gtk.ListStore(str, str)
        for sura in self.model.get_suras():
            sura_id = str(sura[0])
            liststore.append([sura_id, f'{sura_id}. {sura[5]}'])
            self.popover_nav.combo_sura_name.append(
                sura_id, f'{sura_id}. {sura[4]}')
        self.popover_nav.complete_sura_name.set_model(liststore)
        self.popover_nav.complete_sura_name.set_text_column(1)
        self.popover_nav.combo_sura_name.set_active_id(str(self.sura_no))

        def filter_surah(completion: Gtk.EntryCompletion, key: str,
                         iter: Gtk.TreeIter, *user_data) -> bool:
            suraname = completion.get_model()[iter][1]
            return key in suraname.lower()
        self.popover_nav.complete_sura_name.set_match_func(filter_surah, None)

        # for tarajem
        self.populate_tarajem()

        # if self.model.get_selected_musshaf():
        self.btn_tarajem_option.set_sensitive(False)
        self.btn_open_nav.set_sensitive(False)
        self.box_musshaf.listbox.show_all()
        self.is_welcome_opened = True

    def on_key_press(self, window: Gtk.Window, event: Gdk.EventKey) -> None:
        if event.keyval == Gdk.KEY_c and event.state == \
                Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD2_MASK:
            texts = ''
            bboxes = [(bbox[0], bbox[1]) for bbox
                      in self.bboxes_focused['page_right']]
            bboxes.extend([(bbox[0], bbox[1]) for bbox
                           in self.bboxes_focused['page_left']])
            uniques = set()  # for removing duplicate surah-ayah pairs
            bboxes = [x for x in bboxes if not (x in uniques or
                                                uniques.add(x))]
            for bbox in bboxes:
                texts += self.model.get_aya_text(*bbox[:2])
                texts += '\n'
            if texts:
                self.clipboard.set_text(texts, -1)
                self.toast_message.notify('Selected ayah(s) copied')

        if event.keyval == Gdk.KEY_Left:
            if self.page_no + 1 <= self.PAGE_NO_MAX:
                self.page_no += 1
                self.update('page')
        elif event.keyval == Gdk.KEY_Right:
            if self.page_no - 1 >= self.PAGE_NO_MIN:
                self.page_no -= 1
                self.update('page')
        # FIXME: unexpected window scrolling
        elif event.keyval == Gdk.KEY_Up:
            if self.aya_no - 1 == 0:
                if self.sura_no - 1 >= 1:
                    self.sura_no -= 1
                    self.SURA_LENGTH = self.model.get_sura_length(self.sura_no)
                    self.aya_no = self.SURA_LENGTH
                    self.update('aya')
            else:
                self.aya_no -= 1
                self.update('aya')
        elif event.keyval == Gdk.KEY_Down:
            if self.aya_no + 1 > self.SURA_LENGTH:
                if self.sura_no + 1 <= 114:
                    self.sura_no += 1
                    self.update('sura')
            else:
                self.aya_no += 1
                self.update('aya')
        elif event.keyval == Gdk.KEY_Shift_L:
            self.is_shift_pressed = True
            # FIXME: force hovering is not working anymore
            self.hover_on_aya(self.prev_page_focused, self.prev_mouse_event)

    def on_key_release(self, window: Gtk.Window, event: Gdk.EventKey) -> None:
        if event.keyval == Gdk.KEY_Shift_L:
            self.is_shift_pressed = False
            self.hover_on_aya(self.prev_page_focused, self.prev_mouse_event)

    def on_loses_focus(self, window: Gtk.Window, event: Gdk.EventFocus) -> None:
        self.is_shift_pressed = False

    def update(self, updated: str = None) -> None:
        if self.is_updating or self.is_welcome_opened:
            return

        # Sync other navigation variables
        is_page_no_updated = True
        prev_page_no = self.page_no
        if updated in ['page', '2page']:
            if updated == '2page' and self.page_no % 2 == 1:
                self.page_no -= 1
            self.sura_no = self.model.get_sura_no(self.page_no)
            self.aya_no = self.model.get_aya_no(self.page_no)
            self.juz_no = self.model.get_juz_no(self.sura_no, self.aya_no)
            self.hizb_no = self.model.get_hizb_no(self.sura_no, self.aya_no)
            self.SURA_LENGTH = self.model.get_sura_length(self.sura_no)
        elif updated == 'sura':
            self.aya_no = 1
            self.page_no = self.model.get_page_no(self.sura_no, self.aya_no)
            self.juz_no = self.model.get_juz_no(self.sura_no, self.aya_no)
            self.hizb_no = self.model.get_hizb_no(self.sura_no, self.aya_no)
            self.SURA_LENGTH = self.model.get_sura_length(self.sura_no)
        elif updated == 'aya':
            self.page_no = self.model.get_page_no(self.sura_no, self.aya_no)
            self.juz_no = self.model.get_juz_no(self.sura_no, self.aya_no)
            self.hizb_no = self.model.get_hizb_no(self.sura_no, self.aya_no)
        elif updated == 'juz':
            self.sura_no = self.model.get_sura_no(juz_no=self.juz_no)
            self.aya_no = self.model.get_aya_no(juz_no=self.juz_no)
            self.page_no = self.model.get_page_no(self.sura_no, self.aya_no)
            self.hizb_no = 1
            self.SURA_LENGTH = self.model.get_sura_length(self.sura_no)
        elif updated == 'hizb':
            ...
        elif updated == 'focus':
            self.page_no = self.model.get_page_no(self.sura_no, self.aya_no)
            self.juz_no = self.model.get_juz_no(self.sura_no, self.aya_no)
            self.hizb_no = self.model.get_hizb_no(self.sura_no, self.aya_no)
            self.SURA_LENGTH = self.model.get_sura_length(self.sura_no)

        # Always set even page numbers for right pages
        page_right_no = self.page_no
        if self.page_no % 2 == 1:
            page_right_no -= 1

        def set_image(page: Gtk.Image, page_no: int) -> None:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(
                    GLib.get_user_data_dir(), 'grapik-quran/musshaf/'
                    f'{self.model.get_selected_musshaf()}/{page_no}.png'),
                    round(self.PAGE_SIZE_WIDTH * self.PAGE_SCALE),
                    round(self.PAGE_SIZE_HEIGHT * self.PAGE_SCALE), True)
                page.set_from_pixbuf(pixbuf)
            except:
                pixbuf = GdkPixbuf.Pixbuf.new_from_resource_at_scale(
                    '/org/naruaika/Quran/res/img/page_null.png',
                    round(self.PAGE_SIZE_WIDTH * self.PAGE_SCALE),
                    round(self.PAGE_SIZE_HEIGHT * self.PAGE_SCALE), False)
                page.set_from_pixbuf(pixbuf)

        if self.page_no == prev_page_no and updated not in ['page', '2page']:
            is_page_no_updated = False

        if is_page_no_updated:
            # Set the image corresponding to each page
            set_image(self.page_right, page_right_no)
            set_image(self.page_left, page_right_no + 1)

            if self.is_tarajem_opened:
                is_pageno_odd = self.page_no % 2 == 1
                self.page_right_scroll.set_visible(is_pageno_odd)
                self.page_left_scroll.set_visible(not is_pageno_odd)

        self.is_updating = True

        # Sync navigation widget's attributes
        page_no = self.page_no - self.PAGE_NO_SHIFT + 1
        self.popover_nav.spin_page_no.set_value(page_no)
        if self.sura_no > 0:
            self.popover_nav.combo_sura_name.set_active_id(str(self.sura_no))
            self.popover_nav.adjust_aya_no.set_upper(self.SURA_LENGTH)
            self.popover_nav.spin_aya_no.set_value(self.aya_no)
            self.popover_nav.spin_juz_no.set_value(self.juz_no)
            self.popover_nav.spin_hizb_no.set_value(self.hizb_no)
            self.popover_nav.aya_length.set_text(f'({1}–'
                                                 f'{self.SURA_LENGTH})')
            sura_name = self.popover_nav.entry_sura_name.get_text()
            self.win_title.set_text(f'{sura_name.split()[1]} ({self.sura_no}) '
                                    f': {self.aya_no}')
        else:
            self.popover_nav.combo_sura_name.set_active_id('-1')
            self.popover_nav.adjust_aya_no.set_upper(-1)
            self.popover_nav.spin_aya_no.set_value(-1)
            self.popover_nav.spin_juz_no.set_value(-1)
            self.popover_nav.spin_hizb_no.set_value(-1)
            self.popover_nav.aya_length.set_text('')
            self.win_title.set_text('Quran')
        self.btn_back_page.set_visible(self.page_no > self.PAGE_NO_MIN)
        self.btn_next_page.set_visible(self.page_no < self.PAGE_NO_MAX)

        self.is_updating = False

        # Get all bounding box for the new two pages
        self.bboxes['page_right'] = self.model.get_bboxes(page_right_no)
        self.bboxes['page_left'] = self.model.get_bboxes(page_right_no + 1)

        # Get a new aya focus
        self.bboxes_focused['page_right'] = []
        self.bboxes_focused['page_left'] = []
        if updated == 'focus':
            self.bboxes_focused = copy.deepcopy(self.bboxes_hovered)
        else:
            page_id = ('page_left' if self.page_no % 2 == 1 else 'page_right')
            bboxes = self.bboxes[page_id]
            self.bboxes_focused[page_id] = [bbox for bbox in bboxes if bbox[:2]
                                            == (self.sura_no, self.aya_no)]
        self.page_right_drawarea.queue_draw()
        self.page_left_drawarea.queue_draw()

        self.update_tarajem(is_page_no_updated, False)

    def update_tarajem(self, content_changed: bool = True,
                       open_panel: bool = True) -> None:
        if content_changed:
            # Clear previous translations
            self.page_right_listbox.foreach(lambda x:
                self.page_right_listbox.remove(x))
            self.page_left_listbox.foreach(lambda x:
                self.page_left_listbox.remove(x))

        if not self.model.get_selected_tarajem():
            return
        if open_panel:
            self.btn_open_tarajem.set_active(True)  # trigger a click to open
                                                    # tarajem panel

        # Obtain surah-ayah number of the current page accordingly
        page_id = ('page_left' if self.page_no % 2 == 1 else 'page_right')
        bboxes = [bbox[:2] for bbox in self.bboxes[page_id]]
        uniques = set()  # for removing duplicate surah-ayah pairs
        bboxes = [x for x in bboxes if not (x in uniques or uniques.add(x))]

        # Obtain translations
        listbox = (self.page_right_listbox if page_id == 'page_left' else
                   self.page_left_listbox)
        bboxes_focused = [bbox[:2] for bbox in self.bboxes_focused[page_id]]
        was_scrolled = False
        for idx_bbox, bbox in enumerate(bboxes):
            if content_changed:
                row = Gtk.ListBoxRow()
                row.set_can_focus(False)
                hbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                label = Gtk.Label(
                    label=f'{self.model.get_sura_name(bbox[0])} '
                    f'({bbox[0]}) : {bbox[1]}', xalign=0)
                label.set_can_focus(False)
                hbox.pack_start(label, True, True, 0)

                for tid in self.model.get_selected_tarajem():
                    textview = Gtk.TextView()
                    textview.set_editable(False)
                    textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR )
                    textview.set_can_focus(False)
                    textview.set_hexpand(True)
                    tarajem = self.model.get_tarajem(tid)
                    translator = tarajem[1]
                    language = tarajem[2].title()
                    markup = '<span foreground="#444444" size="small">' \
                        f'{language} - {translator}</span>\n<span ' \
                        'size="medium">' \
                        f'{self.model.get_tarajem_text(tid, *bbox[:2])[2]}' \
                        '</span>'
                    buffer = Gtk.TextBuffer()
                    buffer.insert_markup(buffer.get_start_iter(), markup, -1)
                    textview.set_buffer(buffer)
                    hbox.pack_start(textview, True, True, 1)
                row.add(hbox)
                listbox.add(row)

            if bbox in bboxes_focused:
                listbox.get_row_at_index(idx_bbox).set_name('row-focused')
                if not was_scrolled:
                    self.prev_card_focused = listbox.get_row_at_index(idx_bbox)
                    was_scrolled = True
            else:
                listbox.get_row_at_index(idx_bbox).set_name('row')

        # TODO: needs a better solution
        scrollwindow = (self.page_right_scroll if self.page_no % 2 == 1
                        else self.page_left_scroll)
        GLib.timeout_add(50, self.animate_scroll_to, scrollwindow,
                         self.prev_card_focused)

        # Display new translations
        self.page_left_listbox.show_all()
        self.page_right_listbox.show_all()

    def toggle_tarajem(self, button: Gtk.Button) -> None:
        self.is_tarajem_opened = button.get_active()
        if self.is_tarajem_opened:
            is_pageno_odd = self.page_no % 2 == 1
            self.page_right_scroll.set_visible(is_pageno_odd)
            self.page_left_scroll.set_visible(not is_pageno_odd)
        else:
            self.page_right_scroll.set_visible(False)
            self.page_left_scroll.set_visible(False)

    def populate_tarajem(self, query: str = '') -> None:
        if query:
            tarajem_filtered = [meta for meta in self.model.get_tarajems()
                                if query.lower() in meta[1].lower() or
                                query.lower() in meta[2]]
            if self.tarajem_filtered == tarajem_filtered:
                return
            self.tarajem_filtered = tarajem_filtered
        else:
            self.tarajem_filtered = self.model.get_tarajems()

        self.popover_tarajem.listbox.foreach(lambda x:
            self.popover_tarajem.listbox.remove(x))
        selected_tarajem = self.model.get_selected_tarajem()
        for tarajem in self.tarajem_filtered:
            tarajem_id, translator = tarajem[:2]
            language = tarajem[2].title()
            row = Gtk.ListBoxRow()
            row.id = tarajem_id
            row.is_downloaded = self.model.check_tarajem(tarajem_id)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            label = Gtk.Label(label=f'{language} - {translator}', xalign=0)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            icon_name = ('object-select-symbolic' if row.is_downloaded else
                         'folder-download-symbolic')
            image = Gtk.Image.new_from_icon_name(icon_name,
                                                 Gtk.IconSize.BUTTON)
            image.set_halign(Gtk.Align.END)
            image.set_margin_start(5)
            image.set_no_show_all(True)
            if row.is_downloaded and tarajem_id not in selected_tarajem:
                image.hide()
            else:
                image.show()
            hbox.pack_start(label, True, True, 0)
            hbox.pack_start(image, True, True, 1)
            row.add(hbox)
            self.popover_tarajem.listbox.add(row)
        self.popover_tarajem.listbox.show_all()

    def filter_tarajem(self, entry: Gtk.SearchEntry) -> None:
        query = entry.get_text()
        self.populate_tarajem(query)

    def select_tarajem(self, box: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        # TODO: allow multiple downloading at the same time
        # FIXME: freeze when enabling a tarajem while dowloading another
        if self.is_downloading:
            return

        container = row.get_child()
        ic_selected = container.get_children()[1]

        if not row.is_downloaded:
            self.is_downloading = True

            ic_selected.hide()
            spinner = Gtk.Spinner()
            spinner.set_halign(Gtk.Align.END)
            spinner.set_margin_start(5)
            container.pack_end(spinner, True, True, 0)
            container.show_all()
            spinner.start()

            # TODO: enable a tarajem after downloading automatically
            def add_tarajem():
                progressbar = self.popover_tarajem.progressbar
                progressbar.show()
                if ResourceManager.add_tarajem(row.id, progressbar):
                    row.is_downloaded = True
                    ic_selected.set_from_icon_name('object-select-symbolic',
                                                   Gtk.IconSize.BUTTON)
                container.remove(spinner)
                progressbar.hide()
                progressbar.set_fraction(0)
                self.is_downloading = False

            Thread(target=add_tarajem).start()
        else:
            ic_selected.set_visible(
                row.id not in self.model.get_selected_tarajem())
            self.model.update_selected_tarajem(row.id)
            self.update_tarajem()

    def select_musshaf(self, box: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if self.is_downloading:
            return

        container = row.get_child()
        ic_selected = container.get_children()[0]

        if not row.is_downloaded:
            self.is_downloading = True

            spinner = Gtk.Spinner()
            spinner.set_margin_end(5)
            spinner.set_valign(Gtk.Align.START)
            container.remove(ic_selected)
            container.pack_start(spinner, False, True, 0)
            container.show_all()
            spinner.start()

            def add_musshaf() -> None:
                progressbar = self.box_musshaf.progressbar
                progressbar.set_opacity(1)
                if ResourceManager.add_musshaf(row.id, progressbar):
                    row.is_downloaded = True
                    ic_selected.set_from_icon_name('object-select-symbolic',
                                                   Gtk.IconSize.BUTTON)
                    ic_selected.set_opacity(0)
                container.remove(spinner)
                container.pack_start(ic_selected, False, True, 0)
                progressbar.set_opacity(0)
                progressbar.set_fraction(0)
                self.is_downloading = False

            Thread(target=add_musshaf).start()
        else:
            if self.model.get_selected_musshaf == row.id:
                return

            def uncheck_all(row) -> None:
                if row.is_downloaded:
                    container = row.get_children()[0]
                    icon = container.get_children()[0]
                    icon.set_opacity(0)

            box.foreach(uncheck_all)

            ic_selected.set_opacity(1)
            self.model.update_selected_musshaf(row.id)
            self.box_musshaf.btn_ok.set_sensitive(True)

    def go_previous_page(self, button: Gtk.Button) -> None:
        page_increment = (1 if self.is_tarajem_opened else 2)
        self.page_no = max(self.page_no - page_increment, self.PAGE_NO_MIN)
        self.update('page' if self.is_tarajem_opened else '2page')

    def go_next_page(self, button: Gtk.Button) -> None:
        page_increment = (1 if self.is_tarajem_opened else 2)
        self.page_no = min(self.page_no + page_increment, self.PAGE_NO_MAX)
        self.update('page' if self.is_tarajem_opened else '2page')

    def go_to_page(self, button: Gtk.SpinButton) -> None:
        self.page_no = int(button.get_value()) + self.PAGE_NO_SHIFT - 1
        self.update('page')

    def go_to_sura(self, box: Gtk.ComboBoxText) -> None:
        text = box.get_child().get_text()
        if len(text) < 3:
            return
        # print(text)
        try:
            self.sura_no = int(text.split('.')[0])
            self.update('sura')
        except:
            return

    def go_to_aya(self, button: Gtk.SpinButton) -> None:
        self.aya_no = int(button.get_value())
        self.update('aya')

    def go_to_juz(self, button: Gtk.SpinButton) -> None:
        self.juz_no = int(button.get_value())
        self.update('juz')

    # TODO: add navigation to a specific hizb and ruku
    # def go_to_hizb(self, button: Gtk.SpinButton) -> None:
    #     self.hizb_no = int(button.get_value())
    #     self.update('hizb')

    def hover_on_aya(self, widget: Gtk.Widget, event: Gdk.EventMotion) -> None:
        if not widget or not event:
            return

        # Save parameters only for the purpose of forcing update hovering
        self.prev_page_focused = widget
        self.prev_mouse_event = event

        # Find the sura-aya under the cursor
        suraya_hovered = None
        pageid_hovered = widget.get_name()
        page_bboxes = self.bboxes[pageid_hovered]
        for bbox in page_bboxes:
            if bbox[2] <= event.x <= bbox[2] + bbox[4] and \
                    bbox[3] <= event.y <= bbox[3] + bbox[5]:
                suraya_hovered = bbox[:2]
                break

        self.bboxes_hovered['page_right'] = []
        self.bboxes_hovered['page_left'] = []

        if suraya_hovered:
            if self.is_shift_pressed:  # for multiple surah-ayah selections
                suraya_candidates = [suraya_hovered]
                suraya_candidates += \
                    [bbox[:2] for bbox in self.bboxes_focused['page_right']]
                suraya_candidates += \
                    [bbox[:2] for bbox in self.bboxes_focused['page_left']]
                suraya_start = min(suraya_candidates)
                suraya_end = max(suraya_candidates)
                self.bboxes_hovered['page_right'] = \
                    [bbox for bbox in self.bboxes['page_right']
                        if suraya_start <= bbox[:2] <= suraya_end]
                self.bboxes_hovered['page_left'] = \
                    [bbox for bbox in self.bboxes['page_left']
                        if suraya_start <= bbox[:2] <= suraya_end]
            else:
                self.bboxes_hovered[pageid_hovered] = \
                    [bbox for bbox in page_bboxes if bbox[:2]
                     == suraya_hovered]

        # Draw bounding boxes over hovered aya(s) in tarajem viewer
        listbox = (self.page_right_listbox if self.page_no % 2 == 1 else
                   self.page_left_listbox)
        scrollwindow = (self.page_right_scroll if self.page_no % 2 == 1
                        else self.page_left_scroll)
        for row in listbox:
            if row.get_name() == 'row-hovered':
                row.set_name('row')
        if self.is_tarajem_opened and self.model.get_selected_tarajem():
            if suraya_hovered:
                for bbox in self.bboxes_hovered[pageid_hovered]:
                    # TODO: optimise by setting metadata to listboxrow
                    row = listbox.get_row_at_index(self.model.get_suraya_seq(
                        *bbox[:2]) - 1)
                    if row.get_name() != 'row-focused':
                        row.set_name('row-hovered')
                    if suraya_hovered == bbox[:2]:
                        self.animate_scroll_to(scrollwindow, row)
            else:
                self.animate_scroll_to(scrollwindow, self.prev_card_focused)

        # Draw bounding boxes over hovered aya(s) in page viewer
        self.page_right_drawarea.queue_draw()
        self.page_left_drawarea.queue_draw()

    def focus_on_aya(self, widget: Gtk.Widget, event: Gdk.EventButton) -> None:
        page_id = widget.get_name()
        if self.bboxes_hovered[page_id]:
            first_bbox = self.bboxes_hovered[page_id][0]
            self.sura_no = first_bbox[0]
            self.aya_no = first_bbox[1]
            self.update('focus')

    def draw_on_aya(self, widget: Gtk.Widget, context: cairo.Context) -> None:
        page_id = widget.get_name()
        if self.bboxes_focused[page_id]:  # draw focus
            context.set_source_rgba(0.082, 0.325, 0.620, 0.2)
            for bbox in self.bboxes_focused[page_id]:
                context.rectangle(*bbox[2:])
            context.fill()

        if self.bboxes_hovered[page_id] and \
                self.bboxes_hovered[page_id] != \
                    self.bboxes_focused[page_id]:  # draw hover
            context.set_source_rgba(0.2, 0.2, 0.2, 0.075)
            for bbox in self.bboxes_hovered[page_id]:
                if bbox in self.bboxes_focused[page_id]:
                    continue
                context.rectangle(*bbox[2:])
            context.fill()

    # FIXME: it's too heavy on shift key pressed while hovering
    def animate_scroll_to(self, window: Gtk.ScrolledWindow,
                          widget: Gtk.Widget) -> None:
        to = widget.get_allocation()
        adjustment = window.get_vadjustment()
        start = adjustment.get_value()

        if start <= to.y and to.y + to.height <= \
                start + adjustment.get_page_size():
            return
        else:
            if to.y > start:
                if to.height > adjustment.get_page_size():
                    end = to.y
                else:
                    end = min(adjustment.get_upper() -
                            adjustment.get_page_size(), to.y + to.height -
                            adjustment.get_page_size())
            else:
                end = to.y
            self.prev_scroll_y = end

        clock = window.get_frame_clock()
        duration = 600  # in millisecond
        start_time = clock.get_frame_time()
        end_time = start_time + 1000 * duration

        def scroll(widget: Gtk.Widget, frame_clock: Gdk.FrameClock) -> bool:
            if self.prev_scroll_y != end:
                return GLib.SOURCE_REMOVE

            now = clock.get_frame_time()

            def ease_out_cubic(t) -> float:
                p = t - 1
                return p * p * p + 1

            if now < end_time and adjustment.get_value() != end:
                t = (now - start_time) / (end_time - start_time)
                t = ease_out_cubic(t)
                adjustment.set_value(start + t * (end - start))
                return GLib.SOURCE_CONTINUE
            else:
                adjustment.set_value(end)
                return GLib.SOURCE_REMOVE

        window.add_tick_callback(scroll)

    def show_musshaf(self, button: Gtk.Button) -> None:
        self.is_welcome_opened = False

        self.main_overlay.remove(self.box_musshaf)
        self.musshaf_viewer.show()
        self.box_navbar.show()

        self.btn_open_tarajem.set_sensitive(True)
        self.btn_tarajem_option.set_sensitive(True)
        self.btn_open_nav.set_sensitive(True)

        musshaf_dir = os.path.join(
            GLib.get_user_data_dir(),
            f'grapik-quran/musshaf/{self.model.get_selected_musshaf()}')

        self.PAGE_NO_SHIFT = self.model.get_page_no(1, 1)
        self.PAGE_NO_MAX = len(os.listdir(musshaf_dir))
        self.popover_nav.page_length.set_text(
            f'({self.PAGE_NO_MIN}–'
            f'{self.model.get_page_no(114, 1) - self.PAGE_NO_SHIFT + 1})')
        self.popover_nav.adjust_page_no.set_upper(self.PAGE_NO_MAX -
                                                  self.PAGE_NO_SHIFT + 1)
        self.popover_nav.adjust_page_no.set_lower(self.PAGE_NO_MIN -
                                                  self.PAGE_NO_SHIFT + 1)

        page = GdkPixbuf.Pixbuf.new_from_file(os.path.join(
            musshaf_dir, '1.png'))
        self.PAGE_SIZE_WIDTH = page.get_width()
        self.PAGE_SIZE_HEIGHT = page.get_height()

        self.update('sura')

    def show_about(self, button: Gtk.Button) -> None:
        dialog = AboutDialog()
        dialog.set_transient_for(self)
        dialog.show_all()
