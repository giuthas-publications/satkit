#
# Copyright (c) 2019-2022 Pertti Palo, Scott Moisik, Matthew Faytak, and Motoki Saito.
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

from dataclasses import dataclass
from enum import Enum
import logging
import sys
from copy import deepcopy
from pathlib import Path
from typing import Optional

# Numpy
import numpy as np
from satkit.constants import Coordinates
# local modules
from satkit.data_structures import Modality, ModalityData, Recording
from satkit.import_formats import read_ult
from satkit.interpolate_raw_uti import to_fan, to_fan_2d

_modalities_logger = logging.getLogger('satkit.modalities')


@dataclass
class SplineMetadata:
    coordinates: Coordinates
    sample_points: int
    confidence_exists: bool

# TODO: check that the initialisation corresponds to the way these are handled currently


class Splines(Modality):
    """
    Splines from 2D ultrasound data.
    """

    def __init__(self,
                 recording: Recording,
                 data_path: Optional[Path] = None,
                 load_path: Optional[Path] = None,
                 parsed_data: Optional[ModalityData] = None,
                 time_offset: Optional[float] = None,
                 meta: Optional[dict] = None
                 ) -> None:
        # Explicitly copy meta data fields to ensure that we have what we expected to get.
        if meta != None:
            try:
                wanted_meta = {key: meta[key]
                               for key in Splines.requiredMetaKeys}
                self.meta = deepcopy(wanted_meta)
            except KeyError:
                # Missing metadata for one recording may be ok and this could be handled with just
                # a call to _recording_logger.critical and setting self.excluded = True
                notFound = set(Splines.requiredMetaKeys) - set(meta)
                _modalities_logger.critical(
                    "Part of metadata missing when processing %s.",
                    self.meta['filename'])
                _modalities_logger.critical(
                    "Could not find %s.", str(notFound))
                _modalities_logger.critical('Exiting.')
                sys.exit()

        # Initialise super only after ensuring meta is correct,
        # because latter may already end the run.
        super().__init__(
            recording=recording,
            data_path=data_path,
            load_path=load_path,
            parent=None,
            parsed_data=parsed_data,
            time_offset=time_offset)

        # TODO: these are related to GUI and should really be in a decorator class and not here.
        # State variables for fast retrieval of previously tagged ultrasound frames.
        self._stored_index = None
        self._stored_image = None
        self.video_has_been_stored = False

    def _read_data(self) -> ModalityData:
        return read_ult(self.data_path, self.meta, self._time_offset)

    @property
    def data(self) -> np.ndarray:
        return super().data

    @data.setter
    def data(self, data) -> None:
        super()._data_setter(data)

    @property
    def in_polar(self) -> np.ndarray:
        if self.meta_data.coordinates is Coordinates.POLAR:
            return self.data
        else:
            raise NotImplementedError(
                "Can't yet convert cartesian coordinates to polar in Splines.")

    @property
    def in_cartesian(self) -> np.ndarray:
        if self.meta_data.coordinates is Coordinates.CARTESIAN:
            return self.data
        else:
            raise NotImplementedError(
                "Can't yet convert polar coordinates to cartesian in Splines.")
