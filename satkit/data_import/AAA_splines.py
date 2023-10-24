#
# Copyright (c) 2019-2023
# Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
#
# This file is part of Speech Articulation ToolKIT
# (see https://github.com/giuthas/satkit/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# The example data packaged with this program is licensed under the
# Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License. You should have received a
# copy of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International (CC BY-NC-SA 4.0) License along with the data. If not,
# see <https://creativecommons.org/licenses/by-nc-sa/4.0/> for details.
#
# When using the toolkit for scientific publications, please cite the
# articles listed in README.markdown. They can also be found in
# citations.bib in BibTeX format.
#

from collections import defaultdict
import csv
from datetime import datetime
import logging
from contextlib import closing
from pathlib import Path
from typing import Union

import numpy as np
from satkit.constants import SplineMetaData
from satkit.data_import import load_spline_import_config, SplineImportConfig
from satkit.data_structures import ModalityData, Recording

from satkit.modalities.splines import Splines

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


def parse_splines(
        lines: list,
        spline_config: SplineImportConfig) -> ModalityData:
    """
    Parse a list of lines into a ModalityData representing Splines.

    Parameters
    ----------
    lines : list
        Lines from a csv file.
    spline_config : SplineImportConfig
        satkit spline configuration which explains how to parse the lines.

    Returns
    -------
    ModalityData
        _description_
    """

    sampling_rate = 0

    timestamp_ind = spline_config.meta_columns.index(
        SplineMetaData.TIME_IN_RECORDING)
    timevector = [(line[timestamp_ind]) for line in lines]

    coordinates = 0

    return ModalityData(coordinates, sampling_rate, timevector)


def retrieve_splines(
        splinefile: Path,
        spline_config: SplineImportConfig) -> dict[str, Splines]:
    """
    Read all splines from the file.
    """
    prompt_pos = spline_config.meta_columns.index(
        SplineMetaData.PROMPT)
    rec_time_pos = spline_config.meta_columns.index(
        SplineMetaData.DATE_AND_TIME)

    # each entry of the dict is, by default, an empty list
    rows_by_recording = defaultdict(list)
    with closing(open(splinefile, 'r', encoding="utf8")) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"',)

        # We aren't using the header for anything.
        if spline_config.headers:
            next(csvreader)

        for row in csvreader:
            key = f"{row[prompt_pos]} {row[rec_time_pos]}"
            rows_by_recording[key].append(row)

        table = {key: parse_splines(rows_by_recording[key], spline_config)
                 for key in rows_by_recording}

    # TODO: Create Splines objects either here or in parse_splines or
    # add_splines....

    _AAA_spline_logger.info("Read file %s.", str(splinefile))
    return table


def add_splines_from_batch_export(
        recording_list: list[Recording],
        spline_file: Union[str, Path],
        spline_config_file: Union[str, Path]) -> None:
    """
    Add a Spline Modality to each recording.

    The splines are read from a single AAA export file and added to
    the correct Recording by identifying the Recordings based on the date
    and time of the original recording. If no splines are found for a
    given Recording, an empty Spline object will be attached to it.

    Arguments:
    recording_list -- a list of Recording objects
    spline_file -- an AAA export file containing splines

    Return -- None. Recordings are modified in place.
    """
    if isinstance(spline_file, str):
        spline_file = Path(spline_file)
    if isinstance(spline_config_file, str):
        spline_file = Path(spline_config_file)

    if spline_file.is_file() and spline_config_file.is_file():
        spline_config = load_spline_import_config(spline_config_file)
        spline_dict = retrieve_splines(spline_file, spline_config)
        for recording in recording_list:
            search_key = recording.identifier()
            splines = spline_dict[search_key]
            recording.add_modality(splines)

            _AAA_spline_logger.debug(
                "%s has %d splines.",
                recording.basename, len(splines.data.timevector))
