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
from os import path
from typing import Union
import re
import sqlite3

from . import constants as const
from . import globals as glob


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

        def regexp(
                expr: str,
                item: str) -> bool:
            return re.search(expr, item) is not None
        self.connection.create_function('REGEXP', 2, regexp)

        return self

    def __exit__(
            self,
            type,
            value,
            traceback) -> None:
        self.connection.close()


class Metadata(Model):

    def __init__(self) -> None:
        self.database_filepath = \
            path.join(path.dirname(path.abspath(__file__)), 'main.db')

    def get_musshafs(self) -> list:
        self.cursor.execute('SELECT * FROM musshaf ORDER BY name')
        return self.cursor.fetchall()

    def get_musshaf(self) -> list:
        self.cursor.execute('SELECT * FROM musshaf WHERE id=?',
                            (glob.musshaf_name,))
        return self.cursor.fetchone()

    def get_surahs(self) -> list:
        self.cursor.execute('SELECT * FROM suras')
        return self.cursor.fetchall()

    def get_surah_length(
            self,
            surah_no: int) -> int:
        self.cursor.execute('SELECT ayas FROM suras WHERE id=?', (surah_no,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_surah_no(
            self,
            juz_no: int = None,
            hizb_no: int = None,
            manzil_no: int = None,
            ruku_no: int = None) -> int:
        if hizb_no:
            self.cursor.execute('SELECT sura FROM hizbs WHERE id=?',
                                (hizb_no,))
        elif manzil_no:
            self.cursor.execute('SELECT sura FROM manzils WHERE id=?',
                                (manzil_no,))
        elif ruku_no:
            self.cursor.execute('SELECT sura FROM rukus WHERE id=?',
                                (ruku_no,))
        else:
            self.cursor.execute('SELECT sura FROM juzs WHERE id=?', (juz_no,))
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
            hizb_no: int = None,
            manzil_no: int = None,
            ruku_no: int = None) -> int:
        if hizb_no:
            self.cursor.execute('SELECT aya FROM hizbs WHERE id=?', (hizb_no,))
        elif manzil_no:
            self.cursor.execute('SELECT aya FROM manzils WHERE id=?',
                                (manzil_no,))
        elif ruku_no:
            self.cursor.execute('SELECT aya FROM rukus WHERE id=?', (ruku_no,))
        else:
            self.cursor.execute('SELECT aya FROM juzs WHERE id=?', (juz_no,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_ayah_texts(
            self,
            query: str) -> list:
        self.cursor.execute('SELECT sura, aya, text FROM texts WHERE text LIKE'
                            ' ?', ('%'+query+'%',))
        return self.cursor.fetchall()

    def get_ayah_text(
            self,
            musshaf_name: str,
            surah_no: int = -1,
            ayah_no: int = -1,
            text_id: int = None) -> Union[list,str]:
        if text_id:
            self.cursor.execute('SELECT sura, aya, text FROM texts WHERE id=?',
                                (text_id,))
            return self.cursor.fetchall()
        else:
            self.cursor.execute('SELECT text FROM texts WHERE sura=? AND aya=?',
                                (surah_no, ayah_no))
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

    def get_manzil_no(
            self,
            surah_no: int,
            ayah_no: int) -> int:
        self.cursor.execute('SELECT id FROM manzils WHERE (sura=? AND aya<=?) '
                            'OR sura<? ORDER BY id DESC',
                            (surah_no, ayah_no, surah_no))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_ruku_no(
            self,
            surah_no: int,
            ayah_no: int) -> int:
        self.cursor.execute('SELECT id FROM rukus WHERE (sura=? AND aya<=?) OR'
                            ' sura<? ORDER BY id DESC',
                            (surah_no, ayah_no, surah_no))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_tarajems(self) -> list:
        self.cursor.execute('SELECT * FROM tarajem ORDER BY language')
        return self.cursor.fetchall()

    def get_tarajem(
            self,
            tarajem_id: str) -> list:
        self.cursor.execute('SELECT * FROM tarajem WHERE id=?', (tarajem_id,))
        return self.cursor.fetchone()

    def get_telaawas(self) -> list:
        self.cursor.execute('SELECT * FROM telaawa ORDER BY qiraat, qaree, '
                            'bitrate, style ASC')
        return self.cursor.fetchall()

    def get_telaawa(
            self,
            telaawa_id: str) -> list:
        self.cursor.execute('SELECT * FROM telaawa WHERE id=?', (telaawa_id,))
        return self.cursor.fetchone()

    def get_titles(self) -> list:
        self.cursor.execute('SELECT sura, aya, title FROM titles')
        return self.cursor.fetchall()


class Musshaf(Model):

    def __init__(self) -> None:
        self.database_filepath = path.join(const.USER_DATA_PATH, 'musshaf.db')

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
        if not self.is_musshaf_exist(glob.musshaf_name):
            return -1
        query = f'SELECT page FROM {glob.musshaf_name} WHERE sura=? AND aya=?' \
            ' ORDER BY id DESC'
        self.cursor.execute(query, (surah_no, ayah_no))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_translated_page_no(
            self,
            musshaf_src_name: str,
            musshaf_dest_name: str,
            page_no: int) -> int:
        if not self.is_musshaf_exist(musshaf_src_name) \
            or not self.is_musshaf_exist(musshaf_dest_name):
            return -1

        query = f'SELECT sura, aya FROM {musshaf_src_name} WHERE page=?'
        self.cursor.execute(query, (page_no,))
        result = self.cursor.fetchone()
        if result:
            surah_no, ayah_no = result[0]
        else:
            return -1

        query = f'SELECT page FROM {musshaf_dest_name} WHERE sura=? AND aya=?' \
            ' ORDER BY id DESC'
        self.cursor.execute(query, (surah_no, ayah_no))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_surah_no(
            self,
            page_no: int) -> int:
        query = f'SELECT sura FROM {glob.musshaf_name} WHERE page=?'
        self.cursor.execute(query, (page_no,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_ayah_no(
            self,
            page_no: int) -> int:
        query = f'SELECT aya FROM {glob.musshaf_name} WHERE page=?'
        self.cursor.execute(query, (page_no,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return -1

    def get_bboxes(
            self,
            page_no: int) -> list:
        if not self.is_musshaf_exist(glob.musshaf_name):
            return -1
        query = 'SELECT sura, aya, x1, y1, x2-x1, y2-y1 FROM ' \
            f'{glob.musshaf_name} WHERE page=?'
        self.cursor.execute(query, (page_no,))
        return self.cursor.fetchall()


class Tarajem(Model):

    def __init__(self) -> None:
        self.database_filepath = path.join(const.USER_DATA_PATH, 'tarajem.db')

    def is_tarajem_exist(
            self,
            tarajem_name: str) -> bool:
        self.cursor.execute('SELECT name FROM sqlite_master WHERE name=?',
                            (tarajem_name,))
        if self.cursor.fetchone():
            return True
        return False

    def get_tarajem_texts(
            self,
            tarajem_name: str,
            search_query: str,
            case_sensitive: bool = False,
            match_whole_word: bool = False) -> list:
        if self.is_tarajem_exist(tarajem_name):
            if case_sensitive:
                self.cursor.execute('PRAGMA case_sensitive_like = true;')
            else:
                search_query = search_query.lower()
            query = f'SELECT sura, aya, text FROM {tarajem_name} '
            if match_whole_word:
                query = query + 'WHERE text REGEXP ?'
                self.cursor.execute(query, (r'\b'+search_query+r'\b',))
            else:
                query = query + 'WHERE text LIKE ?'
                self.cursor.execute(query, ('%'+search_query+'%',))
            return self.cursor.fetchall()
        return []

    def get_tarajem_text(
            self,
            tarajem_name: str,
            surah_no: int,
            ayah_no: int) -> list:
        if self.is_tarajem_exist(tarajem_name):
            query = f'SELECT sura, aya, text FROM {tarajem_name} WHERE ' \
                'sura=? AND aya=?'
            self.cursor.execute(query, (surah_no, ayah_no))
            return self.cursor.fetchone()
        return []
