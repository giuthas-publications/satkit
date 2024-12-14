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
"""Main configuration for SATKIT."""

import logging
from pathlib import Path

from .configuration_parsers import (
    load_main_config, load_gui_params, load_publish_params,
    load_run_params  # , load_plot_params
)
from .configuration_models import (
    GuiConfig, MainConfig, DataRunConfig, PublishConfig
)

_logger = logging.getLogger('satkit.configuration_setup')


class Configuration:
    """
    Main configuration class of SATKIT.    
    """

    # TODO: implement save functionality.

    def __init__(
            self,
            configuration_file: Path | str | None = None
    ) -> None:
        """
        Init the main configuration object. 

        Run only once. Updates should be done with methods of the class.

        Parameters
        -------
        configuration_file : Union[Path, str, None]
            Path to the main configuration file.
        """
        # TODO: deal with the option that configuration_file is None

        self._main_config_yaml = load_main_config(configuration_file)
        self._main_config = MainConfig(**self._main_config_yaml.data)

        self._gui_yaml = load_gui_params(self._main_config.gui_parameter_file)
        self._gui_config = GuiConfig(**self._gui_yaml.data)

        if self._main_config.data_run_parameter_file is not None:
            self._data_run_yaml = load_run_params(
                self._main_config.data_run_parameter_file)
            self._data_run_config = DataRunConfig(**self._data_run_yaml.data)
        else:
            self._data_run_config = None

        if self._main_config.publish_parameter_file is not None:
            self._publish_yaml = load_publish_params(
                self._main_config.publish_parameter_file)
            self._publish_config = PublishConfig(**self._publish_yaml.data)
        else:
            self._publish_config = None

        # self._plot_yaml = load_plot_params(config['plotting_parameter_file'])
        # self._plot_config = PlotConfig(**self._plot_yaml.data)

    def __repr__(self) -> str:
        return (
            f"Configuration(\nmain_config={self._main_config.model_dump()})"
            f"\ndata_run={self._data_run_config.model_dump()}"
            f"\ngui={self._gui_config.model_dump()}"
            f"\npublish={self._publish_config.model_dump()})"
        )

    @property
    def main_config(self) -> MainConfig:
        """Main config options."""
        return self._main_config

    @property
    def data_run_config(self) -> DataRunConfig | None:
        """Config options for a data run."""
        return self._data_run_config

    @data_run_config.setter
    def data_run_config(self, new_config: DataRunConfig) -> None:
        if isinstance(new_config, DataRunConfig):
            self._data_run_config = new_config
        else:
            raise ValueError(f"Expected a DataRunConfig instance. "
                             f"Found {new_config.__class__} instead.")

    @property
    def gui_config(self) -> GuiConfig:
        """Gui config options."""
        return self._gui_config

    @property
    def publish_config(self) -> PublishConfig | None:
        """Result publishing configuration options."""
        return self._publish_config

    @publish_config.setter
    def publish_config(self, new_config: PublishConfig) -> None:
        if isinstance(new_config, PublishConfig):
            self._data_run_config = new_config
        else:
            raise ValueError(f"Expected a PublishConfig instance. "
                             f"Found {new_config.__class__} instead.")

    def save_to_file(
            self, filename: Path | str
    ) -> None:
        """
        Save configuration to a file.

        Parameters
        ----------
        filename : Path | str
            File to save to.

        Raises
        ------
        NotImplementedError
            This hasn't been implemented yet.
        """
        # filename = path_from_name(filename)
        # with open(filename, 'w') as file:
        # TODO: the problem here is that we can't write Configuration to a
        #   single file.
        #     file.write(self)

        raise NotImplementedError(
            "Saving configuration to a file has not yet been implemented.")

    def update_data_run_from_file(self, configuration_file: Path | str) -> None:
        """
        Update the data run configuration from a file.

        Parameters
        ----------
        configuration_file : Path | str
            File to read the new options from.
        """
        self._data_run_yaml = load_run_params(filepath=configuration_file)
        if self._data_run_config is None:
            self._data_run_config = DataRunConfig(**self._data_run_yaml.data)
        else:
            self._data_run_config.update(self._data_run_yaml.data)

    def update_publish_from_file(self, configuration_file: Path | str) -> None:
        """
        Update the publishing configuration from a file.

        Parameters
        ----------
        configuration_file : Path | str
            File to read the new options from.
        """
        self._publish_yaml = load_publish_params(filepath=configuration_file)
        if self._publish_config is None:
            self._publish_config = DataRunConfig(**self._publish_yaml.data)
        else:
            self._publish_config.update(self._publish_yaml.data)

    def update_gui_from_file(self, configuration_file: Path | str) -> None:
        """
        Update the GUI configuration from a file.

        Parameters
        ----------
        configuration_file : Path | str
            File to read the new options from.
        """
        self._gui_yaml = load_publish_params(filepath=configuration_file)
        if self._gui_config is None:
            self._gui_config = DataRunConfig(**self._gui_yaml.data)
        else:
            self._gui_config.update(self._gui_yaml.data)

    def update_main_from_file(self, configuration_file: Path | str) -> None:
        """
        Update the main configuration from a file.

        This does not update the other configuration members. To do that either
        call the individual update methods or run
        `Configuration.update_all_from_file`.

        Parameters
        ----------
        configuration_file : Path | str
            File to read the new options from.
        """
        self._main_config_yaml = load_publish_params(
            filepath=configuration_file)
        if self._main_config is None:
            self._main_config = DataRunConfig(**self._main_config_yaml.data)
        else:
            self._main_config.update(self._main_config_yaml.data)

    def update_all_from_file(
            self, configuration_file: Path | str
    ) -> None:
        """
        Update the configuration from a file.

        This first updates the main configuration and then recursively updates
        the other configuration members.
        
        NOTE: comment round tripping maybe/will be broken by running any of the
        update methods.

        Parameters
        ----------
        configuration_file : Path | str
            File to read the new options from.
        """
        self.update_main_from_file(configuration_file)
        self.update_gui_from_file(self._main_config.gui_parameter_file)
        if self.main_config.data_run_parameter_file is not None:
            self.update_data_run_from_file(
                self.main_config.data_run_parameter_file
            )
        if self.main_config.publish_parameter_file is not None:
            self.update_publish_from_file(
                self._main_config.publish_parameter_file
            )
