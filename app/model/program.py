"""Collection of tools useful in interfacing with program configs.

Note there are no database objects representing Programs, in either the
Datastore or Cloud SQL. They solely exist as hard-coded JSON config files.
"""

from importlib import import_module
import datetime
import json
import os
import pkgutil
import programs
import re

import programs


class Program():

    mocks = {}

    @classmethod
    def reset_mocks(klass):
        klass.mocks = {}

    @classmethod
    def mock_program_config(klass, label, partial_config):
        """Allow unit tests to insert data into program configs."""
        if 'label' not in partial_config:
            partial_config['label'] = label
        klass.mocks[label] = partial_config

    @classmethod
    def get_config(klass, label):
        """Returns parsed JSON definition. Raises exception if not found."""
        try:
            config = getattr(import_module('programs.' + label), 'config')
        except ImportError as e:
            # Allow unknown programs to be mocked.
            if label in klass.mocks:
                return klass.mocks[label]
            else:
                raise e

        # Allow known programs to be modified via mocks.
        # Copy the dict before mixing in the mocks so we don't change the
        # true config. This applies in unit testing where we don't want mocks
        # to persist from test to test.
        config = config.copy()
        if label in klass.mocks:
            config.update(klass.mocks[label])

        return config

    @classmethod
    def get_all_configs(klass):
        # http://stackoverflow.com/questions/487971/is-there-a-standard-way-to-list-names-of-python-modules-in-a-package
        labels = [label for _, label, _ in pkgutil.iter_modules(['programs'])]
        configs_from_modules = [
            klass.mocks.get(label, None) or klass.get_config(l)
            for l in labels
        ]
        return configs_from_modules + klass.mocks.values()

    @classmethod
    def get_current_cohort(klass, label):
        config = klass.get_config(label)
        today_str = datetime.date.today().isoformat()
        for c_label, c_config in config['cohorts'].items():
            if c_config['open_date'] <= today_str < c_config['close_date']:
                return c_config
        raise Exception("No current cohort in program config.")
