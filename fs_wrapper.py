import xml.etree.ElementTree as ET

import requests

__author__ = 'afox'


class AttributeDict(dict):
    """ Not best practice probably, but maintains dot access """
    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value
        return


class FormSite:
    """ A python wrapper for formsite.com """
    def __init__(self, user, api_key):
        self._api_key = api_key
        self._fs_server = 'fs7'
        self._fs_base_url = 'https://{}.formsite.com/api/users/{}/'.format(self._fs_server, user)
        self.user = user
        self.forms = self._get_all_forms()

    def __len__(self):
        return len(self.forms)

    def __iter__(self):
        return (form for form in self.forms)

    def __getitem__(self, item):
        return self.forms[item]

    def _call_api(self, action):
        url = self._fs_base_url + action
        params = {
            'fs_api_key': self._api_key
        }
        resp = requests.get(url, params=params)
        form_obj = ET.fromstring(resp.text) if resp.ok else None
        return form_obj

    def _get_all_forms(self):
        """ returns a list of Form objects """
        forms = self._call_api('forms').find('forms')
        return [Form(form_obj=form, server=self._fs_server, user=self.user, api_key=self._api_key) for form in forms]


class Form:
    """ pythonic interface for individual forms """

    def __init__(self, form_obj, server, user, api_key):
        self.form_obj = form_obj
        self._api_key = api_key

        self.server = server
        self.user = user
        self.form_id = self.form_obj.attrib['id']
        self.name = self.form_obj.find('name').text
        self.directory = self.form_obj.find('directory').text

    def __len__(self):
        return 7

    def __iter__(self):
        return iter(self.results)

    def __repr__(self):
        return "<{}({}) @ {}>".format(self.directory, self.user, id(self))

    def __str__(self):
        return self.name

    @property
    def status(self):
        url = 'https://{}.formsite.com/api/users/{}/forms/{}/status'.format(
            self.server,
            self.user,
            self.directory
        )
        params = {
            'fs_api_key': self._api_key
        }
        resp = requests.get(url, params=params)
        form_obj = ET.fromstring(resp.text) if resp.ok else None
        limit_items = form_obj.find('status').findall('.//limit[@type="items"]')[0]
        limit_results = form_obj.find('status').findall('.//limit[@type="results"]')[0]

        return AttributeDict({
            'state': form_obj.find("status").find('state').text,
            'last_modified': form_obj.find("status").find('last_modified').text,
            'limit_items': {
                'used': limit_items.find('used').text,
                'total': limit_items.find('total').text,
            },
            'limit_results': {
                'used': limit_results.find('used').text,
                'total': limit_results.find('total').text,
            }
        })

    @property
    def results(self):
        """ GET https://fsX.formsite.com/api/users/yourAccount/forms/yourForm/results
        :return:
        """
        _url = 'https://{}.formsite.com/api/users/{}/forms/{}/results'.format(
            self.server,
            self.user,
            self.directory
        )
        params = {
            'fs_api_key': self._api_key
        }
        resp = requests.get(_url, params=params)
        form_results_et = ET.fromstring(resp.text) if resp.ok else None
        form_results_obj = form_results_et.find('results')
        return FormResults(form_results_obj) if form_results_obj else 0


class FormResults:
    def __init__(self, results_obj):
        self.results_obj = results_obj

    def __len__(self):
        return len(self.results_obj)

    def __iter__(self):
        return iter(FormResult(r) for r in self.results_obj)


class FormResult:
    def __init__(self, fr):
        self.fr = fr
        self.form_id = fr.attrib['id']
        self.form_completed = self.meta.result_status == 'Complete'

    def __str__(self):
        return "<FormResult({}) @ {}".format(self.form_id, id(self))

    @property
    def meta(self):
        _metas = {}
        for meta in self.fr.iter('meta'):
            _metas[meta.attrib['id']] = meta.text
        return AttributeDict(_metas)

    @property
    def items(self):
        _items = {}
        if self.meta.result_status != 'Incomplete':
            for item in self.fr.find('items').iter('item'):
                item_type = item.attrib['type']
                # print(item_type)
                if item_type == 'text':
                    _items[item.attrib['id']] = item.find('value').text

                elif item_type == 'list':
                    _items[item.attrib['id']] = {i.attrib['index']: i.text for i in item.iter('value')}

        return _items


