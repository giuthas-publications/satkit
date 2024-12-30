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
Import or load a Session from a directory.
"""

import logging
import sys
from pathlib import Path

from satkit.configuration import PathStructure
from satkit.constants import (
    DatasourceNames, SourceSuffix, SatkitSuffix, SatkitConfigFile)
from satkit.data_import import (
    generate_aaa_recording_list, load_session_config)
from satkit.data_structures import (
    FileInformation, Session, SessionConfig)
from satkit.save_and_load import load_recording_session

_logger = logging.getLogger('satkit.load_or_import')


def load_or_import_data(path: Path) -> Session:
    """
    Import data from individual files or load a previously saved session.

    Parameters
    ----------
    path : Path
        Directory or SATKIT metafile to read the Session from.

    Returns
    -------
    Session
        The generated Session object with the exclusion list applied.
    """
    if not path.exists():
        _logger.critical(
            'File or directory does not exist: %s.', path)
        _logger.critical('Exiting.')
        sys.exit()

    session = None
    match path.suffix:
        case SourceSuffix.AAA_ULTRA:
            session = load_recording_session(path)
        case SatkitSuffix.CONFIG if path.name == SatkitConfigFile.SATKIT:
            session = load_recording_session(path)
        case SatkitSuffix.CONFIG if path.name == SatkitConfigFile.MANIFEST:
            session = load_recording_session(path)
        case SatkitSuffix.META:
            session = load_recording_session(path)
        case "" if path.is_dir():
            #TODO This needs to somewow split into recorded path and satkit path
            session = read_recording_session_from_dir(path)
        case _:
            # TODO 1.0: consider giving guesses with the error if there are near
            # misses in file names and such
            _logger.error(
                'Unsupported filetype: %s.', path)
            sys.exit()

    for recording in session:
        recording.after_modalities_init()

    return session


def read_recording_session_from_dir(
        recorded_data_path: Path,
        detect_beep: bool = False
) -> Session:
    """
    Wrapper for reading data from a directory full of files.

    Having this as a separate method allows subclasses to change
    arguments or even the parser.

    Note that to make data loading work in a consistent way,
    this method just returns the data and saving it in an
    instance variable is left for the caller to handle.
    """
    containing_dir = recorded_data_path.parts[-1]

    session_config_path = recorded_data_path / SatkitConfigFile.SATKIT
    session_meta_path = recorded_data_path / (containing_dir + '.Session' +
                                              SatkitSuffix.META)
    if session_meta_path.is_file():
        return load_recording_session(recorded_data_path, session_config_path)

    file_info = FileInformation(
        recorded_path=recorded_data_path,
        recorded_meta_file=session_config_path.name)
    if session_config_path.is_file():
        paths, session_config = load_session_config(
            recorded_data_path, session_config_path)

        match session_config.data_source_name:
            case DatasourceNames.AAA:
                recordings = generate_aaa_recording_list(
                    directory=recorded_data_path,
                    import_config=session_config)

                session = Session(
                    name=containing_dir, paths=paths, config=session_config,
                    file_info=file_info, recordings=recordings)
                return session
            case DatasourceNames.RASL:
                raise NotImplementedError(
                    "Loading RASL data hasn't been implemented yet.")
            case _:
                raise NotImplementedError(
                    f"Unrecognised data source: "
                    f"{session_config.data_source_name}")

    if list(recorded_data_path.glob('*' + SourceSuffix.AAA_ULTRA)):
        recordings = generate_aaa_recording_list(
            directory=recorded_data_path,
            detect_beep=detect_beep
        )

        paths = PathStructure(root=recorded_data_path)
        session_config = SessionConfig(data_source=DatasourceNames.AAA)

        session = Session(
            name=containing_dir, paths=paths, config=session_config,
            file_info=file_info, recordings=recordings)
        return session

    _logger.error(
        'Could not find a suitable importer: %s.', recorded_data_path)
