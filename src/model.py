# model.py
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

from gi.repository import GLib, Gtk
from typing import List
from urllib.request import urlopen
import io
import os
import shutil
import sqlite3
import tempfile
import zipfile


class Reader:
    _main_db = sqlite3.connect(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '../main.db'))
    _musshaf_db = sqlite3.connect(os.path.join(
        GLib.get_user_data_dir(), 'grapik-quran/musshaf.db'))
    _tarajem_db = sqlite3.connect(os.path.join(
        GLib.get_user_data_dir(), 'grapik-quran/tarajem.db'))

    _main_cursor = _main_db.cursor()
    _musshaf_cursor = _musshaf_db.cursor()
    _tarajem_cursor = _tarajem_db.cursor()

    _selected_musshaf = ''
    _selected_tarajem = []

    def get_page_no(self, sura_no: int, aya_no: int) -> int:
        query = f'SELECT page FROM {self._selected_musshaf} WHERE sura=? AND' \
            ' aya=? ORDER BY id DESC'
        self._musshaf_cursor.execute(query, (sura_no, aya_no))
        result = self._musshaf_cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_suras(self) -> List:
        self._main_cursor.execute('SELECT * FROM suras')
        return self._main_cursor.fetchall()

    def get_sura_no(self, page_no: int = None, juz_no: int = None) -> int:
        if page_no:
            query = f'SELECT sura FROM {self._selected_musshaf} WHERE page=?'
            self._musshaf_cursor.execute(query, (page_no,))
            result = self._musshaf_cursor.fetchone()
            if result:
                return result[0]
        elif juz_no:
            self._main_cursor.execute('SELECT sura FROM juzs WHERE id=?',
                                      (juz_no,))
            result = self._main_cursor.fetchone()
            if result:
                return result[0]
        return -1

    def get_sura_name(self, sura_no: int) -> int:
        query = f'SELECT tname FROM suras WHERE id=?'
        self._main_cursor.execute(query, (sura_no,))
        result = self._main_cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_sura_length(self, sura_no: int) -> int:
        self._main_cursor.execute('SELECT ayas FROM suras WHERE id=?',
                                  (sura_no,))
        result = self._main_cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_aya_no(self, page_no: int = None, juz_no: int = None) -> int:
        if page_no:
            query = f'SELECT aya FROM {self._selected_musshaf} WHERE page=?'
            self._musshaf_cursor.execute(query, (page_no,))
            result = self._musshaf_cursor.fetchone()
            if result:
                return result[0]
        elif juz_no:
            self._main_cursor.execute('SELECT aya FROM juzs WHERE id=?',
                                      (juz_no,))
            result = self._main_cursor.fetchone()
            if result:
                return result[0]
        return -1

    def get_aya_text(self, sura_no: int, aya_no: int) -> str:
        self._main_cursor.execute('SELECT text FROM texts WHERE sura=? AND '
                                  'aya=?', (sura_no, aya_no))
        result = self._main_cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_suraya_seq(self, sura_no: int, aya_no: int) -> int:
        query = \
            f'''SELECT seq from (SELECT ROW_NUMBER() OVER (ORDER BY id) seq,
            sura, aya FROM {self._selected_musshaf} WHERE page=(SELECT page
            FROM {self._selected_musshaf} WHERE sura=? AND aya=? LIMIT 1)
            GROUP BY sura, aya) WHERE sura=? AND aya=?'''
        self._musshaf_cursor.execute(query, (sura_no, aya_no, sura_no, aya_no))
        result = self._musshaf_cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_juz_no(self, sura_no: int, aya_no: int) -> int:
        self._main_cursor.execute('SELECT id FROM juzs WHERE (sura=? AND '
                                  'aya<=?) OR sura<? ORDER BY id DESC LIMIT 1',
                                  (sura_no, aya_no, sura_no))
        result = self._main_cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_hizb_no(self, sura_no: int, aya_no: int) -> int:
        return 1

    def get_tarajems(self) -> List:
        self._main_cursor.execute('SELECT * FROM tarajem ORDER BY language, ' \
                                  'translator ASC')
        return self._main_cursor.fetchall()

    def get_tarajem(self, tarajem_id: str) -> List:
        self._main_cursor.execute('SELECT * FROM tarajem WHERE id=?',
                                  (tarajem_id,))
        return self._main_cursor.fetchone()

    def get_tarajem_text(self, tarajem_id: str, sura_no: int,
                         aya_no: int) -> List:
        self._main_cursor.execute('SELECT * FROM tarajem WHERE id=?',
                                  (tarajem_id,))
        if self._main_cursor.fetchone():
            query = f'SELECT sura, aya, text FROM {tarajem_id} WHERE sura=? ' \
                'AND aya=?'
            self._tarajem_cursor.execute(query, (sura_no, aya_no))
            return self._tarajem_cursor.fetchone()
        return []

    def get_selected_tarajem(self) -> List:
        return self._selected_tarajem

    def update_selected_tarajem(self, tarajem_id: str) -> List:
        if tarajem_id in self._selected_tarajem:
            self._selected_tarajem.remove(tarajem_id)
        else:
            self._main_cursor.execute('SELECT * FROM tarajem WHERE id=?',
                                      (tarajem_id,))
            if self._main_cursor.fetchone():
                self._selected_tarajem.append(tarajem_id)
        return self._selected_tarajem

    def check_tarajem(self, tarajem_id: str) -> bool:
        self._tarajem_cursor.execute('SELECT name FROM sqlite_master WHERE '
                                     'name=?', (tarajem_id,))
        if self._tarajem_cursor.fetchone():
            return True
        return False

    def get_musshafs(self) -> List:
        self._main_cursor.execute('SELECT * FROM musshaf ORDER BY name')
        return self._main_cursor.fetchall()

    def get_selected_musshaf(self) -> str:
        return self._selected_musshaf

    def update_selected_musshaf(self, musshaf_id: str) -> str:
        self._main_cursor.execute('SELECT * FROM musshaf WHERE id=?',
                                  (musshaf_id,))
        if self._main_cursor.fetchone():
            self._selected_musshaf = musshaf_id
        return self._selected_musshaf

    def check_musshaf(self, musshaf_id: str) -> bool:
        self._musshaf_cursor.execute('SELECT name FROM sqlite_master WHERE '
                                     'name=?', (musshaf_id,))
        if self._musshaf_cursor.fetchone():
            return True
        return False

    def get_bboxes(self, page_no: int) -> List:
        query = 'SELECT sura, aya, x1, y1, x2-x1, y2-y1 FROM ' \
            f'{self._selected_musshaf} WHERE page=?'
        self._musshaf_cursor.execute(query, (page_no,))
        return self._musshaf_cursor.fetchall()


