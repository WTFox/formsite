from pprint import pprint

from fs_wrapper import FormSite
from config import FS_CRED

__author__ = 'afox'

USER = FS_CRED.USER
API_KEY = FS_CRED.API

def main():
    fs = FormSite(USER, API_KEY)
    print("{} forms".format(len(fs)))
    for form in fs:
        if form.results:
            print(form, len(form.results))
            for res in form.results:
                print(res)
                if res.form_completed:
                    pprint(res.items)



if __name__ == '__main__':
    main() 