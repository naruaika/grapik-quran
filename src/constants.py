# constants.py
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
from os import path


# Must be defined by main.py
APPLICATION_NAME: str = ''
APPLICATION_VERSION: str = ''

APPLICATION_ID = 'org.grapik.Quran'
RESOURCE_PATH = '/org/grapik/Quran'
USER_DATA_PATH = path.join(GLib.get_user_data_dir(), 'grapik-quran')

PAGE_MARGIN = 20  # in pixel
PAGE_ZOOM_STEP = 10  # in percent
