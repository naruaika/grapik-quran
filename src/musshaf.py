# musshaf.py
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

from cairo import Context
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GObject
from gi.repository import Gtk
from io import BytesIO
from os import makedirs
from os import path
from shutil import copyfileobj
from tempfile import TemporaryFile
from threading import Thread
from typing import List
from urllib.request import urlopen
from zipfile import ZipFile

from . import constants as const
from . import globals as glo
from .animation import Animation
from .model import Metadata
from .model import Musshaf

import faulthandler


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/musshaf_viewer.ui')
class MusshafViewer(Gtk.Overlay):
    __gtype_name__ = 'MusshafViewer'

    __gsignals__ = {
        'selected-ayah-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'hovered-ayah-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'focused-page-changed': (GObject.SIGNAL_RUN_FIRST, None, ())}

    viewport = Gtk.Template.Child('viewport')
    overlay = Gtk.Template.Child('overlay')
    image = Gtk.Template.Child('image')
    eventbox = Gtk.Template.Child('eventbox')

    page_image: GdkPixbuf.Pixbuf = None

    page_width: int = None
    page_height: int = None

    page_no: int = None  # to stop image page reloading when the page number
                         # has not changed

    bboxes: List = []
    bboxes_hovered: List = []
    bboxes_focused: List = []

    def __init__(
            self,
            page_id: int,
            **kwargs) -> None:
        super().__init__(**kwargs)

        self.id = page_id  # 0 for the main page viewer

        self.setup_viewer()

    def setup_viewer(self) -> None:
        self.musshaf_dir = \
            path.join(const.USER_DATA_PATH, f'musshaf/{glo.musshaf_name}')

        # Load a sample image page of the opened Musshaf ID by assuming that
        # all image pages have the same size
        page_filepath = path.join(self.musshaf_dir, '1.jpg')
        page_image = GdkPixbuf.Pixbuf.new_from_file(page_filepath)

        # Store the actual image page size, because it will be used to
        # calculate the image page size after scalling by the page zoom value
        self.page_width = page_image.get_width()
        self.page_height = page_image.get_height()

    @Gtk.Template.Callback()
    def focus_on_ayah(
            self,
            widget: Gtk.Widget,
            event: Gdk.EventButton) -> None:
        if not self.bboxes_hovered:
            return

        bbox = self.bboxes_hovered[0]
        glo.surah_number = bbox[0]
        glo.ayah_number = bbox[1]
        self.emit('selected-ayah-changed')

    @Gtk.Template.Callback()
    def draw_bboxes(
            self,
            widget: Gtk.Widget,
            context: Context) -> None:
        # Draw hovered ayah(s)
        context.set_source_rgba(0.2, 0.2, 0.2, 0.075)
        for bbox in self.bboxes_hovered:
            if bbox in self.bboxes_focused:
                continue
            context.rectangle(*bbox[2:])
        context.fill()

        # Draw focused ayah(s)
        context.set_source_rgba(0.082, 0.325, 0.620, 0.2)
        for bbox in self.bboxes_focused:
            context.rectangle(*bbox[2:])
        context.fill()

    @Gtk.Template.Callback()
    def hover_on_ayah(
            self,
            widget: Gtk.Widget,
            event: Gdk.EventMotion) -> None:
        # Find any surah-ayah under the cursor
        suraya_hovered = None
        for bbox in self.bboxes:
            if bbox[2] <= event.x <= bbox[2] + bbox[4] and \
                    bbox[3] <= event.y <= bbox[3] + bbox[5]:
                suraya_hovered = bbox[:2]
                break

        if suraya_hovered:
            bboxes_hovered = [bbox for bbox in self.bboxes
                              if bbox[:2] == suraya_hovered]
        else:
            bboxes_hovered = []

        if self.bboxes_hovered == bboxes_hovered:
            return

        self.bboxes_hovered = bboxes_hovered
        self.emit('hovered-ayah-changed')

        # Draw bounding boxes over hovered ayah(s) in Musshaf viewer
        self.eventbox.queue_draw()

    def update(self) -> None:
        # Normalise the page numbering
        if glo.dual_page \
                and glo.page_number % 2 == 1:
            page_no = glo.page_number - 1
        else:
            page_no = glo.page_number
        page_no = page_no + self.id

        # Obtain all ayah bounding boxes of the corresponding page and then
        # scale them all by the page zoom value
        if self.page_no != page_no:
            with Musshaf() as musshaf:
                bboxes = musshaf.get_bboxes(page_no)
                for idx_bbox in range(len(bboxes)):
                    surah_no_, ayah_no_, x, y, w, h = bboxes[idx_bbox]
                    bboxes[idx_bbox] = (surah_no_, ayah_no_,
                                        x * glo.page_scale,
                                        y * glo.page_scale,
                                        w * glo.page_scale,
                                        h * glo.page_scale)
                self.bboxes = bboxes

        # Set focus on the first ayah on the page
        self.bboxes_focused = \
            [bbox for bbox in self.bboxes
             if bbox[:2] == (glo.surah_number, glo.ayah_number)]

        # Request updates to main window
        if self.bboxes_focused \
                and glo.page_focused != self.id:
            glo.page_focused = self.id
            self.emit('focused-page-changed')

        # No need to reload the page image if the page number does not change
        if self.page_no == page_no:
            self.eventbox.queue_draw()
            return
        self.page_no = page_no

        # If the page number is valid, load the corresponding image page.
        # Otherwise, load a blank image page.
        try:
            page_filepath = path.join(self.musshaf_dir, f'{page_no}.jpg')
            self.page_image = GdkPixbuf.Pixbuf.new_from_file(page_filepath)
        except:
            page_filepath = f'{const.RESOURCE_PATH}/img/page_blank.png'
            self.page_image = GdkPixbuf.Pixbuf.new_from_resource(page_filepath)

        # Scale the newly loaded image page by the page zoom value and then
        # display it
        page_width = round(self.page_width * glo.page_scale)
        page_height = round(self.page_height * glo.page_scale)
        page_image = self.page_image.scale_simple(
            page_width, page_height, GdkPixbuf.InterpType.BILINEAR)
        page_image.saturate_and_pixelate(page_image, 1.0, False)
        self.image.set_from_pixbuf(page_image)
        self.eventbox.set_size_request(page_width, page_height)


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/musshaf_dialog.ui')
class MusshafDialog(Gtk.Window):
    __gtype_name__ = 'MusshafDialog'

    listbox = Gtk.Template.Child('listbox')
    progressbar = Gtk.Template.Child('progressbar')
    button_ok = Gtk.Template.Child('button_ok')
    button_quit = Gtk.Template.Child('button_quit')
    scrolledwindow = Gtk.Template.Child('scrolledwindow')

    musshaf_name: str = ''  # to avoid downloading another musshaf while
                            # downloading a musshaf

    open_after_download = False  # request to quit after when the user decides
                                 # to open a Musshaf while downloading another

    def __init__(
            self,
            **kwargs) -> None:
        super().__init__(**kwargs)

        # Set the window application name identifier, so it can be recognized
        # by the user in the desktop application switcher
        self.set_title(const.APPLICATION_NAME)
        self.set_wmclass(const.APPLICATION_NAME, const.APPLICATION_NAME)

        self.populate()

    def populate(self) -> bool:
        """Populate a list of all available Musshafs

        Contains metadata of all supported Musshaf to be downloaded and opened,
        the data is retrieved from the SQLite database. Returns True if the
        Musshaf list is successfully generated, otherwise False. It should
        always returns True if the installation of application has done
        smoothly.
        """
        with Metadata() as metadata, \
             Musshaf() as model:
            musshaf_dir = path.join(const.USER_DATA_PATH, 'musshaf')

            for musshaf in metadata.get_musshafs():
                name = f'<span weight="bold">{musshaf[1]}</span>'
                description = f'<span size="small">{musshaf[4]}</span>'
                row = MusshafListBoxRow(name, description)

                row.id = musshaf[0]

                are_images_downloaded = \
                    path.isdir(path.join(musshaf_dir, row.id))
                are_bboxes_downloaded = model.is_musshaf_exist(row.id)
                row.is_downloaded = are_images_downloaded \
                    and are_bboxes_downloaded

                if row.is_downloaded:
                    icon_name = 'object-select-symbolic'
                else:
                    icon_name = 'folder-download-symbolic'
                row.icon_status.set_from_icon_name(icon_name,
                                                   Gtk.IconSize.BUTTON)

                if row.id == glo.musshaf_name:
                    self.listbox.select_row(row)
                else:
                    row.icon_status.set_opacity(int(not row.is_downloaded))

                self.listbox.add(row)

        self.listbox.show_all()

        if self.listbox.get_children():
            return True
        return False

    @Gtk.Template.Callback()
    def on_selected(
            self,
            listbox: Gtk.ListBox,
            listboxrow: Gtk.ListBoxRow) -> None:
        """Select the activated Musshaf list item."""
        if listboxrow.id == self.musshaf_name:
            self.button_ok.set_sensitive(False)
            self.button_ok.set_label('Downloading...')
        elif not listboxrow.is_downloaded:
            self.button_ok.set_label('Download')
            self.button_ok.set_sensitive(not self.musshaf_name)
        else:
            self.button_ok.set_sensitive(True)
            self.button_ok.set_label('Open')

        if glo.musshaf_name == listboxrow.id:
            return
        glo.musshaf_name = listboxrow.id

        def reset(listboxrow: Gtk.ListBoxRow) -> None:
            if listboxrow.is_downloaded:
                listboxrow.icon_status.set_opacity(0)

        listbox.foreach(reset)

        listboxrow.icon_status.set_opacity(1)

    @Gtk.Template.Callback()
    def on_load(
            self,
            button: Gtk.Button) -> None:
        """Load the selected Musshaf and switch to the main window."""
        row = self.listbox.get_selected_row()

        if not row.is_downloaded:
            self.download()
        else:
            self.get_application().switch_to('main_window')
            if not self.musshaf_name:
                self.destroy()
            else:
                self.open_after_download = True
                self.hide()

    @Gtk.Template.Callback()
    def on_quit(
            self,
            button: Gtk.Button) -> None:
        self.destroy()

    def download(self) -> None:
        """Download selected Musshaf from the internet

        All data related to the selected Musshaf such as images and bounding
        boxes will be downloaded from the URL stored in the SQLite database.
        The images will be placed at a new created directory at `xdg-data/`
        `grapik-quran/musshaf`, whereas the bounding boxes will be placed in a
        new created table.
        """
        if self.musshaf_name:
            return
        self.musshaf_name = glo.musshaf_name
        self.button_ok.set_sensitive(False)
        self.button_ok.set_label('Downloading...')

        row = self.listbox.get_selected_row()
        row.icon_status.hide()
        row.spinner.start()
        row.spinner.show()

        def is_downloaded() -> bool:
            with Metadata() as metadata, \
                 Musshaf() as model:
                musshaf = metadata.get_musshaf(glo.musshaf_name)
                if not musshaf:
                    return False

                # Open connection and look for content length in its header
                # response_images = urlopen(musshaf[2])
                # image_length = response_images.getheader('Content-Length')
                # image_length = (0 if not image_length else int(image_length))
                image_length = 0

                response_bboxes = urlopen(musshaf[3])
                bbox_length = response_bboxes.getheader('Content-Length')
                bbox_length = (0 if not bbox_length else int(bbox_length))

                total_length = image_length + bbox_length
                downloaded_length = 0
                chunk_size = 4096

                # Display better error messsages on unexpected connection
                # closings
                # FIXME: segmentation fault caused by unstable internet
                # connection(?); but it is likely only because of timeout
                faulthandler.enable()

                # Check if the bounding boxes has been downloaded on previous
                # interrupted downloads
                model.cursor.execute('SELECT name FROM sqlite_master WHERE '
                                     'name=?', (glo.musshaf_name,))
                if not model.cursor.fetchone():
                    response_bboxes = urlopen(musshaf[3])  # reopen; in case of
                                                           # connection reset
                                                           # by peer

                    # Download SQL query file for the Musshaf bounding boxes
                    with TemporaryFile() as f:
                        while True:
                            chunk = response_bboxes.read(chunk_size)
                            if not chunk:
                                break
                            downloaded_length += len(chunk)
                            if image_length:
                                self.progressbar.set_fraction(
                                    downloaded_length / total_length)
                            f.write(chunk)

                        f.seek(0)
                        model.cursor.execute('PRAGMA encoding="UTF-8";')
                        model.cursor.executescript(f.read().decode('utf-8'))

                    # Add ID column to the new created table
                    query = \
                        f'''CREATE TABLE {glo.musshaf_name}_copy (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            page INT (3) NOT NULL,
                            sura INT (3) NOT NULL,
                            aya INT (3) NOT NULL,
                            x1 INT (5) NOT NULL,
                            y1 INT (5) NOT NULL,
                            x2 INT (5) NOT NULL,
                            y2 INT (5) NOT NULL
                        );'''
                    model.cursor.execute(query)

                    query = \
                        f'''INSERT INTO {glo.musshaf_name}_copy
                            (page, sura, aya, x1, y1, x2, y2)
                            SELECT page, sura, aya, x1, y1, x2, y2 FROM
                            {glo.musshaf_name}
                        '''
                    model.cursor.execute(query)

                    query = f'DROP TABLE {glo.musshaf_name};'
                    model.cursor.execute(query)
                    query = f'ALTER TABLE {glo.musshaf_name}_copy ' \
                        f'RENAME TO {glo.musshaf_name}'
                    model.cursor.execute(query)

                    model.connection.commit()
                else:
                    downloaded_length += bbox_length

                # Check if the images has been downloaded on previous
                # interrupted downloads
                # musshaf_dir = \
                #     path.join(const.USER_DATA_PATH, f'musshaf/{glo.musshaf_name}')
                # if not path.isdir(musshaf_dir):
                #     # Download archive file for the Musshaf images
                #     with TemporaryFile() as f:
                #         while True:
                #             chunk = response_images.read(chunk_size)
                #             if not chunk:
                #                 break
                #             downloaded_length += len(chunk)
                #             if bbox_length:
                #                 self.progressbar.set_fraction(
                #                     downloaded_length / total_length)
                #             f.write(chunk)

                #         f.seek(0)
                #         with ZipFile(BytesIO(f.read()), 'r') as fz:
                #             makedirs(musshaf_dir, exist_ok=True)
                #             for filename in fz.namelist():
                #                 image = fz.open(filename)
                #                 filepath = path.join(
                #                     musshaf_dir, path.basename(filename))
                #                 with open(filepath, 'wb') as fi:
                #                     copyfileobj(image, fi)
                # else:
                #     downloaded_length += image_length

                self.progressbar.set_fraction(1)  # in case there is no content
                                                  # length in its header

                return True

        def execute() -> None:
            self.progressbar.show()

            if is_downloaded():
                row.is_downloaded = True
                self.button_ok.set_label('Open')
                self.button_ok.set_sensitive(True)

                def reset(row: Gtk.ListBoxRow) -> None:
                    if row.is_downloaded:
                        row.icon_status.set_opacity(0)

                self.listbox.foreach(reset)

                self.listbox.select_row(row)
                row.icon_status.set_from_icon_name(
                    'object-select-symbolic', Gtk.IconSize.BUTTON)
                row.icon_status.set_opacity(1)
                glo.musshaf_name = row.id
                Animation.scroll_to(self.scrolledwindow, row, 200)

            row.spinner.hide()
            row.spinner.stop()
            row.icon_status.show()
            self.progressbar.hide()
            self.progressbar.set_fraction(0)
            self.musshaf_name = ''

            if self.open_after_download:
                self.destroy()

        Thread(target=execute).start()


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/musshaf_listboxrow.ui')
class MusshafListBoxRow(Gtk.ListBoxRow):
    __gtype_name__ = 'MusshafListBoxRow'

    icon_status = Gtk.Template.Child('icon_status')
    spinner = Gtk.Template.Child('spinner')
    label_name = Gtk.Template.Child('label_name')
    label_description = Gtk.Template.Child('label_description')

    def __init__(
            self,
            name: str,
            description: str,
            **kwargs) -> None:
        super().__init__(**kwargs)

        self.label_name.set_markup(name)
        self.label_description.set_markup(description)

        self.icon_status.set_no_show_all(True)
        self.spinner.set_no_show_all(True)
