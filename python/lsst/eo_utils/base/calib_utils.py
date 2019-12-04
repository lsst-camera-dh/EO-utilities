"""This contains code to read a yaml file to define calibration 'flavors'
which provide a single key for a set of calibration options
"""

import yaml

from lsst.eo_utils.base.defaults import DEFAULT_CALIB_FILE


def _find_value_by_key(a_dict, key):
    """Find a key and return it, with a flag saying if it was found"""
    try:
        val = a_dict[key]
    except KeyError:
        return (False, None)
    return (True, val)


def _find_value_by_task_and_key(a_dict, task_name, key):
    """Find a key and return it, with a flag saying if it was found"""
    try:
        sub_dict = a_dict[task_name]
    except KeyError:
        return (False, None)
    return _find_value_by_key(sub_dict, key)


class CalibDict:
    """A small helper class define calibration 'flavors' which can be used
    to wrap together a group of calibration options"""
    def __init__(self, yamlfile):
        """C'tor from a yaml file"""
        o_dict = yaml.safe_load(open(yamlfile))
        self._global_defaults = o_dict.pop('defaults')
        self._calib_dict = o_dict.copy()

    def get_flavors(self):
        """Get the list for flavors"""
        return self._calib_dict.keys()

    def get_calib_value_task(self, flavor, task_name, key):
        """Get the value for calibration parameter from a particular task and flavor"""
        if flavor not in self._calib_dict:
            raise KeyError("Calibration flavor %s not defined.  Options are %s" %\
                               (flavor, str(self._calib_dict.keys())))

        flavor_data = self._calib_dict[flavor]

        found, val = _find_value_by_task_and_key(flavor_data, task_name, key)
        if found:
            return val
        found, val = _find_value_by_task_and_key(flavor_data, "default", key)
        if found:
            return val
        found, val = _find_value_by_key(self._global_defaults, key)
        if found:
            return val
        raise KeyError("Key %s is not defined for task %s, in defaults for flavor %s or in global defaults" %
                       (key, task_name, flavor))


DEFAULT_CALIB_DICT = CalibDict(DEFAULT_CALIB_FILE)


if __name__ == '__main__':

    TRIPLETS = [('normal', 'xx', 'bias'),
                ('normal', 'xx', 'dummy'),
                ('normal', 'FlatPair', 'mask'),
                ('dummy', 'xx', 'mask')]

    for triplet in TRIPLETS:
        try:
            value = DEFAULT_CALIB_DICT.get_calib_value_task(triplet[0], triplet[1], triplet[2])
            print("%s -> %s" % (str(triplet), value))
        except KeyError as msg:
            print(msg)
