#
# Copyright (c) 2019-2024
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
Export various metadata.
"""
import logging
from io import TextIOWrapper
from pathlib import Path
from typing import TextIO

import nestedtext

from satkit.constants import SATKIT_VERSION
from satkit.data_structures import FileInformation, Recording, Session
from satkit.metrics import AggregateImageParameters, DistanceMatrixParameters
from satkit.save_and_load import nested_text_converters
from satkit.utility_functions import path_from_name

_logger = logging.getLogger('satkit.export')


def _paths_from_name(filename: str | Path) -> tuple[Path, Path]:
    path = path_from_name(filename)
    return path, path.with_suffix('.txt')


def _write_session_and_recording_meta(
        file: TextIOWrapper | TextIO, session: Session, recording: Recording):
    file.write(f"Session path: {session.recorded_path}\n")
    file.write(f"Participant ID: {recording.meta_data.participant_id}\n")
    file.write(f"Recording filename: {recording.name}\n")
    file.write(f"Recorded at: {recording.meta_data.time_of_recording}\n")
    file.write(f"Prompt: {recording.meta_data.prompt}\n")


def _export_header(
    file: TextIOWrapper | TextIO,
    object_name: str,
    filename: str,
    file_info: FileInformation | None = None,
) -> None:
    file.write(
        f"Metadata for {object_name} extracted by "
        f"SATKIT {SATKIT_VERSION} to\n")
    file.write(f"\t{filename}.\n\n")
    if file_info is not None:
        file.write(f"{file_info}\n\n")


def export_aggregate_image_meta(
        filename: str | Path,
        session: Session,
        recording: Recording,
        aggregate_meta: AggregateImageParameters,
        interpolation_params: dict | None = None
) -> None:
    """
    Write ultrasound frame metadata to a human-readable text file.

    The purpose of this function is to generate a file documenting an extracted
    ultrasound frame, so that it can be found again in its original context.

    Parameters
    ----------
    filename : str | Path
        Filename or path of the extracted ultrasound frame.
    session : Session
        Session that the frame belongs to.
    recording : Recording
        Recording that the frame belongs to.
    aggregate_meta : AggregateImageParameters
        The parameters of the AggregateImage to be dumped in a file along with
        the session and recording information.
    interpolation_params : dict | None
        Dictionary of interpolation parameters to be passed to `to_fan_2d`, by
        default None. If none, export raw image instead.
    """
    filepath, meta_filepath = _paths_from_name(filename)
    with meta_filepath.open('w', encoding='utf-8') as file:
        _export_header(
            file=file,
            object_name="AggregateImage",
            filename=filename)
        _write_session_and_recording_meta(
            file=file, session=session, recording=recording)

        nestedtext.dump(aggregate_meta.model_dump(), file,
                        converters=nested_text_converters)
        if interpolation_params is not None:
            nestedtext.dump(interpolation_params, file,
                            converters=nested_text_converters)
        else:
            file.write("Interpolated: False")
        _logger.debug("Wrote file %s.", str(meta_filepath))


def export_distance_matrix_meta(
        filename: str | Path,
        session: Session,
        distance_matrix_meta: DistanceMatrixParameters,
) -> None:
    filepath, meta_filepath = _paths_from_name(filename)
    with meta_filepath.open('w', encoding='utf-8') as file:
        _export_header(
            file=file,
            object_name="DistanceMatrix",
            filename=filename)
        file.write(f"Session path: {session.recorded_path}\n")
        participant_id = session.recordings[0].meta_data.participant_id
        file.write(f"Participant ID: {participant_id}\n\n")

        nestedtext.dump(
            dict(sorted(distance_matrix_meta.model_dump().items())),
            file,
            converters=nested_text_converters)
        _logger.debug("Wrote file %s.", str(meta_filepath))


def export_session_and_recording_meta(
        filename: Path | str,
        session: Session,
        recording: Recording,
        description: str
) -> None:
    filepath, meta_filepath = _paths_from_name(filename)
    with meta_filepath.open('w', encoding='utf-8') as file:
        _export_header(
            file=file,
            object_name=description,
            filename=filename)
        _write_session_and_recording_meta(
            file=file, session=session, recording=recording)

        _logger.debug("Wrote file %s.", str(meta_filepath))


def export_ultrasound_frame_meta(
        filename: str | Path,
        session: Session,
        recording: Recording,
        selection_index: int,
        selection_time: float,
) -> None:
    """
    Write ultrasound frame metadata to a human-readable text file.

    The purpose of this function is to generate a file documenting an extracted
    ultrasound frame, so that it can be found again in its original context.

    Parameters
    ----------
    filename : str | Path
        Filename or path of the extracted ultrasound frame.
    session : Session
        Session that the frame belongs to.
    recording : Recording
        Recording that the frame belongs to.
    selection_index : int
        Index of the frame within the ultrasound video.
    selection_time : float
        Time in seconds of the frame within the **recording**. This is relative
        to what ever -- most likely the beginning of audio -- is being used as
        t=0s.
    """
    filepath, meta_filepath = _paths_from_name(filename)
    with meta_filepath.open('w', encoding='utf-8') as file:
        _export_header(
            file=file,
            object_name="AggregateImage",
            filename=filename)
        _write_session_and_recording_meta(
            file=file, session=session, recording=recording)
        file.write(f"Frame number: {selection_index}\n")
        file.write(f"Timestamp in recording: {selection_time}\n")
        _logger.debug("Wrote file %s.", str(meta_filepath))
