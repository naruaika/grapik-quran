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

from __future__ import annotations
from abc import ABC
from gi.repository import GLib
from os import path
from typing import List
import sqlite3

from . import globals as glo
from .constants import USER_DATA_PATH


class Model(ABC):

    _database_filepath = None

    @property
    def database_filepath(self) -> str:
        return self._database_filepath

    @database_filepath.setter
    def database_filepath(
            self,
            filepath: str) -> None:
        self._database_filepath = filepath

    def __enter__(self) -> Model:
        self.connection = sqlite3.connect(self._database_filepath)
        self.cursor = self.connection.cursor()
        return self

    def __exit__(
            self,
            type,
            value,
            traceback) -> None:
        self.connection.close()


class Metadata(Model):

    def __init__(self) -> None:
        self.database_filepath = path.join(
            path.dirname(path.abspath(__file__)), 'main.db')

    def get_musshafs(self) -> List:
        self.cursor.execute('SELECT * FROM musshaf ORDER BY name')
        return self.cursor.fetchall()

    def get_musshaf(
            self) -> List:
        self.cursor.execute('SELECT * FROM musshaf WHERE id=?',
                            (glo.musshaf_name,))
        return self.cursor.fetchone()

    def get_surahs(self) -> List:
        self.cursor.execute('SELECT * FROM suras')
        return self.cursor.fetchall()

    def get_surah_length(
            self,
            surah_no: int) -> int:
        # TODO: obtain the aya numbering after shifting
        self.cursor.execute('SELECT ayas FROM suras WHERE id=?', (surah_no,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_surah_no(
            self,
            juz_no: int = None,
            hizb_no: int = None) -> int:
        if juz_no:
            self.cursor.execute('SELECT sura FROM juzs WHERE id=?', (juz_no,))
            result = self.cursor.fetchone()
        else:
            self.cursor.execute('SELECT sura FROM hizbs WHERE id=?',
                                (hizb_no,))
            result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_surah_name(
            self,
            surah_no: int) -> int:
        query = f'SELECT tname FROM suras WHERE id=?'
        self.cursor.execute(query, (surah_no,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_ayah_no(
            self,
            juz_no: int = None,
            hizb_no: int = None) -> int:
        if juz_no:
            self.cursor.execute('SELECT aya FROM juzs WHERE id=?', (juz_no,))
            result = self.cursor.fetchone()
        else:
            self.cursor.execute('SELECT aya FROM hizbs WHERE id=?', (hizb_no,))
            result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_juz_no(
            self,
            surah_no: int,
            ayah_no: int) -> int:
        self.cursor.execute('SELECT id FROM juzs WHERE (sura=? AND aya<=?) OR '
                            'sura<? ORDER BY id DESC',
                            (surah_no, ayah_no, surah_no))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_hizb_no(
            self,
            surah_no: int,
            ayah_no: int) -> int:
        self.cursor.execute('SELECT id FROM hizbs WHERE (sura=? AND aya<=?) OR'
                            ' sura<? ORDER BY id DESC',
                            (surah_no, ayah_no, surah_no))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_tarajems(self) -> List:
        self.cursor.execute('SELECT * FROM tarajem ORDER BY language')
        return self.cursor.fetchall()

    def get_tarajem(
            self,
            tarajem_id: str) -> List:
        self.cursor.execute('SELECT * FROM tarajem WHERE id=?', (tarajem_id,))
        return self.cursor.fetchone()

    def get_telaawas(self) -> List:
        self.cursor.execute('SELECT * FROM telaawa ORDER BY qiraat, qaree, '
                            'bitrate, style ASC')
        return self.cursor.fetchall()

    def get_telaawa(
            self,
            telaawa_id: str) -> List:
        self.cursor.execute('SELECT * FROM telaawa WHERE id=?', (telaawa_id,))
        return self.cursor.fetchone()


class Musshaf(Model):

    def __init__(self) -> None:
        self.database_filepath = path.join(USER_DATA_PATH, 'musshaf.db')

    def is_musshaf_exist(
            self,
            musshaf_name: str) -> bool:
        self.cursor.execute('SELECT name FROM sqlite_master WHERE name=?',
                            (musshaf_name,))
        if self.cursor.fetchone():
            return True
        return False

    def get_page_no(
            self,
            surah_no: int,
            ayah_no: int) -> int:
        if not self.is_musshaf_exist(glo.musshaf_name):
            return -1
        query = f'SELECT page FROM {glo.musshaf_name} WHERE sura=? AND aya=?' \
            ' ORDER BY id DESC'
        self.cursor.execute(query, (surah_no, ayah_no))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_surah_no(
            self,
            page_no: int) -> int:
        query = f'SELECT sura FROM {glo.musshaf_name} WHERE page=?'
        self.cursor.execute(query, (page_no,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_ayah_no(
            self,
            page_no: int) -> int:
        query = f'SELECT aya FROM {glo.musshaf_name} WHERE page=?'
        self.cursor.execute(query, (page_no,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_bboxes(
            self,
            page_no: int) -> List:
        if not self.is_musshaf_exist(glo.musshaf_name):
            return -1
        query = 'SELECT sura, aya, x1, y1, x2-x1, y2-y1 FROM ' \
            f'{glo.musshaf_name} WHERE page=?'
        self.cursor.execute(query, (page_no,))
        return self.cursor.fetchall()


class Tarajem(Model):

    def __init__(self) -> None:
        self.database_filepath = path.join(USER_DATA_PATH, 'tarajem.db')

    def is_tarajem_exist(
            self,
            tarajem_name: str) -> bool:
        self.cursor.execute('SELECT name FROM sqlite_master WHERE name=?',
                            (tarajem_name,))
        if self.cursor.fetchone():
            return True
        return False

    def get_tarajem_text(
            self,
            tarajem_name: str,
            surah_no: int,
            ayah_no: int) -> List:
        if self.is_tarajem_exist(tarajem_name):
            query = f'SELECT sura, aya, text FROM {tarajem_name} WHERE ' \
                'sura=? AND aya=?'
            self.cursor.execute(query, (surah_no, ayah_no))
            return self.cursor.fetchone()
        return []
