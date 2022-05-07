import re
from urllib.parse import urlparse


class PromptUI:

    def __init__(self, title=None, prompt=None, choices=None, data=None,
                 raw_data=True):
        """
        Gets data of the prompt will shown
        :param title: first row, should give an info about the prompt, optional
        :param prompt: the text before the input, optional
        :param choices: the choices of the prompt, optional
        :param data: the initial data if not wanted to show input, optional
        """
        self._data = data
        self._valid = False
        self._raw_data = raw_data
        self.title = title
        self.prompt = prompt
        self.choices = choices

        if self.choices:
            self._set_choices()

    def _set_choices(self):
        if isinstance(self.choices, (list, tuple)):
            self.choices = self._get_list()
        elif isinstance(self.choices, dict):
            pass
        else:
            raise TypeError('choices must be a list or a dict, not %s' % type(self.choices))

    def list_choices(self):
        for k, v in self.choices.items():
            print(f'{k}. {v}')

    def _get_title(self):
        return self.title

    def _get_prompt(self):
        return self.prompt

    def _get_list(self):
        return {str(i): c for i, c in enumerate(self.choices)}

    def get_input(self, show_text=True):
        self._valid = False
        prompt = self._get_prompt()
        prompt_message = ''
        if prompt and show_text:
            prompt_message = prompt
        self._data = input(prompt_message).strip()
        self._normalize_data()

    def _normalize_data(self):
        pass

    def is_valid(self):
        if self.choices:
            if self._data in self.choices:
                self._valid = True
            else:
                self._valid = False
        else:
            self._valid = True
        return self._valid

    @property
    def data(self):
        if self._valid:
            if self.choices and not self._raw_data:
                return self.choices[self._data]
            else:
                return self._data
        else:
            raise ValueError('the data is not valid')

    def render(self):
        title = self._get_title()
        if title:
            print(title)

        if self.choices:
            self.list_choices()


class PromptURL(PromptUI):

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


class PromptCategory(PromptUI):

    def _normalize_data(self):
        try:
            source_selections = {source_selection for source_selection in self._data.split(',')}
            if '0' in source_selections:
                source_selections.update(self.choices.keys())
                source_selections.discard('0')
            source_selections = {int(i) for i in source_selections}
            negatives = set([i for i in source_selections if i < 0])
            discarded_positives = set([abs(i) for i in negatives])
            source_selections -= negatives | discarded_positives
            source_selections = {str(i) for i in source_selections}
            self._data = ', '.join(source_selections)
        except ValueError:
            pass

    def is_valid(self):
        if self.choices:
            try:
                if self._data and set(self._data.split(', ')).issubset(set(self.choices.keys())):
                    self._valid = True
                else:
                    self._valid = False
            except ValueError:
                self._valid = False
        else:
            self._valid = True
        return self._valid

    @property
    def data(self):
        if self._valid:
            if self.choices and not self._raw_data:
                return [self.choices[i] for i in self._data.split(', ')]
            else:
                return self._data.split(', ')
        else:
            raise ValueError('the data is not valid')
