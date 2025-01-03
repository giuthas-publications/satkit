#
# Copyright (c) 2019-2025
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
"""
Routines for loading splines exported from AAA.
"""

from collections import defaultdict
from contextlib import closing
import csv
import logging
from pathlib import Path

import dateutil.parser
import numpy as np
from icecream import ic

from satkit.constants import (
    CoordinateSystems, SatkitConfigFile,
    SplineDataColumn, SplineMetaColumn)
from satkit.data_structures import ModalityData, Recording
from satkit.errors import SatkitError
from satkit.modalities.splines import Splines, SplineMetadata

from .spline_import_config import (
    SplineImportConfig, load_spline_config)

_AAA_spline_logger = logging.getLogger('satkit.AAA_splines')


def parse_splines(
        lines: list,
        spline_config: SplineImportConfig) -> tuple[ModalityData, int, bool]:
    """
    Construct a ModalityData from a list of lines representing Splines.

    Note that currently splines with varying number of sample points are not
    supported and that confidence values generated by AAA are not imported.

    Parameters
    ----------
    lines : list
        Lines from a csv file.
    spline_config : SplineImportConfig
        satkit spline configuration which explains how to parse the lines.

    Returns
    -------
    ModalityData
        ModalityData which contains the splines. Sampling rate will be set to
        zero, because splines may not exist for all frames rendering any value
        calculated from spline timestamps unreliable.

        Note that the sampling rate of the returned modality data will only be
        set to non-zero, if `np.amax(time_diffs) < 1.1*np.amin(time_diffs`
        where `time_diffs = np.diffs(timevector_of_splines)`. This is so that,
        if the splines are sparse in time, we won't set a weird sampling rate.
        However, this may cause problems when trying to calculate time-wise
        comparisons of splines and determine that metric's sampling rate.
    """
    coordinates = []

    timestamp_ind = spline_config.meta_columns.index(
        SplineMetaColumn.TIME_IN_RECORDING)
    timevector = np.asarray([float(line[timestamp_ind]) for line in lines])

    if spline_config.interleaved_coords:
        raise NotImplementedError
    else:
        spline_point_index = spline_config.meta_columns.index(
            SplineMetaColumn.NUMBER_OF_SPLINE_POINTS)
        spline_points = int(lines[0][spline_point_index])
        data_start_index = len(spline_config.meta_columns)

        if SplineDataColumn.CONFIDENCE in spline_config.data_columns:
            confidence_exists = True
            conf_index = spline_config.data_columns.index(
                SplineDataColumn.CONFIDENCE)
            conf_index = data_start_index + conf_index * spline_points
            confidence = [line[conf_index:conf_index + spline_points]
                          for line in lines]
            confidence = np.asfarray(confidence)
            confidence = np.divide(confidence, 100.0)
        else:
            confidence_exists = False

        if spline_config.coordinates is CoordinateSystems.POLAR:
            r_index = spline_config.data_columns.index(
                SplineDataColumn.R)
            r_index = data_start_index + r_index * spline_points
            phi_index = spline_config.data_columns.index(SplineDataColumn.PHI)
            phi_index = data_start_index + phi_index * spline_points

            r = [line[r_index:r_index + spline_points] for line in lines]
            phi = [line[phi_index:phi_index + spline_points] for line in lines]
            if confidence_exists:
                coordinates = np.asfarray([r, phi, confidence])
            else:
                coordinates = np.asfarray([r, phi])
        else:
            x_index = spline_config.data_columns.index(
                SplineDataColumn.X)
            x_index = data_start_index + x_index * spline_points
            y_index = spline_config.data_columns.index(SplineDataColumn.Y)
            y_index = data_start_index + y_index * spline_points

            x = [line[x_index:x_index + spline_points] for line in lines]
            y = [line[y_index:y_index + spline_points] for line in lines]
            if confidence_exists:
                coordinates = np.asfarray([x, y, confidence])
            else:
                coordinates = np.asfarray([x, y])

    if len(timevector) > 2:
        time_diffs = np.diff(timevector)
        if np.amax(time_diffs) < 1.1*np.amin(time_diffs):
            step = np.mean(time_diffs)
            sampling_rate = 1.0/step
        else:
            sampling_rate = 0

    # Make time the first dimension.
    coordinates = np.swapaxes(coordinates, 0, 1)

    return (ModalityData(coordinates, sampling_rate, timevector),
            spline_points,
            confidence_exists)


