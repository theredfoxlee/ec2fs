""" This module contains guarded_kv_store class. """


import collections
import json
import time
import typing

from readerwriterlock import rwlock


class guarded_kv_store:
    """ This class utilizes python's dict to create thread safe key-value store.

        Note that values are returned as shallow copy - reckless use of these values
            might waste thread safety of this class.
    """

    def __init__(self, dict_cls: typing.Type = dict) -> None:
        self._dict = dict_cls()
        self._guard = rwlock.RWLockWrite()

    def __len__(self) -> int:
        with self._guard.gen_rlock():
            return len(self._dict)

    def __contains__(self, key: typing.Hashable) -> bool:
        with self._guard.gen_rlock():
            return key in self._dict 

    def insert(self, key: typing.Hashable, value: dict) -> None:
        """ Add/Overwrite value of key. """
        with self._guard.gen_wlock():
            self._insert(key, value)

    def remove(self, key: typing.Hashable) -> None:
        """ Remove value of key. """
        with self._guard.gen_wlock():
            del self._dict[key]

    def get(self, key: typing.Hashable, default: typing.Any = None) -> dict:
        """ Get value of key or default if key does not exist. """
        with self._guard.gen_rlock():
            return self._dict.get(key, default)

    def bulk_insert(self, entries: typing.List[typing.Tuple[typing.Hashable, typing.Any]]) -> None:
        """ Add/Overwrite given (key,value) entries. """ 
        with self._guard.gen_wlock():
            for key, value in entries:
                self._insert(key, value)

    def bulk_remove(self, keys: typing.List[typing.Hashable], key_error_ok: bool = False) -> None:
        """ Remove valaues of given keys (ignore errors if `key_error_ok` specified). """ 
        with self._guard.gen_rlock():
            for key in keys:
                try:
                    del self._dict[key]
                except KeyError:
                    if not key_error_ok:
                        raise

    def bulk_get(self, keys: typing.Optional[typing.List[typing.Hashable]] = None, key_error_ok: bool = False) -> typing.List[dict]:
        """ Get vlue of given keys (ignore errors if `key_error_ok` specified). """
        with self._guard.gen_rlock():
            if keys:
                ret = {}
                for key in keys:
                    try:
                        ret[key] = self._dict[key]
                    except KeyError:
                        if not key_error_ok:
                            raise
                return ret
            else:
                return dict(self._dict)

    def bulk_update(self, entries: typing.List[typing.Tuple[typing.Hashable, dict]]) -> None:
        """ Assume inner structure is dict and update its values in bulk request. """
        with self._guard.gen_wlock():
            for key, value in entries:
                self._update(self._dict[key], value)

    def _insert(self, key: typing.Hashable, value: dict) -> None:
        """ Insert/Overwrite given (key, value) entry nad setup timestamps. """
        timestamp = time.time()
        raw_data = json.dumps(value, default=str).encode()
        if key in self._dict:
            self._dict[key]['data'] = value
            self._dict[key]['raw_data'] = raw_data
            self._dict[key]['metadata']['@updated_timestamp'] = timestamp
            self._dict[key]['metadata']['size'] = len(raw_data)
        else:
            self._dict[key] = {
                'data': value,
                'raw_data': raw_data,
                'metadata': {
                    '@created_timestamp': timestamp,
                    '@updated_timestamp': timestamp,
                    'size': len(raw_data)
                }
            }

    def _update(self, d, u):
        """ Update nested dict - taken from stackoverflow. """
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self._update(d.get(k, {}), v)
            else:
                d[k] = v
        return d