
import datetime
import logging
from contextlib import closing

import numpy as np

_AAA_spline_logger = logging.getLogger('satkit.AAA_splines')

def parse_spline_line(line):
    """Parse a single line in an old AAA spline export file."""
    # This relies on none of the fields being empty and is necessary to be
    # able to process AAA's output which sometimes has extra tabs.
    cells = line.split('\t')
    token = {'id': cells[0],
             'date_and_time': datetime.strptime(
        cells[1],
        '%m/%d/%Y %I:%M:%S %p'),
        'sample_time': float(cells[2]),
        'prompt': cells[3],
        'nro_spline_points': int(cells[4]),
        'beg': 0, 'end': 42}

    # token['x'] = np.fromiter(cells[8:8+token['nro_spline_points']:2], dtype='float')
    # token['y'] = np.fromiter(cells[9:9+token['nro_spline_points']:2], dtype='float')

    #    temp = [token['x'], token['y']]
    #    nans = np.sum(np.isnan(temp), axis=0)
    #    print(token['prompt'])
    #    print('first ' + str(nans[::-1].cumsum(0).argmax(0)))
    #    print('last ' + str(nans.cumsum(0).argmax(0)))

    token['r'] = np.fromiter(
        cells[5: 5 + token['nro_spline_points']],
        dtype='float')
    token['phi'] = np.fromiter(
        cells
        [5 + token['nro_spline_points']: 5 + 2 * token['nro_spline_points']],
        dtype='float')
    token['conf'] = np.fromiter(
        cells
        [5 + 2 * token['nro_spline_points']: 5 + 3 * token
         ['nro_spline_points']],
        dtype='float')
    token['x'] = np.multiply(token['r'], np.sin(token['phi']))
    token['y'] = np.multiply(token['r'], np.cos(token['phi']))

    return token


def retrieve_splines(filename):
    """
    Read all splines from the file.
    """
    with closing(open(filename, 'r',encoding="utf8")) as splinefile:
        splinefile.readline()  # Discard the headers on first line.
        table = [parse_spline_line(line) for line in splinefile.readlines()]

    _AAA_spline_logger.info("Read file %s.", filename)
    return table


def add_splines_from_file(recording_list, spline_file):
    """
    Add a Spline data object to each recording.

    The splines are read from a single AAA export file and added to
    the correct Recording by identifying the Recordings based on the date
    and time of the original recording. If no splines are found for a
    given Recording, an empty Spline object will be attached to it.

    Arguments:
    recording_list -- a list of Recording objects
    spline_file -- an AAA export file containing splines

    Return -- None. Recordings are modified in place.
    """
    # select the right recording here - we are accessing a database.
    # splines = retrieve_splines(token['spline_file'], token['prompt'])
    # splines = retrieve_splines('annd_sample/File003_splines.csv',
    #                            token['prompt'])
    raise NotImplementedError(
        "Adding splines nor the Spline modality have not yet been implemented.")
    # if spline_file:
    #     splines = retrieve_splines(spline_file)
    #     for token in recording_list:
    #         table = [
    #             row for row in splines
    #             if row['date_and_time'] == token['date_and_time']]
    #         token['splines'] = table
    #         _AAA_logger.debug(
    #             token['prompt'] + ' has ' + str(len(table)) + 'splines.')
    #
    # return recording_list