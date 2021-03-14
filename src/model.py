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

from gi.repository import GLib
from typing import List
import sqlite3
import os


class Reader:
    _main_db = sqlite3.connect(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '../main.db'))
    _page_db = sqlite3.connect(os.path.join(
        GLib.get_user_data_dir(), 'grapik-quran/pages.db'))
    _tarajem_db = sqlite3.connect(os.path.join(
        GLib.get_user_data_dir(), 'grapik-quran/tarajem.db'))

    _main_cursor = _main_db.cursor()
    _page_cursor = _page_db.cursor()
    _tarajem_cursor = _tarajem_db.cursor()

    _selected_quran = 'standard'
    _selected_tarajem = []

    def get_page_no(self, sura_no: int, aya_no: int) -> int:
        query = f'SELECT page FROM {self._selected_quran} WHERE sura=? AND ' \
            'aya=? ORDER BY id DESC'
        self._page_cursor.execute(query, (sura_no, aya_no))
        return self._page_cursor.fetchone()[0]

    def get_suras(self) -> List:
        self._main_cursor.execute('SELECT * FROM suras')
        return self._main_cursor.fetchall()

    def get_sura_no(self, page_no: int = None, juz_no: int = None) -> int:
        if page_no:
            query = f'SELECT sura FROM {self._selected_quran} WHERE page=?'
            self._page_cursor.execute(query, (page_no,))
            return self._page_cursor.fetchone()[0]
        elif juz_no:
            self._main_cursor.execute('SELECT sura FROM juzs WHERE id=?',
                                      (juz_no,))
            return self._main_cursor.fetchone()[0]

    def get_sura_name(self, sura_no: int) -> int:
        query = f'SELECT tname FROM suras WHERE id=?'
        self._main_cursor.execute(query, (sura_no,))
        return self._main_cursor.fetchone()[0]

    def get_sura_length(self, sura_no: int) -> int:
        self._main_cursor.execute('SELECT ayas FROM suras WHERE id=?',
                                  (sura_no,))
        return self._main_cursor.fetchone()[0]

    def get_aya_no(self, page_no: int = None, juz_no: int = None) -> int:
        if page_no:
            query = f'SELECT aya FROM {self._selected_quran} WHERE page=? ' \
                'AND type="ayah" LIMIT 1'
            self._page_cursor.execute(query, (page_no,))
            return self._page_cursor.fetchone()[0]
        elif juz_no:
            self._main_cursor.execute('SELECT aya FROM juzs WHERE id=?',
                                      (juz_no,))
            return self._main_cursor.fetchone()[0]

    def get_aya_text(self, sura_no: int, aya_no: int) -> str:
        self._main_cursor.execute('SELECT text FROM texts WHERE sura=? AND '
                                  'aya=?', (sura_no, aya_no))
        return self._main_cursor.fetchone()[0]

    def get_suraya_seq(self, sura_no: int, aya_no: int) -> int:
        query = \
            f'''SELECT seq from (SELECT ROW_NUMBER() OVER (ORDER BY id) seq,
            sura, aya FROM {self._selected_quran} WHERE page=(SELECT page FROM
            {self._selected_quran} WHERE sura=? AND aya=? LIMIT 1) AND
            TYPE="ayah" GROUP BY sura, aya) WHERE sura=? AND aya=?'''
        self._page_cursor.execute(query, (sura_no, aya_no, sura_no, aya_no))
        return self._page_cursor.fetchone()[0]

    def get_juz_no(self, sura_no: int, aya_no: int) -> int:
        self._main_cursor.execute('SELECT id FROM juzs WHERE (sura=? AND '
                                  'aya<=?) OR sura<? ORDER BY id DESC LIMIT 1',
                                  (sura_no, aya_no, sura_no))
        return self._main_cursor.fetchone()[0]

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

    def check_tarajem(self, tarajem_id: str) -> bool:
        self._tarajem_cursor.execute('SELECT name FROM sqlite_master WHERE '
                                     'name=?', (tarajem_id,))
        if self._tarajem_cursor.fetchone():
            return True
        return False

    def get_bboxes(self, page_no: int) -> List:
        query = 'SELECT sura, aya, type, x1, y1, x2-x1, y2-y1 FROM ' \
            f'{self._selected_quran} WHERE page=? AND type="ayah"'
        self._page_cursor.execute(query, (page_no,))
        return self._page_cursor.fetchall()

    def get_selected_quran(self) -> str:
        return self._selected_quran

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


class ResourceManager:

    @staticmethod
    def add_quran(page_id: str) -> bool:
        ...

    @staticmethod
    def add_tarajem(tarajem_id: str) -> bool:
        # Open database connection
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

        # Try to download the file
        import requests
        sql = requests.get(url=meta[-1], timeout=30)

        # Check if the file is downloaded
        if not sql.ok:
            con.close()
            return False

        # Execute SQL queries
        query = f'''CREATE TABLE {tarajem_id} (
            id   INT(4) PRIMARY KEY
                        NOT NULL,
            sura INT(3) NOT NULL,
            aya  INT(3) NOT NULL,
            text TEXT   NOT NULL
        );'''
        cur.execute(query)
        cur.execute('PRAGMA encoding="UTF-8";')
        cur.executescript('\n'.join(sql.text.replace('index', 'id')
                                    .replace(r"\'", "''").split('\n')[46:]))

        # Close database connection
        con.commit()
        con.close()
        return True
