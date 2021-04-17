# search.py
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

from collections import Counter
from gi.repository import Gtk
from gi.repository import GObject
from os import path
from typing import List
import itertools
import re

from . import globals as glob
from . import constants as const
from .model import Metadata
from .model import Tarajem

@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/search_popover.ui')
class SearchPopover(Gtk.PopoverMenu):
    __gtype_name__ = 'SearchPopover'

    __gsignals__ = {
        'go-to-suraya': (GObject.SIGNAL_RUN_CLEANUP, None, (int, int))}

    entry = Gtk.Template.Child()
    note = Gtk.Template.Child()
    listbox = Gtk.Template.Child()
    progressbar = Gtk.Template.Child()
    scrolledwindow = Gtk.Template.Child()

    query: str = ''
    results: List = []  # store the search results to avoid unneeded
                        # refreshment of search results
    match_case: bool = False
    match_whole_word: bool = False

    def populate(
            self,
            query: str = '') -> bool:
        """Display search results

        Search everything including Musshaf unicode texts and tarajem/tafaser
        based on the user's search query. The search query should contain at
        least three characters.
        """
        # TODO: implement substring highlight
        if not query:
            query = self.query
        self.query = query

        def reset() -> None:
            def reset(row: Gtk.ListBoxRow) -> None:
                self.listbox.remove(row)
            self.listbox.foreach(reset)

        if len(query) < 3:
            self.note.hide()
            reset()
            return

        with Metadata() as metadata, \
             Tarajem() as tarajem:
            n_search_results = 0
            max_search_results = 100

            # Search for ayah by imlaei
            results = metadata.get_ayah_texts(query)

            if not results:
                # Search for ayah by phonetic
                # TODO: implement cache system
                query_phonetic = self.latin2phonetic(query)
                matched_docs = self.search_phonetic(query_phonetic)
                for matched_doc in matched_docs:
                    results += metadata.get_ayah_text(
                        glob.musshaf_name, text_id=matched_doc['document-id'])

            if not results:
                # Search for tarajem/tafaser
                for tarajem_name in glob.tarajem_names:
                    results_tarajem = tarajem.get_tarajem_texts(
                        tarajem_name, query, self.match_case,
                        self.match_whole_word)
                    results += results_tarajem

            # Compare to the previous displayed list. If they are the same,
            # do not update the display. Otherwise, save current list.
            n_search_results = len(results)
            results = results[:max_search_results]
            if self.results == results:
                return
            self.results = results

            reset()
            for result in self.results:
                text = \
                    '<span>' \
                        f'{result[-1]}' \
                    '</span>'
                label =  \
                    '<span size="small">' \
                        f'Found in Surah {metadata.get_surah_name(result[0])} ' \
                        f'({result[0]}) Ayah {result[1]}' \
                    '</span>'
                row = SearchListBoxRow(text, label)
                row.id = (result[0], result[1])
                self.listbox.add(row)

            if results:
                self.note.set_markup(
                    '<span size="small" foreground="#808080808080">'
                        'Displaying search results '
                        f'{min(max_search_results, n_search_results)} '
                        f'of {n_search_results}'
                    '</span>')
                self.note.show()

        self.listbox.show_all()

        if self.listbox.get_children():
            return True
        return False

    @Gtk.Template.Callback()
    def search(
            self,
            entry: Gtk.SearchEntry) -> None:
        query = entry.get_text()
        self.populate(query)

    @Gtk.Template.Callback()
    def match_case_toggled(
            self,
            toggle: Gtk.ToggleButton) -> None:
        self.match_case = toggle.get_active()
        self.populate()

    @Gtk.Template.Callback()
    def match_whole_word_toggled(
            self,
            toggle: Gtk.ToggleButton) -> None:
        self.match_whole_word = toggle.get_active()
        self.populate()

    @Gtk.Template.Callback()
    def select(
            self,
            listbox: Gtk.ListBox,
            listboxrow: Gtk.ListBoxRow) -> None:
        if not listboxrow:
            return
        self.emit('go-to-suraya', *listboxrow.id)

    def latin2phonetic(
            self,
            latin_text: str) -> str:
        # Normalise the latin text
        # make all characters capitalized
        latin_text = latin_text.upper()

        # replace strips with spaces
        latin_text = latin_text.replace('-', ' ')

        # remove non-alphabetic characters except ampersands and spaces
        latin_text = re.sub(r"[^A-Z'`\&\s]", '', latin_text)

        # Transform the latin text
        # remove repeated adjacent characters
        latin_text = ''.join(c[0] for c in itertools.groupby(latin_text))

        # remove duplicate adjacent two-letter-consonants
        latin_text = re.sub(r'(KH|CH|SH|TS|SY|DH|TH|ZH|DH|DZ|GH)+', r'\1',
                            latin_text)

        # replace the letters O and E since they are not in arabic
        latin_text = latin_text.replace('O', 'A')
        latin_text = latin_text.replace('E', 'I')

        # replace the diphthong from non-Arabic to Arabic
        latin_text = latin_text.replace('AI', 'AY')
        latin_text = latin_text.replace('AU', 'AW')

        # mark the hamzas
        latin_text = re.sub(r'^(A|I|U)+', r'X\1', latin_text)
        latin_text = latin_text.replace(' A', ' XA')
        latin_text = latin_text.replace(' I', ' XI')
        latin_text = latin_text.replace(' U', ' XU')
        latin_text = latin_text.replace('IA', 'IXA')
        latin_text = latin_text.replace('IU', 'IXU')
        latin_text = latin_text.replace('UA', 'UXA')
        latin_text = latin_text.replace('UI', 'UXI')

        # replace the ikhfas (NG)
        latin_text = re.sub(r'(A|I|U)NG\s?(D|F|J|K|P|Q|S|T|V|Z)+', r'\1N\2',
                            latin_text)

        # replace the iqlabs
        latin_text = re.sub(r'N\s?B', 'MB', latin_text)

        # replace the idghams
        latin_text = latin_text.replace('DUNYA', 'DUN_YA')
        latin_text = latin_text.replace('BUNYAN', 'BUN_YAN')
        latin_text = latin_text.replace('QINWAN', 'KIN_WAN')
        latin_text = latin_text.replace('KINWAN', 'KIN_WAN')
        latin_text = latin_text.replace('SINWAN', 'SIN_WAN')
        latin_text = latin_text.replace('SHINWAN', 'SIN_WAN')
        latin_text = re.sub(r'N\s?(N|M|L|R|Y|W)+', r'\1', latin_text)
        latin_text = latin_text.replace('DUN_YA', 'DUNYA')
        latin_text = latin_text.replace('BUN-YAN', 'BUNYAN')
        latin_text = latin_text.replace('KIN_WAN', 'KINWAN')
        latin_text = latin_text.replace('SIN_WAN', 'SINWAN')

        # replace two-letter-consonants
        latin_text = latin_text.replace('KH', 'H')
        latin_text = latin_text.replace('CH', 'H')
        latin_text = latin_text.replace('SH', 'S')
        latin_text = latin_text.replace('TS', 'S')
        latin_text = latin_text.replace('SY', 'S')
        latin_text = latin_text.replace('DH', 'D')
        latin_text = latin_text.replace('ZH', 'Z')
        latin_text = latin_text.replace('DZ', 'Z')
        latin_text = latin_text.replace('TH', 'T')
        latin_text = latin_text.replace('NGA', 'XNGA')
        latin_text = latin_text.replace('NGI', 'XNGI')
        latin_text = latin_text.replace('NGU', 'XNGU')
        latin_text = latin_text.replace('GH', 'G')

        # replace one-letter-consonants
        latin_text = latin_text.replace('GH', 'G')
        latin_text = latin_text.replace("'", 'X')
        latin_text = latin_text.replace("`", 'X')
        latin_text = latin_text.replace("Q", 'K')
        latin_text = latin_text.replace("K", 'K')
        latin_text = latin_text.replace("F", 'F')
        latin_text = latin_text.replace("V", 'F')
        latin_text = latin_text.replace("P", 'F')
        latin_text = latin_text.replace("J", 'Z')
        latin_text = latin_text.replace("Z", 'Z')

        # remove spaces
        latin_text = latin_text.replace(' ', '')

        return latin_text

    def search_phonetic(
            self,
            query: str,
            threshold: float = 0.8) -> List:
        module_dirpath = path.dirname(path.abspath(__file__))
        termlist_filepath = path.join(module_dirpath, 'lafzi_termlist.txt')
        postlist_filepath = path.join(module_dirpath, 'lafzi_postlist.txt')

        with open(termlist_filepath, 'r') as termlist_file, \
             open(postlist_filepath, 'r') as postlist_file:
            # create tri-grams from the query
            if len(query) == 3:
                trigrams = [query]
            else:
                trigrams = [query[i:i+3] for i in range(len(query) - 2)]

            # count each tri-gram occurence frequencies
            term_frequencies = Counter(trigrams).most_common()
            trigrams = {}
            for term, frequency in term_frequencies:
                position = query.index(term)
                trigrams[term] = (frequency, position)

            #
            termlist = {}
            for line in termlist_file:
                key, value = line.split('|')
                termlist[key] = int(value)

            #
            matched_docs = {}
            for term, (frequency, position) in trigrams.items():
                if term not in termlist:
                    continue
                postlist_file.seek(termlist[term])
                matched_postlists = postlist_file.readline().split(';')
                for postlist in matched_postlists:
                    document_id, term_frequency, term_position = \
                        postlist.split(':')
                    term_position = term_position.split(',')
                    if document_id in matched_docs:
                        matched_docs[document_id]['matched-trigrams-count'] += \
                            min(frequency, int(term_frequency))
                    else:
                        matched_docs[document_id] = {
                            'document-id': document_id,
                            'matched-trigrams-count': 1,
                            'matched-terms': {}}
                    matched_docs[document_id]['matched-terms'][term] = \
                        term_position

            # Filter matched documents by a given threshold
            min_score = threshold * (len(query) - 2)
            filtered_docs = [doc for doc in matched_docs.values()
                             if doc['matched-trigrams-count'] >= min_score]

            return filtered_docs


@Gtk.Template(resource_path=f'{const.RESOURCE_PATH}/ui/search_listboxrow.ui')
class SearchListBoxRow(Gtk.ListBoxRow):
    __gtype_name__ = 'SearchListBoxRow'

    text = Gtk.Template.Child()
    label = Gtk.Template.Child()

    def __init__(
            self,
            text: str,
            label: str,
            **kwargs) -> None:
        super().__init__(**kwargs)

        self.text.set_markup(text)
        self.label.set_markup(label)
