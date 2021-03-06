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

from typing import List
import sqlite3
import os


class Reader:
    __dirname__ = os.path.dirname(os.path.abspath(__file__))

    _main_db = sqlite3.connect(os.path.join(__dirname__, '../res/main.db'))
    _main_cursor = _main_db.cursor()

    _pages_db = sqlite3.connect(os.path.join(__dirname__, '../res/pages.db'))
    _pages_cursor = _pages_db.cursor()

    _tarajem_db = sqlite3.connect(os.path.join(
        __dirname__, '../res/translations.db'))
    _tarajem_cursor = _tarajem_db.cursor()

    # Selection(s)
    _selected_pages = 'medina'  # TODO: support page type changing
    _selected_tarajem = []

    #################
    # Navigation
    #################
    def get_page_no(self, sura_no: int, aya_no: int) -> int:
        query = f'SELECT page FROM {self._selected_pages} WHERE sura=? AND ' \
            'aya=? ORDER BY id DESC LIMIT 1'
        self._pages_cursor.execute(query, (sura_no, aya_no))
        return self._pages_cursor.fetchone()[0]

    def get_suras(self) -> List:
        self._main_cursor.execute('SELECT * FROM suras')
        return self._main_cursor.fetchall()

    def get_sura_no_by_page(self, page_no: int) -> int:
        query = f'SELECT sura FROM {self._selected_pages} WHERE page=? LIMIT 1'
        self._pages_cursor.execute(query, (page_no,))
        return self._pages_cursor.fetchone()[0]

    def get_sura_no_by_juz(self, juz_no: int) -> int:
        self._main_cursor.execute('SELECT sura FROM juzs WHERE id=?', (juz_no,))
        return self._main_cursor.fetchone()[0]

    def get_sura_name_by_no(self, sura_no: int) -> int:
        query = f'SELECT tname FROM suras WHERE id=?'
        self._main_cursor.execute(query, (sura_no,))
        return self._main_cursor.fetchone()[0]

    def get_aya_no_by_page(self, page_no: int) -> int:
        query = f'SELECT aya FROM {self._selected_pages} WHERE page=? AND ' \
            'type="ayah" LIMIT 1'
        self._pages_cursor.execute(query, (page_no,))
        return self._pages_cursor.fetchone()[0]

    def get_aya_no_by_juz(self, juz_no: int) -> int:
        self._main_cursor.execute('SELECT aya FROM juzs WHERE id=?', (juz_no,))
        return self._main_cursor.fetchone()[0]

    def get_aya_no_max(self, sura_no: int) -> int:
        self._main_cursor.execute('SELECT ayas FROM suras WHERE id=?',
                                  (sura_no,))
        return self._main_cursor.fetchone()[0]

    def get_aya_text(self, sura_no: int, aya_no: int) -> str:
        self._main_cursor.execute('SELECT text FROM texts WHERE sura=? AND '
                                  'aya=?', (sura_no, aya_no))
        return self._main_cursor.fetchone()[0]

    def get_juz_no(self, sura_no: int, aya_no: int) -> int:
        self._main_cursor.execute('SELECT id FROM juzs WHERE (sura=? AND '
                                  'aya<=?) OR sura<? ORDER BY id DESC LIMIT 1',
                                  (sura_no, aya_no, sura_no))
        return self._main_cursor.fetchone()[0]

    def get_hizb_no(self, sura_no: int, aya_no: int) -> int:
        return 1

    #################
    # Pages
    #################
    def get_bboxes_by_page(self, page_no: int) -> List:
        query = 'SELECT sura, aya, type, x1, y1, x2-x1, y2-y1 FROM ' \
            f'{self._selected_pages} WHERE page=? AND type="ayah"'
        self._pages_cursor.execute(query, (page_no,))
        return self._pages_cursor.fetchall()

    #################
    # Tarajem
    #################
    def get_tarajem_metas(self) -> List:
        self._tarajem_cursor.execute('SELECT * FROM meta ORDER BY language ASC')
        return self._tarajem_cursor.fetchall()

    def get_tarajem_meta(self, tarajem_id: str) -> List:
        self._tarajem_cursor.execute('SELECT * FROM meta WHERE id=?',
                                     (tarajem_id,))
        return self._tarajem_cursor.fetchone()

    def get_tarajem_text(self, tarajem_id: str, sura_no: int,
                         aya_no: int) -> List:
        self._tarajem_cursor.execute('SELECT * FROM meta WHERE id=?',
                                     (tarajem_id,))
        if self._tarajem_cursor.fetchone():
            query = f'SELECT sura, aya, text FROM {tarajem_id} WHERE sura=? ' \
                'AND aya=?'
            self._tarajem_cursor.execute(query, (sura_no, aya_no))
            return self._tarajem_cursor.fetchone()
        return []

    def is_tarajem_exist(self, tarajem_id: str) -> bool:
        self._tarajem_cursor.execute('SELECT name FROM sqlite_master WHERE '
                                     'name=?', (tarajem_id,))
        if self._tarajem_cursor.fetchone():
            return True
        return False

    def get_selected_tarajem(self) -> List:
        return self._selected_tarajem

    def update_selected_tarajem(self, tarajem_id: str) -> List:
        if tarajem_id in self._selected_tarajem:
            self._selected_tarajem.remove(tarajem_id)
        else:
            self._tarajem_cursor.execute('SELECT * FROM meta WHERE id=?',
                                        (tarajem_id,))
            if self._tarajem_cursor.fetchone():
                self._selected_tarajem.append(tarajem_id)
        # TODO: sort `self._selected_tarajem` by language name
        return self._selected_tarajem


class ResourceManager:

    @staticmethod
    def add_tarajem(tarajem_id: str) -> bool:
        # Open database connection
        con = sqlite3.connect(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '../res/translations.db'))
        cur = con.cursor()

        # Check if the id is valid
        cur.execute('SELECT * FROM meta WHERE id=?', (tarajem_id,))
        meta = cur.fetchone()
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