class ResourceManager:

    @staticmethod
    def add_musshaf(musshaf_id: str,
                    progressbar: Gtk.ProgressBar = None) -> bool:
        con = sqlite3.connect(os.path.join(
            GLib.get_user_data_dir(), 'grapik-quran/musshaf.db'))
        cur = con.cursor()

        # Check if the id is valid
        con_ = sqlite3.connect(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '../main.db'))
        cur_ = con_.cursor()
        cur_.execute('SELECT * FROM musshaf WHERE id=?', (musshaf_id,))
        meta = cur_.fetchone()
        con_.close()
        if not meta:
            con.close()
            return False

        response_images = urlopen(url=meta[2])
        response_bboxes = urlopen(url=meta[3])

        image_size = int(response_images.getheader('Content-Length'))
        bbox_size = int(response_bboxes.getheader('Content-Length'))
        total_length = image_size + bbox_size
        dl = 0

        # Download archive file for the musshaf images
        # FIXME: segmentation fault caused by unstable internet connection(?)
        chunk_size = 4096
        musshaf_dir = os.path.join(
            GLib.get_user_data_dir(), f'grapik-quran/musshaf/{musshaf_id}')
        if not os.path.isdir(musshaf_dir):
            with tempfile.TemporaryFile() as f:
                while True:
                    chunk = response_images.read(chunk_size)
                    if not chunk:
                        break
                    dl += len(chunk)
                    if progressbar:
                        progressbar.set_fraction(dl / total_length)
                    f.write(chunk)

                f.seek(0)
                with zipfile.ZipFile(io.BytesIO(f.read()), 'r') as fz:
                    os.makedirs(musshaf_dir, exist_ok=True)
                    for filename in fz.namelist():
                        image = fz.open(filename)
                        filepath = os.path.join(
                            musshaf_dir, os.path.basename(filename))
                        with open(filepath, 'wb') as fi:
                            shutil.copyfileobj(image, fi)
        else:
            dl += image_size

        cur.execute('SELECT name FROM sqlite_master WHERE name=?',
                    (musshaf_id,))
        if not cur.fetchone():
            # Download SQL query file for the musshaf bounding boxes
            response_bboxes = urlopen(url=meta[3])  # reopen in case of
                                                    # connection reset by peer
            with tempfile.TemporaryFile() as f:
                while True:
                    chunk = response_bboxes.read(chunk_size)
                    if not chunk:
                        break
                    dl += len(chunk)
                    if progressbar:
                        progressbar.set_fraction(dl / total_length)
                    f.write(chunk)

                f.seek(0)
                cur.execute('PRAGMA encoding="UTF-8";')
                cur.executescript(f.read().decode('utf-8'))

            # Add ID column to the new created table
            query = f'''CREATE TABLE {musshaf_id}_copy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page INT (3) NOT NULL,
                sura INT (3) NOT NULL,
                aya INT (3) NOT NULL,
                x1 INT (5) NOT NULL,
                y1 INT (5) NOT NULL,
                x2 INT (5) NOT NULL,
                y2 INT (5) NOT NULL
            );'''
            cur.execute(query)
            query = f'''INSERT INTO {musshaf_id}_copy
                (page, sura, aya, x1, y1, x2, y2)
                SELECT page, sura, aya, x1, y1, x2, y2 FROM {musshaf_id}
            '''
            cur.execute(query)
            query = f'''DROP TABLE {musshaf_id};'''
            cur.execute(query)
            query = f'''ALTER TABLE {musshaf_id}_copy RENAME TO {musshaf_id}'''
            cur.execute(query)
            con.commit()
        else:
            dl += bbox_size

        con.close()

        return True

    @staticmethod
    def add_tarajem(tarajem_id: str,
                    progressbar: Gtk.ProgressBar = None) -> bool:
        con = sqlite3.connect(os.path.join(
            GLib.get_user_data_dir(), 'grapik-quran/tarajem.db'))
        cur = con.cursor()

        # Check if the id is valid
        con_ = sqlite3.connect(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '../main.db'))
        cur_ = con_.cursor()
        cur_.execute('SELECT * FROM tarajem WHERE id=?', (tarajem_id,))
        meta = cur_.fetchone()
        con_.close()
        if not meta:
            con.close()
            return False

        response = urlopen(url=meta[-1])

        total_length = int(response.getheader('Content-Length'))
        dl = 0

        chunk_size = 4096
        with tempfile.TemporaryFile() as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                dl += len(chunk)
                if progressbar:
                    progressbar.set_fraction(dl / total_length)
                f.write(chunk)

            f.seek(0)
            query = f'''CREATE TABLE {tarajem_id} (
                id   INT(4) PRIMARY KEY
                            NOT NULL,
                sura INT(3) NOT NULL,
                aya  INT(3) NOT NULL,
                text TEXT   NOT NULL
            );'''
            cur.execute(query)
            cur.execute('PRAGMA encoding="UTF-8";')
            cur.executescript('\n'.join(f.read().decode('utf-8').replace('index', 'id')
                                        .replace(r"\'", "''").split('\n')[46:]))

        con.commit()
        con.close()
        return True
