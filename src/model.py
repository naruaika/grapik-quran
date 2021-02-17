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
import xml.etree.ElementTree as etree
import gi

gi.require_version('Gio', '2.0')

from gi.repository import Gio

class Model:

    # Databases
    # FIXME: for best performance, use SQLite instead
    _map = etree.fromstring(Gio.resources_lookup_data(
        '/org/naruaika/Quran/res/db/map.xml', 0).get_data())

    def get_page_no(self, sura_no: int, aya_no: int) -> int:
        pages = self._map.find('pages').findall('page')
        for page in reversed(pages):
            if sura_no == int(page.get('sura')):
                if aya_no >= int(page.get('aya')):
                    return int(page.get('index'))
            elif sura_no > int(page.get('sura')):
                return int(page.get('index'))

    def get_suras(self) -> List:
        suras = self._map.find('suras').findall('sura')
        return suras

    def get_page_sura_no(self, page_no: int) -> int:
        pages = self._map.find('pages').findall('page')
        sura_no = pages[page_no - 1].get('sura')
        return int(sura_no)

    def get_juz_sura_no(self, juz_no: int) -> int:
        juzs = self._map.find('juzs').findall('juz')
        sura_no = juzs[juz_no - 1].get('sura')
        return int(sura_no)

    def get_page_aya_no(self, page_no: int) -> int:
        pages = self._map.find('pages').findall('page')
        aya_no = pages[page_no - 1].get('aya')
        return int(aya_no)

    def get_juz_aya_no(self, juz_no: int) -> int:
        juzs = self._map.find('juzs').findall('juz')
        aya_no = juzs[juz_no - 1].get('aya')
        return int(aya_no)

    def get_aya_no_max(self, sura_no: int) -> int:
        suras = self._map.find('suras').findall('sura')
        aya_no_max = suras[sura_no - 1].get('ayas')
        return int(aya_no_max)

    def get_juz_no(self, sura_no: int, aya_no: int) -> int:
        juzs = self._map.find('juzs').findall('juz')
        for juz in reversed(juzs):
            if sura_no == int(juz.get('sura')):
                if aya_no >= int(juz.get('aya')):
                    return int(juz.get('index'))
            elif sura_no > int(juz.get('sura')):
                return int(juz.get('index'))

    def get_hizb_no(self, sura_no: int, aya_no: int) -> int:
        # hizbs = self._map.find('hizbs').findall('hizb')
        return 1
