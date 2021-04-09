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

from copy import deepcopy
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GdkPixbuf
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gst
from gi.repository import Gtk
from gi.repository import Handy
from os import path
from threading import Timer
from typing import List

from . import constants as const
from . import globals as glob
from .animation import Animation
from .headerbar import HeaderBar
from .musshaf import MusshafViewer
from .tarajem import TarajemViewer
from .telaawa import TelaawaPlayer


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/window.ui')
class MainWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'MainWindow'

    __gsignals__ = {
        'notify-requested': (GObject.SIGNAL_RUN_LAST, None, (str,))}

    Handy.init()

    main_container = Gtk.Template.Child()
    main_paned = Gtk.Template.Child()
    main_overlay = Gtk.Template.Child()
    buttonbox_navigation = Gtk.Template.Child()
    button_next_page = Gtk.Template.Child()
    button_previous_page = Gtk.Template.Child()

    status_loading = Gtk.Template.Child()
    loading_spinner = Gtk.Template.Child()
    loading_message = Gtk.Template.Child()
    revealer_notification = Gtk.Template.Child()
    notification_icon = Gtk.Template.Child()
    notification_message = Gtk.Template.Child()

    # To remember the previous value of application variables for deciding
    # which child widget to reload
    show_tarajem: bool = False
    surah_number: int = None
    ayah_number: int = None
    page_number: int = None
    page_focused: int = None
    tarajem_names: List = None

    timer_buttonnav: Timer = None

    def __init__(
            self,
            **kwargs) -> None:
        super().__init__(**kwargs)

        # Set the window application name identifier, so it can be recognized
        # by the user in the desktop application switcher
        self.set_title(const.APPLICATION_NAME)
        self.set_wmclass(const.APPLICATION_NAME, const.APPLICATION_NAME)

        # FIXME: the application icon appears too small
        self.set_default_icon_name(const.APPLICATION_ID)

        self.setup_headerbar()
        self.setup_musshaf_viewer()
        self.setup_tarajem_viewer()

        self.show_all()

        self.setup_window_size()

        # Init self variables
        self.surah_number = glob.surah_number
        self.ayah_number = glob.ayah_number

        # Init children states
        self.musshaf_viewer_right.update()
        self.musshaf_viewer_left.update()
        self.headerbar.popover_tarajem.populate()
        self.headerbar.popover_telaawa.populate()
        self.headerbar.popover_nav.update()
        self.headerbar.popover_nav_alt.update()

        self.headerbar.button_open_tarajem.set_active(glob.show_tarajem)

        # Setup a timer for show/hiding overlay widgets
        self.timer_buttonnav = Timer(2.0, self.hide_buttonnav)
        self.timer_buttonnav.start()

    def setup_headerbar(self) -> None:
        self.headerbar = HeaderBar()
        self.main_container.pack_start(self.headerbar, False, True, 0)

        self.headerbar.connect('tarajem-toggled', self.reload_tarajem_viewer)
        self.headerbar.connect(
            'mobileview-toggled', self.reload_navigation_panel)

        self.headerbar.popover_tarajem.connect(
            'tarajem-names-updated', self.reload_tarajem_viewer)
        self.headerbar.popover_telaawa.connect(
            'go-to-next-ayah', self.headerbar.popover_nav.go_to_next_ayah)
        self.headerbar.popover_telaawa.connect(
            'go-to-previous-ayah',
            self.headerbar.popover_nav.go_to_previous_ayah)

        self.headerbar.popover_telaawa.connect(
            'go-to-next-ayah', self.headerbar.popover_nav_alt.go_to_next_ayah)
        self.headerbar.popover_telaawa.connect(
            'go-to-previous-ayah',
            self.headerbar.popover_nav_alt.go_to_previous_ayah)

        self.button_next_page.connect(
            'clicked', self.headerbar.popover_nav.go_to_next_page)
        self.button_previous_page.connect(
            'clicked', self.headerbar.popover_nav.go_to_previous_page)

        self.button_next_page.connect(
            'clicked', self.headerbar.popover_nav_alt.go_to_next_page)
        self.button_previous_page.connect(
            'clicked', self.headerbar.popover_nav_alt.go_to_previous_page)

        self.headerbar.popover_menu.connect('page-scaled', self.resize_musshaf)
        self.headerbar.popover_menu.connect(
            'dualpage-toggled', self.toggle_dualpage)

    def setup_musshaf_viewer(self) -> None:
        self.musshaf_viewer_right = MusshafViewer(0)
        self.main_paned.pack_end(self.musshaf_viewer_right, True, True, 0)
        self.musshaf_viewer_right.image.set_halign(Gtk.Align.START)
        self.musshaf_viewer_right.eventbox.set_halign(Gtk.Align.START)

        self.musshaf_viewer_left = MusshafViewer(1)
        self.musshaf_viewer_left.image.set_halign(Gtk.Align.END)
        self.musshaf_viewer_left.eventbox.set_halign(Gtk.Align.END)
        self.main_paned.pack_start(self.musshaf_viewer_left, True, True, 0)

        self.headerbar.popover_nav.connect(
            'reload-musshaf-viewer', self.reload_musshaf_viewer)
        self.headerbar.popover_nav.connect(
            'reload-tarajem-viewer', self.reload_tarajem_viewer)
        self.headerbar.popover_nav.connect(
            'reload-telaawa-player', self.reload_telaawa_player)

        self.headerbar.popover_nav_alt.connect(
            'reload-musshaf-viewer', self.reload_musshaf_viewer)
        self.headerbar.popover_nav_alt.connect(
            'reload-tarajem-viewer', self.reload_tarajem_viewer)

        self.musshaf_viewer_right.connect(
            'selected-ayah-changed', self.reload_navigation_panel)
        self.musshaf_viewer_right.connect(
            'hovered-ayah-changed', self.reload_tarajem_viewer)
        self.musshaf_viewer_right.connect(
            'focused-page-changed', self.reload_tarajem_viewer)

        self.musshaf_viewer_left.connect(
            'selected-ayah-changed', self.reload_navigation_panel)
        self.musshaf_viewer_left.connect(
            'hovered-ayah-changed', self.reload_tarajem_viewer)
        self.musshaf_viewer_left.connect(
            'focused-page-changed', self.reload_tarajem_viewer)

    def setup_tarajem_viewer(self) -> None:
        self.tarajem_viewer = TarajemViewer()

    def setup_window_size(self) -> None:
        """Scale the window to fit all its visible contents

        The size is calculated from scaled two-side image pages (or a page).
        For its height, the headerbar height is added.
        """
        musshaf_dir = path.join(const.USER_DATA_PATH,
                                f'musshaf/{glob.musshaf_name}')

        # Load a sample image page of the opened Musshaf ID by assuming that
        # all image pages have the same size
        image_filepath = path.join(musshaf_dir, '1.jpg')
        page_image = GdkPixbuf.Pixbuf.new_from_file(image_filepath)

        page_width = round(page_image.get_width() * glob.page_scale)
        page_height = round(page_image.get_height() * glob.page_scale)

        headerbar_size = self.headerbar.get_allocation()
        window_height = page_height + headerbar_size.height

        if glob.dual_page:
            window_width = page_width*2 + const.PAGE_MARGIN/2*3
        else:
            window_width = page_width

        self.resize(window_width, window_height + const.PAGE_MARGIN)
        self.tarajem_viewer.scrolledwindow.set_size_request(
            page_width, page_height)

        if glob.dual_page:
            window_width = window_width + 52
        else:
            window_width = window_width + 72

        self.set_size_request(window_width, self.get_size_request()[1])

    @Gtk.Template.Callback()
    def on_key_press(
            self,
            window: Gtk.Window,
            event: Gdk.EventKey) -> None:
        ...

    @Gtk.Template.Callback()
    def on_key_release(
            self,
            window: Gtk.Window,
            event: Gdk.EventKey) -> None:
        ...

    @Gtk.Template.Callback()
    def on_loses_focus(
            self,
            window: Gtk.Window,
            event: Gdk.EventFocus) -> None:
        ...

    @Gtk.Template.Callback()
    def on_motion(
            self,
            widget: Gtk.Widget,
            event: Gdk.EventMotion) -> None:
        self.buttonbox_navigation.set_opacity(1)

        self.timer_buttonnav.cancel()
        self.timer_buttonnav = Timer(2.0, self.hide_buttonnav)
        self.timer_buttonnav.start()

    @Gtk.Template.Callback()
    def on_quit(
            self,
            widget: Gtk.Widget) -> None:
        # Free resources
        self.timer_buttonnav.cancel()
        player = self.headerbar.popover_telaawa
        player.playbin.set_state(Gst.State.NULL)
        Gst.Object.unref(player.playbin)
        if player.playbin_seeker:
            GLib.source_remove(player.playbin_seeker)

    @Gtk.Template.Callback()
    def on_buttonnav_focused(
            self,
            widget: Gtk.Widget) -> None:
        self.buttonbox_navigation.set_opacity(1)
        self.timer_buttonnav.cancel()
        self.timer_buttonnav = Timer(2.0, self.hide_buttonnav)

    @Gtk.Template.Callback()
    def on_buttonnav_unfocused(
            self,
            widget: Gtk.Widget) -> None:
        self.timer_buttonnav = Timer(2.0, self.hide_buttonnav)
        self.timer_buttonnav.start()

    def hide_buttonnav(self) -> None:
        Animation.to_invisible(self.buttonbox_navigation)

    def reload_navigation_panel(
            self,
            widget: Gtk.Widget) -> None:
        if not glob.mobile_view:
            self.headerbar.popover_nav.update()
        else:
            self.headerbar.popover_nav_alt.update()

    def reload_musshaf_viewer(
            self,
            widget: Gtk.Widget) -> None:
        self.musshaf_viewer_right.update()
        if glob.dual_page:
            self.musshaf_viewer_left.update()

    def reload_tarajem_viewer(
            self,
            widget: Gtk.Widget) -> None:
        if self.page_focused != glob.page_focused \
                or self.show_tarajem != glob.show_tarajem:
            self.show_tarajem = glob.show_tarajem

            self.main_paned.remove(self.musshaf_viewer_right)
            self.main_paned.remove(self.tarajem_viewer)
            self.main_paned.remove(self.musshaf_viewer_left)

            if glob.dual_page:
                self.musshaf_viewer_right.image.set_halign(Gtk.Align.START)
                self.musshaf_viewer_right.eventbox.set_halign(Gtk.Align.START)

                if glob.show_tarajem \
                        and glob.page_focused >= 0:  # a negative is invalid
                    # If the right Musshaf viewer is on focus, replace the left
                    # Musshaf viewer with tarajem viewer and vice versa.
                    if glob.page_focused == self.musshaf_viewer_right.id:
                        self.main_paned.remove(self.musshaf_viewer_left)
                        self.tarajem_viewer.set_halign(Gtk.Align.END)
                        self.main_paned.pack_start(
                            self.tarajem_viewer, True, True, 0)
                        self.main_paned.pack_end(
                            self.musshaf_viewer_right, True, True, 0)
                    else:
                        self.main_paned.remove(self.musshaf_viewer_right)
                        self.tarajem_viewer.set_halign(Gtk.Align.START)
                        self.main_paned.pack_end(
                            self.tarajem_viewer, True, True, 0)
                        self.main_paned.pack_start(
                            self.musshaf_viewer_left, True, True, 0)
                else:
                    # If tarajem opening is not requested, display only Musshaf
                    # viewer(s)
                    self.main_paned.pack_start(
                        self.musshaf_viewer_left, True, True, 0)
                    self.main_paned.pack_end(
                        self.musshaf_viewer_right, True, True, 0)
            else:
                self.main_paned.pack_end(
                    self.musshaf_viewer_right, True, True, 0)
                self.musshaf_viewer_right.image.set_halign(Gtk.Align.CENTER)
                self.musshaf_viewer_right.eventbox.set_halign(Gtk.Align.CENTER)

        if not glob.show_tarajem or not glob.dual_page:
            return

        is_page_no_updated = self.page_number != glob.page_number
        if is_page_no_updated:
            self.page_number = glob.page_number

        is_tarajem_names_updated = self.tarajem_names != glob.tarajem_names
        if is_tarajem_names_updated:
            self.tarajem_names = deepcopy(glob.tarajem_names)

        is_content_updated = is_page_no_updated \
            or is_tarajem_names_updated

        # Populate tarajem based on the page where the focused ayah is
        # located
        if glob.page_focused == self.musshaf_viewer_right.id:
            self.tarajem_viewer.populate(
                self.musshaf_viewer_right.bboxes,
                self.musshaf_viewer_right.bboxes_hovered,
                self.musshaf_viewer_right.bboxes_focused,
                is_content_updated)
        else:
            self.tarajem_viewer.populate(
                self.musshaf_viewer_left.bboxes,
                self.musshaf_viewer_left.bboxes_hovered,
                self.musshaf_viewer_left.bboxes_focused,
                is_content_updated)

    def reload_telaawa_player(
            self,
            widget: Gtk.Widget) -> None:
        state = self.surah_number != glob.surah_number \
            or self.ayah_number != glob.ayah_number
        self.surah_number = glob.surah_number
        self.ayah_number = glob.ayah_number

        player = self.headerbar.popover_telaawa
        if state \
                and player.ready_to_play:
            player.playback(TelaawaPlayer.PLAY)
        else:
            player.playback(TelaawaPlayer.STOP)

    def resize_musshaf(
            self,
            widget: Gtk.Widget) -> None:
        # FIXME: widget allocations are not updated immediately
        self.musshaf_viewer_right.update(True)
        if glob.dual_page:
            self.musshaf_viewer_left.update(True)
        self.setup_window_size()

    def toggle_dualpage(
            self,
            widget: Gtk.Widget) -> None:
        self.reload_tarajem_viewer(widget)
        self.resize_musshaf(widget)
        self.setup_window_size()

    # def on_notified(
    #         self,
    #         widget: Gtk.Widget,
    #         message: str) -> None:
    #     visible = message != ''
    #     self.status_loading.set_visible(visible)
    #     self.loading_spinner.props.active = visible
    #     self.loading_message.set_text(message)
