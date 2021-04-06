# animation.py
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

from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk


class Animation(Gtk.Application):

    @staticmethod
    def ease_out_cubic(t) -> float:
        p = t - 1
        return p*p*p + 1

    @staticmethod
    def scroll_to(
            scroll: Gtk.ScrolledWindow,
            target: Gtk.Widget,
            duration: int = 600) -> None:
        """Animate the scroll for duration in milliseconds."""
        target = target.get_allocation()
        adjustment = scroll.get_vadjustment()
        start_point = adjustment.get_value()

        page_size = adjustment.get_page_size()
        if start_point <= target.y \
                and (target.y+target.height) <= (start_point+page_size):
            # If all parts of the target widget content are visible,
            # no need to animate the scroll.
            return
        else:
            if target.y > start_point:
                # If the height of the target widget is greater than the
                # height of its container, scroll to the top-left coordinates
                # of the widget. Otherwise, scroll to the bottom-right
                # coordinates of the widget.
                if target.height > page_size:
                    end_point = target.y
                else:
                    end_point = min(adjustment.get_upper()-page_size,
                                    target.y+target.height-page_size)
            else:
                end_point = target.y

            # Stop the current animating when the same widget requested to be
            # animated again before it has finished animating
            scroll.end_point = end_point

        frame_clock = scroll.get_frame_clock()
        start_time = frame_clock.get_frame_time()
        end_time = start_time + 1000*duration

        def animate(
                widget: Gtk.Widget,
                frame_clock: Gdk.FrameClock) -> bool:
            current_time = frame_clock.get_frame_time()
            if current_time < end_time \
                    and adjustment.get_value() != end_point \
                    and widget.end_point == end_point:
                t = (current_time-start_time) / (end_time-start_time)
                t = Animation.ease_out_cubic(t)
                adjustment.set_value(start_point + t*(end_point-start_point))
                return GLib.SOURCE_CONTINUE
            else:
                return GLib.SOURCE_REMOVE

        scroll.add_tick_callback(animate)

    @staticmethod
    def to_invisible(
            widget: Gtk.Widget,
            duration: int = 600) -> None:
        """Animate the opacity from 1 to 0 for duration in milliseconds."""
        frame_clock = widget.get_frame_clock()
        start_time = frame_clock.get_frame_time()
        end_time = start_time + 1000*duration

        # Stop the current animating when the same widget requested to be
        # animated again before it has finished animating
        widget.animate = False

        def animate(
                widget: Gtk.Widget,
                frame_clock: Gdk.FrameClock) -> bool:
            widget.animate = True

            current_time = frame_clock.get_frame_time()
            if current_time < end_time \
                    and 0 < widget.get_opacity() \
                    and widget.animate:
                t = (current_time-start_time) / (end_time-start_time)
                t = 1 - Animation.ease_out_cubic(t)
                widget.set_opacity(t)
                return GLib.SOURCE_CONTINUE
            else:
                return GLib.SOURCE_REMOVE

        widget.add_tick_callback(animate)
