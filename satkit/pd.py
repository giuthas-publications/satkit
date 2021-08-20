#
# Copyright (c) 2019-2021 Pertti Palo, Scott Moisik, and Matthew Faytak.
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

# Built in packages
from contextlib import closing
import logging

# Numpy and scipy
import numpy as np
import scipy.io.wavfile as sio_wavfile

# local modules
import satkit.audio as satkit_audio
import satkit.io.AAA as satkit_AAA
from satkit.recording import DerivedModality


_pd_logger = logging.getLogger('satkit.pd')    

class PD(DerivedModality):
    """
    Calculate PD and represent it as a DerivedModality. 

    PD maybe calculated using several different norms and therefore the
    result may be non-singular. For this reason self.data is a dict
    containing a PD curve for each key.
    """

    acceptedNorms = [
        'l1',
        'l2',
        'l3',
        'l4',
        'l5',
        'l6',
        'l7',
        'l8',
        'l9',
        'l10',
        'inf',
    ]

    def __init__(self, name = "pixel difference", parent=None, 
                preload=True, timeOffset=0, dataModality=None,
                norms=['l2'], timesteps=[1]):
        """
        Build a Pixel Difference (PD) Modality       

        If timestep is given as a vector of positive integers, then calculate
        and return pd for each of those.
        """
        super().__init__(name, parent=parent, preload=preload, timeOffset=timeOffset, dataModality=dataModality)

        # This allows the caller to be lazy.
        if not parent and dataModality:
            self.parent = dataModality.parent

        if all(norm in PD.acceptedNorms for norm in norms):
            self._norms = norms
        else:
            ValueError("Unexpected norm requested in " + str(norms))

        if all((isinstance(timestep,int) and timestep > 0) 
                for timestep in timesteps):
            # Since all timesteps are valid, we are ok.
            self._timesteps = timesteps
        else:
            ValueError("Negative or non-integer timestep in " + str(timesteps))

        self._loggingBaseNotice = (self.parent.meta['base_name'] 
                                + " " + self.parent.meta['prompt'])

        if preload:
            self._calculate()

    def _calculate(self):
        """
        Build a Pixel Difference (PD) Modality       

        If timestep is given as a vector of positive integers, then calculate
        and return pd for each of those.
        """        
        _pd_logger.info(self._loggingBaseNotice 
                        + ': Token being processed.')
        
        data = self.dataModality.data
        result = {}
            
        raw_diff = np.diff(data, axis=0)
        abs_diff = np.abs(raw_diff)
        square_diff = np.square(raw_diff)
        slw_pd = np.sum(square_diff, axis=2) # this should be square rooted at some point

        
        result['sbpd'] = slw_pd
        result['pd'] = np.sqrt(np.sum(slw_pd, axis=1))
        result['l1'] = np.sum(abs_diff, axis=(1,2))
        result['l3'] = np.power(np.sum(np.power(abs_diff, 3), axis=(1,2)), 1.0/3.0)
        result['l4'] = np.power(np.sum(np.power(abs_diff, 4), axis=(1,2)), 1.0/4.0)
        result['l5'] = np.power(np.sum(np.power(abs_diff, 5), axis=(1,2)), 1.0/5.0)
        result['l10'] = np.power(np.sum(np.power(abs_diff, 10), axis=(1,2)), .1)
        result['l_inf'] = np.max(abs_diff, axis=(1,2))

        _pd_logger.debug(self._loggingBaseNotice 
                        + ': PD calculated.')

        result['pd_time'] = (self.dataModality.timevector 
                            + .5/self.dataModality.meta['FramesPerSec'])

        self.data = result

        

