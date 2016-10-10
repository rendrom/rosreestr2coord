from __future__ import print_function

import json
import os

CATALOG_VERSION = "1"  # Version of cache file structure


class Catalog:
    def __init__(self, file_path):

        self.file_path = file_path
        self.local_file = None
        self.store = None

        self.open()

    def open(self, buffering=-1):
        if not os.path.isfile(self.file_path):
            self.store = {"version": CATALOG_VERSION, "Area": {}}
            with open(self.file_path, "w", buffering=buffering) as local_file:
                json.dump(self.store, local_file)
        else:
            with open(self.file_path, "r", buffering=buffering) as local_file:
                data = json.load(local_file)
                if data["version"] != CATALOG_VERSION:
                    raise Exception("Catalog version mismatch")
                else:
                    self.store = data
        return self

    def read(self):
        return self.store

    def find(self, code):
        if self.store and self.store["Area"] and code in self.store["Area"]:
            return self.store["Area"][code]
        return False

    def update(self, area):
        if self.store and "Area" in self.store:
            to_store = {}
            attr_list = getattr(area, "save_attrs")
            for a in attr_list:
                to_store[a] = getattr(area, a)
            self.store["Area"][getattr(area, "code")] = to_store
            return to_store

    def close(self, buffering=-1):
        with open(self.file_path, "w", buffering=buffering) as local_file:
            json.dump(self.store, local_file)
