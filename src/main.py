# main.py
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

import sys
import gi

gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gio', '2.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Handy', '1')
gi.require_version('Pango', '1.0')

from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GObject
from gi.repository import Gtk
from os import path

from . import constants as const
from . import globals as glob
from .model import Musshaf
from .musshaf import MusshafDialog
from .window import MainWindow

class Application(Gtk.Application):

    def __init__(self) -> None:
        super().__init__(application_id=const.APPLICATION_ID,
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

        # Load the saved user settings
        self.settings = Gio.Settings.new(const.APPLICATION_ID)
        glob.musshaf_name = self.settings.get_string('musshaf-name')
        glob.tarajem_names = self.settings.get_strv('tarajem-names')
        glob.telaawa_name = self.settings.get_string('telaawa-name')

        glob.page_scale = self.settings.get_double('page-scale')
        glob.dual_page = self.settings.get_boolean('dual-page')
        glob.tarajem_visibility = self.settings.get_boolean('tarajem-visibility')
        glob.playback_loop = self.settings.get_boolean('playback-loop')

        glob.page_number = self.settings.get_int('page-number')
        glob.surah_number = self.settings.get_int('surah-number')
        glob.ayah_number = self.settings.get_int('ayah-number')
        glob.juz_number = self.settings.get_int('juz-number')
        glob.hizb_number = self.settings.get_int('hizb-number')
        glob.quarter_number = self.settings.get_int('quarter-number')

        # Watch the system-wide settings when global Gtk application theme has
        # been changed
        Gtk.Settings.get_default().connect('notify::gtk-theme-name',
                                           self.on_theme_changed)

        # Initialise the application theme based on the activated global Gtk
        # application theme
        self.reload_css()

    def do_activate(self) -> None:
        window = self.props.active_window

        if not window:
            # If the application has ever been opened, open the main window.
            # Otherwise, open the musshaf manager dialog.
            musshaf_filepath = path.join(
                const.USER_DATA_PATH,
                f'musshaf/{glob.musshaf_name}/1.jpg')
            with Musshaf() as musshaf:
                if musshaf.is_musshaf_exist(glob.musshaf_name) \
                        and path.isfile(musshaf_filepath):
                    window = MainWindow(application=self)
                else:
                    window = MusshafDialog(application=self)

        window.present()

    def switch_to(
            self,
            window_name: str,
            replaced: bool = False) -> None:
        if replaced:
            self.props.active_window.destroy()

        if window_name == 'musshaf_dialog':
            window = MusshafDialog(application=self)
        else:
            window = MainWindow(application=self)

        window.present()

    def reload_css(self) -> None:
        """Reload styles based on the global Gtk application theme variants

        Any Gtk application theme that has 'dark' or 'inverse' in its name
        should be a dark theme variant.
        """
        default_settings = Gtk.Settings.get_default()
        gtk_theme_name = default_settings.get_property('gtk-theme-name')
        gtk_theme_name = gtk_theme_name.lower()

        if 'dark' in gtk_theme_name \
                or 'inverse' in gtk_theme_name:
            variant = '-dark'
        else:
            variant = ''

        provider = Gtk.CssProvider()
        css_resource_path = f'/org/grapik/Quran/css/main{variant}.css'
        provider.load_from_resource(css_resource_path)

        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def save_user_settings(self) -> None:
        """Save the last page read settings."""
        self.settings.set_string('musshaf-name', glob.musshaf_name)
        self.settings.set_strv('tarajem-names', glob.tarajem_names)
        self.settings.set_string('telaawa-name', glob.telaawa_name)

        self.settings.set_double('page-scale', glob.page_scale)
        self.settings.set_boolean('dual-page', glob.dual_page)
        self.settings.set_boolean('tarajem-visibility', glob.tarajem_visibility)
        self.settings.set_boolean('playback-loop', glob.playback_loop)

        if glob.surah_number < 0:
            # If the last page read has no ayah(s), go to the page where Surah
            # Al-Fathihah is located
            self.settings.reset('page-number')
            self.settings.reset('surah-number')
            self.settings.reset('ayah-number')
            self.settings.reset('juz-number')
            self.settings.reset('hizb-number')
            self.settings.reset('quarter-number')
        else:
            self.settings.set_int('page-number', glob.page_number)
            self.settings.set_int('surah-number', glob.surah_number)
            self.settings.set_int('ayah-number', glob.ayah_number)
            self.settings.set_int('juz-number', glob.juz_number)
            self.settings.set_int('hizb-number', glob.hizb_number)
            self.settings.set_int('quarter-number', glob.quarter_number)

    def on_theme_changed(
            self,
            settings: Gtk.Settings,
            gparamstring: str) -> None:
        self.reload_css()


def main(
        app_name: str,
        app_version: str) -> int:
    const.APPLICATION_NAME = app_name
    const.APPLICATION_VERSION = app_version
    GObject.threads_init()
    application = Application()
    exit_status = application.run(sys.argv)
    application.save_user_settings()
    return exit_status
