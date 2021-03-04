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
import cairo
import copy

from .model import Model
from .dialog import About
from .popover import Navigation, Help
from .revealer import Message


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

    page_no: int = -1
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

    model = Model()
    popover_help = Help()
    popover_nav = Navigation()
    toast_message = Message()

    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    on_update: bool = False  # to stop unwanted signal triggering
    is_shift_pressed = False
    is_transpanel_opened = False

    btn_open_menu = Gtk.Template.Child('btn_open_menu')
    btn_open_nav = Gtk.Template.Child('btn_open_nav')
    btn_back_page = Gtk.Template.Child('btn_back_page')
    btn_next_page = Gtk.Template.Child('btn_next_page')
    btn_trans_toggle = Gtk.Template.Child('btn_trans_toggle')
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
    win_title = Gtk.Template.Child('win_title')
    main_overlay = Gtk.Template.Child('main_overlay')

    _tmp_widget = None
    _tmp_event = None

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
        self.btn_trans_toggle.connect('clicked', self.toggle_translation_panel)
        self.page_left_evbox.connect('motion-notify-event', self.page_hovered)
        self.page_right_evbox.connect('motion-notify-event', self.page_hovered)
        self.page_left_evbox.connect('button-press-event', self.focus_on_aya)
        self.page_right_evbox.connect('button-press-event', self.focus_on_aya)
        self.page_left_drawarea.connect('draw', self.draw_bbox)
        self.page_right_drawarea.connect('draw', self.draw_bbox)
        self.popover_nav.spin_page_no.connect('value-changed', self.go_to_page)
        self.popover_nav.combo_sura_name.connect('changed', self.go_to_sura)
        self.popover_nav.spin_aya_no.connect('value-changed', self.go_to_aya)
        self.popover_nav.spin_juz_no.connect('value-changed', self.go_to_juz)
        # self.popover_nav.spin_hizb_no.connect('value-changed', self.go_to_hizb)
        self.popover_help.btn_about.connect('clicked', self.show_about)
        self.connect('key-press-event', self.on_key_press)
        self.connect('key-release-event', self.on_key_release)

        self.btn_open_menu.set_popover(self.popover_help)
        self.btn_open_nav.set_popover(self.popover_nav)

        # Set default views
        for sura in self.model.get_suras():
            sura_id = str(sura[0])
            sura_name = f'{sura_id}. {sura[4]}'
            self.popover_nav.combo_sura_name.append(sura_id, sura_name)
        self.popover_nav.page_length.set_text(f'({self.PAGE_NO_MIN}–'
                                              f'{self.PAGE_NO_MAX})')
        self.main_overlay.add_overlay(self.toast_message)

        # TODO: get last read page
        self.popover_nav.combo_sura_name.set_active_id(str(self.sura_no))

    def on_key_press(self, window: Gtk.Window, event: Gdk.EventKey) -> None:
        keyname = Gdk.keyval_name(event.keyval)
        if Gdk.ModifierType.CONTROL_MASK and keyname == 'c':
            texts = ''
            bboxes = [(bbox[0], bbox[1]) for bbox
                      in self.bboxes_focused['page_right']]
            bboxes.extend([(bbox[0], bbox[1]) for bbox
                           in self.bboxes_focused['page_left']])
            uniques = set()  # for removing duplicate surah-ayah pairs
            bboxes = [x for x in bboxes if not (x in uniques or uniques.add(x))]
            for bbox in bboxes:
                texts += self.model.get_aya_text(*bbox[:2])
                texts += '\n'
            if texts:
                self.clipboard.set_text(texts, -1)
                self.toast_message.notify('Selected ayah(s) copied')
        if Gdk.ModifierType.SHIFT_MASK:
            self.is_shift_pressed = True
            self.page_hovered(self._tmp_widget, self._tmp_event)

    def on_key_release(self, window: Gtk.Window, event: Gdk.EventKey) -> None:
        if Gdk.ModifierType.SHIFT_MASK:
            self.is_shift_pressed = False
            self.page_hovered(self._tmp_widget, self._tmp_event)

    def update(self, updated: str = None) -> None:
        if self.on_update:
            return

        # Sync other navigation variables
        is_page_no_updated = True
        prev_page_no = self.page_no
        if updated in ['page', '2page']:
            if updated == '2page' and self.page_no % 2 == 0:
                self.page_no -= 1
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
            self.sura_no = self.model.get_sura_no_by_juz(self.juz_no)
            self.aya_no = self.model.get_aya_no_by_juz(self.juz_no)
            self.page_no = self.model.get_page_no(self.sura_no, self.aya_no)
            self.hizb_no = self.HIZB_NO_MIN
            self.AYA_NO_MAX = self.model.get_aya_no_max(self.sura_no)
        elif updated == 'hizb':
            ...
        elif updated == 'focus':
            self.page_no = self.model.get_page_no(self.sura_no, self.aya_no)
            self.juz_no = self.model.get_juz_no(self.sura_no, self.aya_no)
            self.hizb_no = self.model.get_hizb_no(self.sura_no, self.aya_no)
            self.AYA_NO_MAX = self.model.get_aya_no_max(self.sura_no)
        if self.page_no == prev_page_no and updated not in ['page', '2page']:
            is_page_no_updated = False

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

        if is_page_no_updated:
            # Set the image corresponding to each page
            set_image(self.page_right, page_right_no)
            set_image(self.page_left, page_right_no + 1)

            if self.is_transpanel_opened:
                if self.page_no % 2 == 0:
                    self.page_right_scroll.set_visible(True)
                    self.page_left_scroll.set_visible(False)
                else:
                    self.page_right_scroll.set_visible(False)
                    self.page_left_scroll.set_visible(True)

        self.on_update = True

        # Sync navigation widget's attributes
        self.popover_nav.spin_page_no.set_value(self.page_no)
        self.popover_nav.combo_sura_name.set_active_id(str(self.sura_no))
        self.popover_nav.adjust_aya_no.set_upper(self.AYA_NO_MAX)
        self.popover_nav.spin_aya_no.set_value(self.aya_no)
        self.popover_nav.spin_juz_no.set_value(self.juz_no)
        self.popover_nav.spin_hizb_no.set_value(self.hizb_no)
        self.popover_nav.aya_length.set_text(f'({self.AYA_NO_MIN}–'
                                             f'{self.AYA_NO_MAX})')
        sura_name = self.popover_nav.combo_sura_name.get_active_text()
        self.win_title.set_text(f'{sura_name.split()[1]} ({self.sura_no}) : '
                                f'{self.aya_no}')
        self.btn_back_page.set_visible(self.page_no > self.PAGE_NO_MIN)
        self.btn_next_page.set_visible(self.page_no < self.PAGE_NO_MAX)

        self.on_update = False

        # Get all bounding box for the new two pages
        self.bboxes['page_right'] = self.model.get_bboxes_by_page(page_right_no)
        self.bboxes['page_left'] = \
            self.model.get_bboxes_by_page(page_right_no + 1)

        # Get a new aya focus
        self.bboxes_focused['page_right'] = []
        self.bboxes_focused['page_left'] = []
        if updated == 'focus':
            self.bboxes_focused = copy.deepcopy(self.bboxes_hovered)
        else:
            page_id = ('page_left' if self.page_no % 2 == 0 else 'page_right')
            bboxes = self.bboxes[page_id]
            self.bboxes_focused[page_id] = [bbox for bbox in bboxes
                                            if bbox[1] == self.aya_no]
        self.page_right_drawarea.queue_draw()
        self.page_left_drawarea.queue_draw()

        if self.is_transpanel_opened:
            if is_page_no_updated:
                self.update_translation()
            else:
                self.update_translation(False)

    def update_translation(self, page_changed: bool = True) -> None:
        if page_changed:
            # Clear previous translations
            self.page_right_listbox.foreach(lambda x:
                self.page_right_listbox.remove(x))
            self.page_left_listbox.foreach(lambda x:
                self.page_left_listbox.remove(x))

        # Obtain surah-ayah number of the current page accordingly
        page_id = ('page_left' if self.page_no % 2 == 0 else 'page_right')
        bboxes = [(bbox[0], bbox[1]) for bbox in self.bboxes[page_id]]
        uniques = set()  # for removing duplicate surah-ayah pairs
        bboxes = [x for x in bboxes if not (x in uniques or uniques.add(x))]

        bboxes_focused = [(bbox[0], bbox[1]) for bbox in
                          self.bboxes_focused[page_id]]

        if page_id == 'page_left':
            listbox = self.page_right_listbox
        else:
            listbox = self.page_left_listbox

        # Obtain translations
        for idx_bbox, bbox in enumerate(bboxes):
            if page_changed:
                row = Gtk.ListBoxRow()
                row.set_can_focus(False)
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                label = Gtk.Label()
                markup = f'<span foreground="#555555"><i><small>' \
                    f'{self.model.get_sura_name_by_no(bbox[0])} ' \
                    f'({bbox[0]}): {bbox[1]}</small></i></span>\n'
                markup += self.model.get_translation_text(*bbox[:2])[2]
                label.set_markup(markup)
                label.set_line_wrap(True)
                label.set_selectable(True)
                label.set_justify(Gtk.Justification.FILL)
                label.set_halign(Gtk.Align.START)

                row.add(label)
                hbox.pack_start(label, True, True, 0)
                listbox.add(row)

            if bbox in bboxes_focused:
                listbox.get_row_at_index(idx_bbox).set_name('row-focused')
            else:
                listbox.get_row_at_index(idx_bbox).set_name('row')

        # Display new translations
        self.page_left_listbox.show_all()
        self.page_right_listbox.show_all()

    def go_previous_page(self, button: Gtk.Button) -> None:
        page_increment = (1 if self.is_transpanel_opened else 2)
        self.page_no = max(self.page_no - page_increment, self.PAGE_NO_MIN)
        self.update('page' if self.is_transpanel_opened else '2page')

    def go_next_page(self, button: Gtk.Button) -> None:
        page_increment = (1 if self.is_transpanel_opened else 2)
        self.page_no = min(self.page_no + page_increment, self.PAGE_NO_MAX)
        self.update('page' if self.is_transpanel_opened else '2page')

    def toggle_translation_panel(self, button: Gtk.Button) -> None:
        self.is_transpanel_opened = button.get_active()
        if self.is_transpanel_opened:
            if self.page_no % 2 == 0:
                self.page_right_scroll.set_visible(True)
                self.page_left_scroll.set_visible(False)
            else:
                self.page_right_scroll.set_visible(False)
                self.page_left_scroll.set_visible(True)
            self.update_translation()
        else:
            self.page_right_scroll.set_visible(False)
            self.page_left_scroll.set_visible(False)

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

    def page_hovered(self, widget: Gtk.Widget, event: Gdk.EventMotion) -> None:
        self._tmp_widget = widget
        self._tmp_event = event.copy()

        ayano_hovered = None
        page_id = widget.get_name()
        curr_page_bboxes = self.bboxes[page_id]
        for bbox in curr_page_bboxes:
            if bbox[3] <= event.x <= bbox[3] + bbox[5] and \
                    bbox[4] <= event.y <= bbox[4] + bbox[6]:
                ayano_hovered = bbox[1]
                break
        self.bboxes_hovered['page_right'] = []
        self.bboxes_hovered['page_left'] = []
        if ayano_hovered:
            if self.is_shift_pressed:
                if self.bboxes_focused['page_right'] and page_id == 'page_left':
                    self.bboxes_hovered['page_right'] = \
                        [bbox for bbox in self.bboxes['page_right']
                         if self.bboxes_focused['page_right'][0][1] <= bbox[1]]
                    self.bboxes_hovered['page_left'] = \
                        [bbox for bbox in curr_page_bboxes
                         if bbox[1] <= ayano_hovered]
                else:
                    try:
                        self.bboxes_hovered[page_id] = \
                            [bbox for bbox in curr_page_bboxes
                            if self.bboxes_focused[page_id][0][1] <= bbox[1]
                            <= ayano_hovered]
                    except:
                        ...
            else:
                self.bboxes_hovered[page_id] = \
                    [bbox for bbox in curr_page_bboxes
                     if bbox[1] == ayano_hovered]
            self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))
        else:
            self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.ARROW))
        self.page_right_drawarea.queue_draw()
        self.page_left_drawarea.queue_draw()

    def focus_on_aya(self, widget: Gtk.Widget, event: Gdk.EventButton) -> None:
        page_id = widget.get_name()
        if self.bboxes_hovered[page_id]:
            first_bbox = self.bboxes_hovered[page_id][-1]
            self.sura_no = first_bbox[0]
            self.aya_no = first_bbox[1]
            self.update('focus')

    def draw_bbox(self, widget: Gtk.Widget, context: cairo.Context) -> None:
        page_id = widget.get_name()
        if self.bboxes_focused[page_id]:
            context.set_source_rgba(0.082, 0.325, 0.620, 0.2)
            for bbox in self.bboxes_focused[page_id]:
                context.rectangle(*bbox[3:])
            context.fill()

        if self.bboxes_hovered[page_id] and \
                self.bboxes_hovered[page_id] != \
                    self.bboxes_focused[page_id]:
            context.set_source_rgba(0.2, 0.2, 0.2, 0.075)
            for bbox in self.bboxes_hovered[page_id]:
                if bbox in self.bboxes_focused[page_id]:
                    continue
                context.rectangle(*bbox[3:])
            context.fill()

    def show_about(self, button: Gtk.Button) -> None:
        # TODO: modal has to be attached to the main window
        About().show_all()
