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


class Model:
    __dirname__ = os.path.dirname(os.path.abspath(__file__))

    _main_db = sqlite3.connect(os.path.join(__dirname__, '../res/main.db'))
    _main_cursor = _main_db.cursor()

    _pages_db = sqlite3.connect(os.path.join(__dirname__, '../res/pages.db'))
    _pages_cursor = _pages_db.cursor()
    _pages_type = 'medina'  # TODO: support page type changing

    def get_page_no(self, sura_no: int, aya_no: int) -> int:
        query = f'SELECT page FROM {self._pages_type} WHERE sura=? AND aya=? ' \
            'ORDER BY id DESC LIMIT 1'
        self._pages_cursor.execute(query, (sura_no, aya_no))
        return self._pages_cursor.fetchone()[0]

    def get_suras(self) -> List:
        self._main_cursor.execute('SELECT * FROM suras')
        return self._main_cursor.fetchall()

    def get_sura_no_by_page(self, page_no: int) -> int:
        query = f'SELECT sura FROM {self._pages_type} WHERE page=? LIMIT 1'
        self._pages_cursor.execute(query, (page_no,))
        return self._pages_cursor.fetchone()[0]

    def get_sura_no_by_juz(self, juz_no: int) -> int:
        self._main_cursor.execute('SELECT sura FROM juzs WHERE id=?',
                                  (juz_no,))
        return self._main_cursor.fetchone()[0]

    def get_aya_no_by_page(self, page_no: int) -> int:
        query = f'SELECT aya FROM {self._pages_type} WHERE page=? AND ' \
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

    def get_juz_no(self, sura_no: int, aya_no: int) -> int:
        self._main_cursor.execute('SELECT id FROM juzs WHERE (sura=? AND '
                                  'aya<=?) OR sura<? ORDER BY id DESC LIMIT 1',
                                  (sura_no, aya_no, sura_no))
        return self._main_cursor.fetchone()[0]

    def get_hizb_no(self, sura_no: int, aya_no: int) -> int:
        # hizbs = self._metadata.find('hizbs').findall('hizb')
        return 1
