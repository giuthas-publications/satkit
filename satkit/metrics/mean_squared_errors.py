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

import logging
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np

from satkit.data_structures import (
    Modality, ModalityData, Recording, SessionMetric, SessionMetricMetaData)
from satkit.helpers import product_dict

_logger = logging.getLogger('satkit.mse')


class MseParameters(SessionMetricMetaData):
    """
    Parameters used in generating the parent MSE metric.

    Parameters
    ----------
    parent_name: str
        Name of the Modality this instance of MSE was calculated on.
    metric : str
        A string specifying this Modality's metric. Defaults to the l2 norm.
    release_data_memory : bool
        Wether to assign None to parent.data after deriving this Modality from
        the data. Currently has no effect as deriving MSE at runtime is not yet
        supported.
    interpolated : bool
        Should this MSE be calculated on interpolated images. Defaults to False
        for calculating MSE on raw data. This one really can only be used on 2D
        ultrasound data. For other data raw data is the regular data.
    """
    parent_name: str
    metric: str = 'l2'
    interpolated: bool = False
    release_data_memory: bool = True


class MSE(SessionMetric):
    """
    Represent Mean Squared Error (MSE) as a SessionMetric. 
    """

    accepted_metrics = [
        'l2',
    ]

    @classmethod
    def generate_name(cls, params: MseParameters) -> str:
        """
        Generate a MSE modality name to be used as its unique identifier.

        This static method **defines** what the names are. This implementation
        pattern (MSE.name calls this and any where that needs to guess what a
        name would be calls this) is how all derived Modalities should work.

        Parameters
        ----------
        params : MSEParameters
            The parameters of the MSE instance. Note that this MSEParameters
            instance does not need to be attached to a MSE instance.

        Returns
        -------
        str
            Name of the MSE instance.
        """
        # name_string = 'MSE' + " " + params.metric
        name_string = cls.__name__ + " " + params.metric

        if params.timestep != 1:
            name_string = name_string + " ts" + str(params.timestep)

        if params.image_mask:
            name_string = name_string + " " + params.image_mask.value

        if params.interpolated and params.parent_name:
            name_string = ("Interpolated " + name_string + " on " +
                           params.parent_name)
        elif params.parent_name:
            name_string = name_string + " on " + params.parent_name

        if params.is_downsampled:
            name_string += " downsampled by " + str(params.downsampling_ratio)

        return name_string

    @staticmethod
    def get_names_and_meta(
        modality: Union[Modality, str],
        norms: list[str] = None,
        mse_on_interpolated_data: bool = False,
        release_data_memory: bool = True
    ) -> dict[str: MseParameters]:
        """
        Generate MSE modality names and metadata.

        This method will generate the full cartesian product of the possible
        combinations. If only some of them are needed, make more than one call
        or weed the results afterwards.

        Parameters
        ----------
        modality : Modality
            parent modality that MSE would be derived from
        norms : List[str], optional
            list of norms to be calculated, defaults to 'l2'.
        timesteps : List[int], optional
            list of timesteps to be used, defaults to 1.
        mse_on_interpolated_data : bool, optional
            indicates if interpolated data should be used for instead of
            RawUltrasound, by default False
        mask_images : bool, optional
            indicates if images should be masked, by default False
        release_data_memory: bool
            Should parent Modlity's data be assigned to None after calculations
            are complete, by default True.

        Returns
        -------
        dict[str: MSEParameters]
            Dictionary where the names of the MSE Modalities index the 
            MSEParameter objects.
        """
        if isinstance(modality, str):
            parent_name = modality
        else:
            parent_name = modality.__name__

        if not norms:
            norms = ['l2']

        param_dict = {
            'parent_name': [parent_name],
            'metric': norms,
            'interpolated': [mse_on_interpolated_data],
            'release_data_memory': [release_data_memory]}

        mseparams = [MseParameters(**item)
                     for item in product_dict(**param_dict)]

        return {MSE.generate_name(params): params for params in mseparams}

    def __init__(self,
                 recording: Recording,
                 metadata: MseParameters,
                 load_path: Optional[Path] = None,
                 meta_path: Optional[Path] = None,
                 parsed_data: Optional[ModalityData] = None,
                 time_offset: Optional[float] = None) -> None:
        """
        Build a Pixel Difference (MSE) Modality       

        Positional arguments:
        recording -- the containing Recording.   
        parameters : MSEParameters
            Parameters used in calculating this instance of MSE.
        Keyword arguments:
        load_path -- path of the saved data - both ultrasound and metadata
        parent -- the Modality this one was derived from. None means this 
            is an underived data Modality.
            If parent is None, it will be copied from dataModality.
        parsed_data -- ModalityData object containing raw ultrasound, 
            sampling rate, and either timevector and/or time_offset. Providing 
            a timevector overrides any time_offset value given, but in absence
            of a timevector the time_offset will be applied on reading the data 
            from file. 
        timeoffset -- timeoffset in seconds against the Recordings baseline.
            If not specified or 0, timeOffset will be copied from dataModality.
        """
        # This allows the caller to be lazy.
        if not time_offset:
            if parsed_data:
                time_offset = parsed_data.timevector[0]

        super().__init__(
            recording,
            metadata=metadata,
            data_path=None,
            load_path=load_path,
            meta_path=meta_path,
            parsed_data=parsed_data)

        self.meta_data = metadata

    def _derive_data(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Calculate Pixel Difference (MSE) on the data Modality parent.       
        """
        raise NotImplementedError(
            "Currently MSE Modalities have to be "
            "calculated at instantiation time.")

    def get_meta(self) -> dict:
        # This conversion is done to keep nestedtext working.
        meta = self.meta_data.model_dump()
        return meta

    @property
    def name(self) -> str:
        """
        Identity, metric, and parent data class.

        The name will be of the form
        'MSE [metric name] on [data modality class name]'.

        This overrides the default behaviour of Modality.name.
        """
        return MSE.generate_name(self.meta_data)
