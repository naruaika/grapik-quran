# process.py
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

import xml.etree.ElementTree as etree
import gi

gi.require_version('Gio', '2.0')

from gi.repository import Gio

class Process:

    # Databases
    db_map = etree.fromstring(Gio.resources_lookup_data(
        '/org/naruaika/Quran/res/db/map.xml', 0).get_data())

    def __init__(self) -> None:
        pass