def retrieve_splines(
        splinefile: Path,
        spline_config: SplineImportConfig) -> dict[str, ModalityData]:
    """
    Read all splines from the file.
    """
    prompt_pos = spline_config.meta_columns.index(
        SplineMetaColumn.PROMPT)
    rec_time_pos = spline_config.meta_columns.index(
        SplineMetaColumn.DATE_AND_TIME)

    # each entry of the dict is, by default, an empty list
    rows_by_recording = defaultdict(list)
    with closing(open(splinefile, 'r', encoding='utf-8')) as csvfile:
        csvreader = csv.reader(
            csvfile, delimiter=spline_config.delimiter, quotechar='"',)

        # We aren't using the header for anything.
        if spline_config.headers:
            next(csvreader)

        for row in csvreader:
            key = (
                f"{row[prompt_pos]} "
                f"{dateutil.parser.parse(row[rec_time_pos])}")
            rows_by_recording[key].append(row)

        result = {key: parse_splines(rows_by_recording[key], spline_config)
                  for key in rows_by_recording}

    _AAA_spline_logger.info("Read file %s.", str(splinefile))
    return result


def add_splines_from_batch_export(
        recording_list: list[Recording],
        spline_config: SplineImportConfig) -> None:
    """
    Add a Splines Modality to each recording from a batch file.

    The splines are read from a single AAA export file and added to the correct
    Recording by identifying the Recordings based on the date and time of the
    original recording and the prompt (because several recordings may have been
    saved during the same minute). 

    If no splines are found for a given Recording, an empty Spline object will
    be attached to it.

    Note that Recordings are modified in place.

    Parameters
    ----------
    recording_list : list[Recording]
        a list of Recording objects
    spline_config : SplineImportConfig
        a parsed spline import configuration file
    """
    spline_file = recording_list[0].path/spline_config.spline_file
    spline_dict = retrieve_splines(spline_file, spline_config)

    for recording in recording_list:
        search_key = recording.identifier()
        (spline_data, number_of_points, confidence) = spline_dict[search_key]
        metadata = SplineMetadata(coordinates=spline_config.coordinates,
                                  number_of_sample_points=number_of_points,
                                  confidence_exists=confidence)
        splines = Splines(recording,
                          metadata=metadata,
                          data_path=spline_file,
                          parsed_data=spline_data)
        recording.add_modality(splines)

        _AAA_spline_logger.debug(
            "%s has %d splines.",
            recording.basename, len(splines.timevector))


def add_splines_from_individual_files(
        recording_list: list[Recording],
        spline_config: SplineImportConfig) -> None:
    """
    Add a Splines Modality to each Recording a corresponding file.

    If no splines are found for a given Recording, an empty Spline object will
    be attached to it.

    Note that Recordings are modified in place.

    Parameters
    ----------
    recording_list : list[Recording]
        a list of Recording objects
    spline_config : SplineImportConfig
        a parsed spline import configuration file
    """
    spline_extension = spline_config.spline_file_extension

    for recording in recording_list:
        spline_file = recording.path/(recording.basename + spline_extension)
        spline_dict = retrieve_splines(spline_file, spline_config)
        keys = list(spline_dict.keys())
        if len(keys) > 1:
            raise SatkitError(
                f"Spline file {spline_file} was supposed to "
                f"contain splines of a single recording, "
                f"but multiple found: {keys}.")
        (spline_data, number_of_points, confidence) = spline_dict[keys[0]]
        metadata = SplineMetadata(coordinates=spline_config.coordinates,
                                  number_of_sample_points=number_of_points,
                                  confidence_exists=confidence)

        splines = Splines(recording,
                          metadata=metadata,
                          data_path=spline_file,
                          parsed_data=spline_data)
        recording.add_modality(splines)

        _AAA_spline_logger.debug(
            "%s has %d splines.",
            recording.basename, len(splines.timevector))


def add_splines(
        recording_list: list[Recording],
        directory: Path) -> None:
    """
    Load and add Splines to the Recordings if available.

    Note that a SatkitConfigFile.CSV_SPLINE_IMPORT file needs to be present in
    the directory. Otherwise nothing gets loaded because SATKIT doesn't know
    how to handle arbitrary spline files.

    Parameters
    ----------
    recording_list : list[Recording]
        The Recordings.
    directory : Path
        Path to the directory where the splines (and most likely other
        Recording files) are.
    """
    spline_config_path = directory/SatkitConfigFile.SPLINE
    if spline_config_path.is_file():
        spline_config = load_spline_config(spline_config_path)
        if spline_config.import_config.single_spline_file:
            add_splines_from_batch_export(
                recording_list, spline_config.import_config)
        else:
            add_splines_from_individual_files(
                recording_list, spline_config.import_config)
    else:
        _AAA_spline_logger.info(
            "Did not find spline import config file at %s.",
            str(spline_config_path))
        _AAA_spline_logger.info(
            "No splines laoded from %s.",
            str(directory))
