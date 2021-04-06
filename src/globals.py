# globals.py
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


"""Application variables

This module must be imported by other modules that have at least one class that
needs to communicate with other classes in other modules or have at least one
variable that needs to be saved as a user setting.
"""
musshaf_name: str = None
tarajem_names: List = None
telaawa_name: str = None

page_scale: float = None
dual_page: bool = None
show_tarajem: bool = None

page_number: int = None
surah_number: int = None
ayah_number: int = None
juz_number: int = None
hizb_number: int = None
quarter_number: int = None

# These are not savable variables, but rather variables used to reduce
# computational cost
page_focused: int = None
