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

import logging
import sys
from copy import deepcopy
from pathlib import Path
from typing import Optional

# Numpy
import numpy as np
# local modules
from satkit.data_structures import Modality, ModalityData, Recording
from satkit.formats import read_ult
from satkit.interpolate_raw_uti import to_fan, to_fan_2d

_modalities_logger = logging.getLogger('satkit.modalities')

class Splines(Modality):
    """
    Splines from 2D ultrasound data.
    """

    requiredMetaKeys = [
        'meta_file',
        'Angle',
        'FramesPerSec',
        'NumVectors',
        'PixPerVector',
        'PixelsPerMm',
        'ZeroOffset'
    ]

    def __init__(self, 
                recording: Recording, 
                data_path: Optional[Path]=None,
                load_path: Optional[Path]=None,
                parsed_data: Optional[ModalityData]=None,
                time_offset: Optional[float]=None,
                meta: Optional[dict]=None 
                ) -> None:
        """
        Create a RawUltrasound Modality.

        Positional arguments:
        recording -- the containing Recording.        

        Keyword arguments:
        data_path -- path of the ultrasound file
        load_path -- path of the saved data - both ultrasound and metadata
        parsed_data -- ModalityData object containing raw ultrasound, sampling rate,
            and either timevector and/or time_offset. Providing a timevector 
            overrides any time_offset value given, but in absence of a 
            timevector the time_offset will be applied on reading the data 
            from file. 
        meta -- a dict with (at least) the keys listed in 
            RawUltrasound.requiredMetaKeys. Extra keys will be ignored. 
            Default is None.
        """
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

    def interpolated_image(self, index):
        """
        Return an interpolated version of the ultrasound frame at index.
        
        A new interpolated image is calculated, if necessary. To avoid large memory overheads
        only the current frame's interpolated version maybe stored in memory.

        Arguments:
        index - the index of the ultrasound frame to be returned
        """
        if self.video_has_been_stored:
            half_way = int(self.stored_video.shape[0]/2)
            return self.stored_video[half_way, :, :].copy()
        elif self._stored_index and self._stored_index == index:
            return self._stored_image
        else:
            self._stored_index = index
            #frame = scipy_medfilt(self.data[index, :, :].copy(), [1,15])
            frame = self.data[index, :, :].copy()
            half = int(frame.shape[1]/2)
            frame[:,half:] = 0
            frame = np.transpose(frame)
            frame = np.flip(frame, 0)
            self._stored_image = to_fan_2d(
                frame,
                angle=self.meta['Angle'],
                zero_offset=self.meta['ZeroOffset'],
                pix_per_mm=self.meta['PixelsPerMm'],
                num_vectors=self.meta['NumVectors'])
            return self._stored_image

    def interpolated_frames(self) -> np.ndarray:
        """
        Return an interpolated version of the ultrasound frame at index.
        
        A new interpolated image is calculated, if necessary. To avoid large memory overheads
        only the current frame's interpolated version maybe stored in memory.

        Arguments:
        index - the index of the ultrasound frame to be returned
        """
        data = self.data.copy()
        data = np.transpose(data, (0,2,1))
        data = np.flip(data, 1)

        self.video_has_been_stored = True
        video = to_fan(
            data,
            angle=self.meta['Angle'],
            zero_offset=self.meta['ZeroOffset'],
            pix_per_mm=self.meta['PixelsPerMm'],
            num_vectors=self.meta['NumVectors'],
            show_progress=True)
        half = int(video.shape[1]/2)
        self.stored_video = video.copy()
        self.stored_video[:,:half,:] = 0
        return video