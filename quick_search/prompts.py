import re
from urllib.parse import urlparse

from cli_prompts import Prompt


class PromptURL(Prompt):

    def is_valid(self):
        # https://regexr.com/39nr7
        regex = r'[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'
        if self._data and re.match(regex, self._data):
            hostname = urlparse(self._data).hostname
            if self.choices:
                if hostname in self.choices.values():
                    self._valid = True
                else:
                    self._valid = False
            else:
                self._valid = True
        else:
            self._valid = False
        return self._valid

    def render(self):
        title = self._get_title()
        if title:
            print(title)


class PromptSource(Prompt):

    def _normalize_data(self):
        try:
            source_selections = {s for s in self._data.split(',')}
            if '0' in source_selections:
                source_selections.update(self.choices.keys())
                source_selections.discard('0')
            source_selections = {int(i) for i in source_selections}
            negatives = set([i for i in source_selections if i < 0])
            discarded_positives = set([abs(i) for i in negatives])
            source_selections -= negatives | discarded_positives
            source_selections = {str(i) for i in source_selections}
            self._data = source_selections
        except ValueError:
            pass

    def is_valid(self):
        data = self._data
        if self.choices:
            if data and set(data).issubset(set(self.choices.keys())):
                self._valid = True
        else:
            self._valid = True
        return self._valid

    @property
    def data(self):
        if self._valid:
            if self.choices and not self._raw_data:
                return [self.choices[i] for i in self._data]
            else:
                return self._data
        else:
            raise ValueError('the data is not valid')
