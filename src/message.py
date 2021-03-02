# message.py
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

from gi.repository import Gtk, GLib


@Gtk.Template(resource_path='/org/naruaika/Quran/res/ui/message.ui')
class Action(Gtk.Revealer):
    __gtype_name__ = 'revealer_action'

    message = Gtk.Template.Child('message')

    def notify(self, message, timeout=5):
        self.message.set_text(message)
        self.set_reveal_child(True)

        if timeout > 0:
            GLib.timeout_add(1000, _Runner(timeout, self))


class _Runner:

    def __init__(self, timeout: int, revealer: Gtk.Revealer) -> None:
        self.timeout = timeout
        self.revealer = revealer
        self.timer = 0

    def __call__(self) -> bool:
        self.timer += 1
        # is_running
        if is_running := self.timer < self.timeout:
            self.revealer.set_reveal_child(False)
        return is_running
