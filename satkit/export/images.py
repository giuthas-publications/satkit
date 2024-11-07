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
Export various images.

Raw and interpolated ultrasound frames, AggregateImages. and DistanceMatrices.
"""
import logging
from pathlib import Path

import nestedtext
import numpy as np
from matplotlib.figure import Figure
from PIL import Image

from local.depracated_code.recording import RawUltrasound
from satkit.data_structures import Recording, Session
from satkit.data_structures.base_classes import DataAggregator, DataContainer
from satkit.interpolate_raw_uti import to_fan_2d
from satkit.metrics import (
    AggregateImage, AggregateImageParameters,
    DistanceMatrix, DistanceMatrixParameters
)
from satkit.save_and_load import nested_text_converters

_logger = logging.getLogger('satkit.export')


def _export_data_as_image(
        data: DataContainer | np.ndarray,
        path: Path,
        image_format: str = ".png",
        interpolation_params: dict | None = None,
) -> Path:
    if path.is_dir() and not isinstance(data, DataContainer):
        raise ValueError("Data must be DataContainer if path is a directory.")
    elif path.is_dir():
        filename = data.name.replace(" ", "_")
        filepath = path / filename
    else:
        filepath = path

    if isinstance(data, DataContainer):
        raw_data = data.data
    else:
        raw_data = data

    if interpolation_params is not None:
        raw_data = to_fan_2d(raw_data, **interpolation_params)

    im = Image.fromarray(raw_data)
    im = im.convert('L')
    im.save(filepath.with_suffix(image_format))
    _logger.info("Wrote file %s.", filepath)
    return filepath


def _publish_image(
        container: DataAggregator,
        statistic_name: str,
        image_format: str = ".png"
) -> Path | None:
    if statistic_name in container.statistics:
        statistic = container.statistics[statistic_name]
        raw_data = statistic.data
        im = Image.fromarray(raw_data)
        im = im.convert('L')
        name = container.name
        path = container.recorded_path
        image_file = path / (name + image_format)
        im.save(image_file)
        _logger.info("Wrote file %s.", image_file)
        return image_file


def publish_aggregate_images(
        session: Session, image_name: str, image_format: str = ".png"
) -> None:
    """
    Publish AggregateImages as image files.

    Parameters
    ----------
    session : Session
        Session containing the Recordings whose AggregateImages are being saved.
    image_name : str
        Name of the AggregateImage to publish.
    image_format : str
        File format to use, by default ".png".
    """
    for recording in session:
        _publish_image(recording, image_name, image_format)


def publish_distance_matrix(
        session: Session, distance_matrix_name: str, image_format: str = ".png"
) -> None:
    """
    Publish DistanceMatrix as an image file.

    Parameters
    ----------
    session : Session
        Session containing the DistanceMatrix which is being saved.
    distance_matrix_name : str
        Name of the DistanceMatrix to publish.
    image_format : str
        File format to use, by default ".png".
    """
    _publish_image(session, distance_matrix_name, image_format)


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
    if not isinstance(filename, Path):
        filename = Path(filename)
    meta_filename = filename.with_suffix('.txt')
    with meta_filename.open('w', encoding='utf-8') as file:
        file.write(
            f"Metadata for AggregateImage extracted by SATKIT to {filename}.\n")
        file.write(f"Session path: {session.recorded_path}\n")
        file.write(f"Participant ID: {recording.meta_data.participant_id}\n")
        file.write(f"Recording filename: {recording.name}\n")
        file.write(f"Recorded at: {recording.meta_data.time_of_recording}\n")
        file.write(f"Prompt: {recording.meta_data.prompt}\n")

        nestedtext.dump(aggregate_meta.model_dump(), file,
                        converters=nested_text_converters)
        if interpolation_params is not None:
            nestedtext.dump(interpolation_params, file,
                            converters=nested_text_converters)
        else:
            file.write("Interpolated: False")
        _logger.debug("Wrote file %s.", meta_filename)


def export_aggregate_image_and_meta(
        image: AggregateImage,
        session: Session,
        recording: Recording,
        path: Path,
        image_format: str = ".png",
        interpolation_params: dict | None = None
) -> None:
    """
    Export AggregateImage to an image file and meta to a text file.

    Parameters
    ----------
    image : AggregateImage
        The AggregateImage to be exported.
    session : Session
        Session the AggregateImage belongs to.
    recording : Recording
        Recording that the AggregateImage belongs to.
    path : Path
        Path to save the image and meta file.
    image_format : str, optional
        File format to save the image in, by default ".png"
    interpolation_params : dict | None
        Dictionary of interpolation parameters to be passed to `to_fan_2d`, by
        default None. If none, export raw image instead.
    """
    filepath = _export_data_as_image(
        image, path, image_format, interpolation_params)

    export_aggregate_image_meta(
        filename=filepath.with_suffix(".txt"),
        session=session,
        recording=recording,
        aggregate_meta=image.meta_data,
        interpolation_params=interpolation_params
    )


def export_distance_matrix_meta(
        filename: str | Path,
        session: Session,
        distance_matrix_meta: DistanceMatrixParameters,
) -> None:
    if not isinstance(filename, Path):
        filename = Path(filename)
    meta_filename = filename.with_suffix('.txt')
    with meta_filename.open('w', encoding='utf-8') as file:
        file.write(
            f"Metadata for AggregateImage extracted by SATKIT to {filename}.\n")
        file.write(f"Session path: {session.recorded_path}\n")
        participant_id = session.recordings[0].meta_data.participant_id
        file.write(f"Participant ID: {participant_id}\n")

        nestedtext.dump(distance_matrix_meta.model_dump(), file,
                        converters=nested_text_converters)
        _logger.debug("Wrote file %s.", meta_filename)


def export_distance_matrix_and_meta(
        matrix: DistanceMatrix,
        session: Session,
        path: Path,
        image_format: str = ".png"
) -> None:
    path = _export_data_as_image(matrix, path, image_format)

    export_distance_matrix_meta(
        filename=path.with_suffix(".txt"),
        session=session,
        distance_matrix_meta=matrix.meta_data,
    )


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
    if not isinstance(filename, Path):
        filename = Path(filename)
    meta_filename = filename.with_suffix('.txt')
    with meta_filename.open('w', encoding='utf-8') as file:
        file.write(f"Metadata for frame extracted by SATKIT to {filename}.\n")
        file.write(f"Session path: {session.recorded_path}\n")
        file.write(f"Participant ID: {recording.meta_data.participant_id}\n")
        file.write(f"Recording filename: {recording.name}\n")
        file.write(f"Recorded at: {recording.meta_data.time_of_recording}\n")
        file.write(f"Prompt: {recording.meta_data.prompt}\n")
        file.write(f"Frame number: {selection_index}\n")
        file.write(f"Timestamp in recording: {selection_time}\n")
        _logger.debug("Wrote file %s.", meta_filename)


def export_ultrasound_frame_and_meta(
        filepath: str | Path,
        session: Session,
        recording: Recording,
        selection_index: int,
        selection_time: float,
        ultrasound: RawUltrasound,
        image_format: str = ".png",
        interpolation_params: dict | None = None
) -> None:
    """
    Write ultrasound frame metadata to a human-readable text file.

    The purpose of this function is to generate a file documenting an extracted
    ultrasound frame, so that it can be found again in its original context.

    Parameters
    ----------
    filepath : str | Path
        Filename or path for the ultrasound frame to export. Format is deduced
        from the file suffix.
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
    ultrasound : RawUltrasound
        The RawUltrasound from which a frame is to be exported.
    image_format : str, optional
        File format to save the image in, by default ".png"
    interpolation_params : dict | None
        Dictionary of interpolation parameters to be passed to `to_fan_2d`, by
        default None. If none, export raw image instead.
    """
    filepath = _export_data_as_image(
        ultrasound, filepath, image_format, interpolation_params)

    # figure.savefig(filepath, bbox_inches=bbox_inches, pad_inches=pad_inches)
    _logger.debug("Wrote file %s.", filepath)

    export_ultrasound_frame_meta(
        filename=filepath,
        session=session,
        recording=recording,
        selection_index=selection_index,
        selection_time=selection_time,
    )
