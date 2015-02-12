import json
import os
import re
from icu import Locale, Collator, UnicodeString


class IndexedCollation:

    def __init__(self, iso639_3):
        try:
            with open(os.path.join(os.path.dirname(__file__), 'data/{language}.json'.format(language=iso639_3)), 'r') as f:
                self.spec = json.load(f)
        except IOError:
            with open(os.path.join(os.path.dirname(__file__), 'data/{language}.json'.format(language='eng')), 'r') as f:
                self.spec = json.load(f)

    @property
    def section_titles(self):
        return self.spec.get('section_titles', self.spec.get('index_titles'))

    @property
    def index_titles(self):
        return self.spec.get('index_titles', self.spec.get('section_titles'))

    @property
    def start_strings(self):
        return self.spec.get('start_strings', [self.to_lowercase(title) for title in self.index_titles])

    @property
    def section_classes(self):
        return self.spec.get('section_classes', [0 for _ in self.section_titles])

    @property
    def locale(self):
        return Locale(self.spec['collation'])

    @property
    def collator(self):
        return Collator.createInstance(self.locale)

    def sections(self, iterable, key=None):
        # Create sections
        sections = []
        for index_title, section_title in zip(self.index_titles, self.section_titles):
            sections.append((index_title, section_title, []))

        # Populate sections
        compare = self.collator.compare
        for obj in sorted(iterable, cmp=compare, key=lambda obj: self.transformed_for_sorting(obj, key=key)):
            sections[self.section(obj, cmp=compare, key=key)][2].append(obj)

        # Remove unused classes of sections
        used_classes = set([self.section_classes[i] for i, section in enumerate(sections) if len(section[2]) > 0])
        sections = [section for i, section in enumerate(sections) if self.section_classes[i] in used_classes]

        return sections

    def section(self, obj, cmp, key=None):
        # Change to lowercase, under the assumption that the start_strings are lowercase
        value = self.to_lowercase(self.transformed_for_sorting(obj, key=key))

        start_strings = self.start_strings
        for i, start_string in enumerate(start_strings):
            if i == 0:
                continue

            if cmp(value, start_string) < 0:
                return i - 1

        return len(start_strings) - 1

    def transformed_for_sorting(self, obj, key=None):
        value = key(obj) if key else obj
        # Strip leading punctuation for sorting
        value = re.sub(r'^\W+', '', value, flags=re.UNICODE)
        return value

    def to_lowercase(self, value):
        return unicode(UnicodeString(value).toLower(self.locale))