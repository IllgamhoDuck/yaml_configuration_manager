

import os
import yaml
import glob
import shutil

from datetime import datetime
import pandas as pd

from .logger import InfoLogger

class ConfigurationManager:
    """Manage YAML configurations for anything

    Support the following functions

    1. Manage Modules
        - Create Module
        - Delete Module

    2. Manage YAML configuration by command line
        - Create YAML
            - Default setting
                - `DATETIME`
                - `VERSION`
        - Update YAML
        - Get YAML
        - Delete YAML
            - Experiment related to this deleted YAML will be automatically deleted

    3. Track the recent usage of YAML configuration for each project name
        - Tracks only the last used configuration for each stage called by `get()`

    4. Save YAML configuration record for experiment management
        - Save Experiment
        - Load Experiment
        - Delete Experiment

    5. Automatically create folder based on ML pipeline setting

    ######################## Usage #########################
    1. project name and path must be given

        ```python
        ConfigurationManager(project_name=PROJECT_NAME,
                             project_path=PROJECT_PATH)
        ```

    2. Manage Modules
        - create or delete modules

        ```python
        config.create_module('data')
        config.delete_module('data')
        ```

    3. Manage the configuration YAML file by command line
        - If experiment name is not given project name will be used alternatively

        ```python
        config.show('training')
        config.show_all()

        config.create('training', 1.0)
        config.update('training', 1.0, update_config)
        config.get('training', 1.0)
        config.delete('training', 1.0)

        config.create_yaml(yaml)
        config.update_yaml(yaml, update_config)
        config.get_yaml(yaml)
        config.delete_yaml(yaml)
        ```

    4. Manage experiment
        - All records will be saved at pandas DataFrame
        - Record of the experiment will be saved manually
        - Load & Delete is controlled by index of record dataframe

        ```python
        config.show_experiment()

        config.save_experiment('training', 1.0, note="warmstart")
        config.load_experiment(2)
        config.delete_experiment(5)
        ```

    5. History
        - Tracking the most recently used configuration files for each project

        ```python
        config.show_history()
        ```
    ########################################################

    Args:
        project_path (str): Root path for project
        project_name (str): Current project name
                            This name will be used for experiment name as default
    """
    def __init__(self, project_name, project_path):
        # project name
        self.project_name = project_name

        # Setting logger
        self.logger = InfoLogger("{0}".format(self.__class__.__qualname__))
        self.logger.info("Configuration manager initialized")

        # path setting
        ## project_path/
        self.project_path = project_path

        ## project_path/configuration/
        self.config_path = os.path.join(project_path, "configuration")

        # initialize configuration folder
        self._initialize_configuration_folder()

        # synchronize with modules already created
        self.synchronize_module()

        # load history for tracking recent YAML usage of project
        self.history_path = os.path.join(self.config_path, "history.yaml")
        self._load_history()
        self._synchronize_history()

        # load experiment record for experiment manage of project
        self.record_path = os.path.join(self.config_path, f"{self.project_name}_experiment_record.pkl")
        self._load_record()

    def __repr__(self):
        return f"ConfigurationManager(project_name=\'{self.project_name}, project_path=\'{PROJECT_PATH}\')"

    def __str__(self):
        # update the self.modules
        self.synchronize_module()

        return f"Total Modules : {len(self.modules)}, Total YAML files : {self.__len__()}"

    def __len__(self):
        """return total YAML file number"""
        # update the self.modules
        self.synchronize_module()

        total_yaml = 0

        for module in self.modules:
            yaml_path_list = list(glob.glob(os.path.join(self.config_path, module) + '/*'))
            total_yaml += len(yaml_path_list)

        return total_yaml



    def create_module(self, module):
        # set path name
        ## project_path/configuration/data
        module_config_path = os.path.join(self.config_path, module)

        # Check the folder exist and if not create
        # config folder
        if not os.path.isdir(module_config_path):
            self.logger.info(f"[ {module} ] Configuration folder created")
            os.mkdir(module_config_path)
        else:
            raise FileExistsError(f"[ {module} ] Configuration folder already exist ")

        self.synchronize_module()

    def delete_module(self, module):
        # project_path/configuration/data
        module_config_path = os.path.join(self.config_path, module)

        if not os.path.isdir(module_config_path):
            raise FileNotFoundError(f"No Configuration folder [ {module} ] to delete")
        else:
            # delete folder
            shutil.rmtree(module_config_path)
            self.logger.info(f"[ {module} ] Configuration folder deleted")

        # delete the module from record
        self._delete_module_from_all_records(module)

    def synchronize_module(self):
        config_list = os.listdir(self.config_path)

        modules = []
        for f in config_list:
            # only if the file is Directory
            if os.path.isdir(os.path.join(self.config_path, f)):
                modules.append(f)
        self.modules = modules



    def create_yaml(self, yaml_name, config_dict=None):
        module, version, experiment_name = self._get_config_info(yaml_name)

        return self.create(module=module,
                           version=version,
                           experiment_name=experiment_name,
                           config_dict=config_dict)

    def update_yaml(self, yaml_name, config_dict, override=False):
        module, version, experiment_name = self._get_config_info(yaml_name)

        return self.update(module=module,
                           version=version,
                           experiment_name=experiment_name,
                           config_dict=config_dict,
                           override=override)

    def get_yaml(self, yaml_name):
        module, version, experiment_name = self._get_config_info(yaml_name)

        return self.get(module=module,
                        version=version,
                        experiment_name=experiment_name)

    def delete_yaml(self, yaml_name):
        module, version, experiment_name = self._get_config_info(yaml_name)

        return self.delete(module=module,
                           version=version,
                           experiment_name=experiment_name)



    def create(self, module, version, experiment_name=None, config_dict=None):
        """Make a new YAML file"""
        # If the experiment name is not given use the project name
        if experiment_name is None:
            experiment_name = self.project_name

        # update the existance of modules and history
        self.synchronize_module()
        self._synchronize_history()
        if module not in self.modules:
            self.create_module(module)

        # If user gave an configuration dictionary check the type
        if config_dict and not isinstance(config_dict, dict):
            raise TypeError(f"Type [ {type(config_dict)} ] for 'config_dict' is not supported")

        yaml_name = self._get_yaml_name(module, experiment_name, version)

        # project_path/configuration/data/data_riiid_v1.0.yaml
        yaml_path = os.path.join(self.config_path, module, yaml_name)

        if os.path.isfile(yaml_path):
            raise FileExistsError(f"[ {yaml_name} ] file already exist ")
        else:
            # create new configuration
            new_config_dict = self._initialize_config_dict(version)
            self.write_yaml(new_config_dict, yaml_path)
            self.logger.info(f"[ {yaml_name} ] file created successfully ")

        # If user gave an configuration dictionary
        if config_dict:
            # update the information to the created configuration above
            self.update(module=module,
                        version=version,
                        experiment_name=experiment_name,
                        config_dict=config_dict)

    def update(self, module, version, config_dict, experiment_name=None, override=False):
        """Update YAML file

        Args:
            override (bool): If True than the original configuration dictionary
                             will be replaced to the given configuration dictionary

                             original - {'a': 1, 'c': 7}
                             new      - {'a': 2, 'b': 1}
                             ---------------------------
                             result   - {'a': 2, 'b': 1}

                             If False than the dictionary will be updated to the
                             given configuration dictionary but leave the legacy

                             original - {'a': 1, 'c': 7}
                             new      - {'a': 2, 'b': 1}
                             ---------------------------
                             result   - {'a': 2, 'b': 1, 'c': 7}
        """
        # If the experiment name is not given use the project name
        if experiment_name is None:
            experiment_name = self.project_name

        # update the existance of modules and history
        self.synchronize_module()
        self._synchronize_history()
        if module not in self.modules:
            raise FileNotFoundError(f"No Module [ {module} ] exist")

        # check given configuration dictionary type
        if not isinstance(config_dict, dict):
            raise TypeError(f"Type [ {type(config_dict)} ] for 'config_dict' is not supported")

        yaml_name = self._get_yaml_name(module, experiment_name, version)

        # project_path/configuration/data/data_riiid_v1.0.yaml
        yaml_path = os.path.join(self.config_path, module, yaml_name)

        # If yaml doesn't exist raise an error
        if not os.path.isfile(yaml_path):
            raise FileNotFoundError(f"No file [ {yaml_name} ] to update")
        else:
            if override:
                self.write_yaml(config_dict, yaml_path)
            else:
                # update new configuration
                original_config_dict = self.read_yaml(yaml_path)

                for k, v in config_dict.items():
                    # datetime and version will be managed automatically
                    if k in ['DATETIME', 'VERSION']:
                        continue
                    original_config_dict[k] = v

                # save the updated configuration
                self.write_yaml(original_config_dict, yaml_path)

        self.logger.info(f"[ {yaml_name} ] file updated successfully ")

    def get(self, module, version, experiment_name=None):
        # If the experiment name is not given use the project name
        if experiment_name is None:
            experiment_name = self.project_name

        # update the existance of modules and history
        self.synchronize_module()
        self._synchronize_history()
        if module not in self.modules:
            raise FileNotFoundError(f"No Module [ {module} ] exist")

        yaml_name = self._get_yaml_name(module, experiment_name, version)

        # project_path/configuration/data/data_riiid_v1.0.yaml
        yaml_path = os.path.join(self.config_path, module, yaml_name)

        # If yaml doesn't exist raise an error
        if not os.path.isfile(yaml_path):
            raise FileNotFoundError(f"No file [ {yaml_name} ] to get")

        # update the history
        self._update_history(yaml_path)
        self.logger.info(f"[ {yaml_name} ] file read successfully ")

        return self.read_yaml(yaml_path)

    def delete(self, module, version, experiment_name=None):
        # If the experiment name is not given use the project name
        if experiment_name is None:
            experiment_name = self.project_name

        # update the existance of modules and history
        self.synchronize_module()
        self._synchronize_history()
        if module not in self.modules:
            raise FileNotFoundError(f"No Module [ {module} ] exist")

        yaml_name = self._get_yaml_name(module, experiment_name, version)

        # project_path/configuration/data/data_riiid_v1.0.yaml
        yaml_path = os.path.join(self.config_path, module, yaml_name)

        # If yaml doesn't exist raise an error
        if not os.path.isfile(yaml_path):
            raise FileNotFoundError(f"No file [ {yaml_name} ] to delete")

        # delete the experiment record
        self._delete_experiment_from_all_records(yaml_path)

        # remove configuration
        os.remove(yaml_path)
        self.logger.info(f"[ {yaml_name} ] file removed successfully ")

    def show(self, module):
        """Show the list of configuration files of module"""
        self.synchronize_module()

        yaml_path_list = list(glob.glob(os.path.join(self.config_path, module) + '/*'))
        yaml_list = [path.split('/')[-1] for path in yaml_path_list]

        return yaml_list

    def show_all(self):
        """Show all configuration files of modules"""
        self.synchronize_module()

        all_yaml = {}
        for module in self.modules:
            yaml_path_list = list(glob.glob(os.path.join(self.config_path, module) + '/*'))
            yaml_list = [path.split('/')[-1] for path in yaml_path_list]

            all_yaml[module] = yaml_list

        return all_yaml



    def _load_record(self):
        # check the existance of record file
        if os.path.isfile(self.record_path):
            self.record_df = self.read_pickle(self.record_path)
            self.logger.info(f"[ record ] Loaded successfully")
        else:
            # if the record was never created
            self.logger.info("[ record ] Initializing file")
            self.record_df = pd.DataFrame(columns=['datetime', 'yaml', 'module', 'experiment_name', 'version', 'note'])
            self.write_pickle(self.record_df, self.record_path)

    def _delete_experiment_from_all_records(self, yaml_path):
        """When user delete the configuration file delete all the related experiment record"""
        # project_path/configuration/data/data_riiid_v1.0.yaml
        yaml_info = yaml_path.split('/')

        ## data_riiid_v1.0.yaml
        yaml_name = yaml_info[-1]

        # delete experiment record from all the projects experiment records
        for record_path in glob.glob(self.config_path + '/*_experiment_record.pkl'):
            # read the following experiment record file
            record_df = self.read_pickle(record_path)

            # Drop all the rows related to the yaml
            record_df = record_df.query("yaml != @yaml_name").reset_index(drop=True)

            # save to pickle
            self.write_pickle(record_df, record_path)

        # update the current record_df
        self.record_df = self.read_pickle(self.record_path)

    def _delete_module_from_all_records(self, module):
        """When user delete the configuration file delete all the related experiment record"""
        # delete module record from all the projects experiment records
        for record_path in glob.glob(self.config_path + '/*_experiment_record.pkl'):
            # read the following experiment record file
            record_df = self.read_pickle(record_path)

            # Drop all the rows related to the yaml
            record_df = record_df.query("module != @module").reset_index(drop=True)

            # save to pickle
            self.write_pickle(record_df, record_path)

        # update the current record_df
        self.record_df = self.read_pickle(self.record_path)

    def save_experiment(self, module, version, experiment_name=None, note=""):
        """Save the experiment to pandas DataFrame

        Args:
            module (str): module for the experiment
            version (float): version of experiment
            experiment_name (optional(str)): name of experiment
                                             if None than project name will be used
            note (optional(str)): note about the experiment
        """
        # If the experiment name is not given use the project name
        if experiment_name is None:
            experiment_name = self.project_name

        yaml_name = self._get_yaml_name(module, experiment_name, version)

        # project_path/configuration/data/data_riiid_v1.0.yaml
        yaml_path = os.path.join(self.config_path, module, yaml_name)

        # If yaml doesn't exist raise an error
        if not os.path.isfile(yaml_path):
            raise FileNotFoundError(f"No experiment [ {yaml_name} ] to save")

        # save experiment
        self.record_df = self.record_df.append({'datetime': datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                                                'yaml': yaml_name,
                                                'module': module,
                                                'experiment_name': experiment_name,
                                                'version': version,
                                                'note': note},
                                               ignore_index=True)


        # save to pickle
        self.write_pickle(self.record_df, self.record_path)
        self.logger.info(f"[ {yaml_name} ] successfully saved")

    def show_experiment(self):
        return self.record_df

    def load_experiment(self, index):
        """load experiment from record by index

        check the experiments at record_df
        """
        # 01_data
        module = self.record_df.iloc[index].module

        # data_riiid_v1.0.yaml
        yaml_name = self.record_df.iloc[index].yaml

        # project_path/configuration/data/data_riiid_v1.0.yaml
        yaml_path = os.path.join(self.config_path, module, yaml_name)

        # If yaml doesn't exist raise an error
        if not os.path.isfile(yaml_path):
            raise FileNotFoundError(f"No file [ {yaml_name} ] to load")

        # update the history
        self._update_history(yaml_path)

        self.logger.info(f"[ {yaml_name} ] successfully loaded")

        return self.read_yaml(yaml_path)

    def delete_experiment(self, index):
        """load experiment from record by index

        check the experiments at record_df
        """
        # data_riiid_v1.0.yaml
        yaml_name = self.record_df.iloc[index].yaml

        # delete the row refering the index
        self.record_df = self.record_df.drop(index).reset_index(drop=True)

        # save to pickle
        self.write_pickle(self.record_df, self.record_path)
        self.logger.info(f"[ {yaml_name} ] successfully deleted")



    def show_history(self):
        # update history
        self._synchronize_history()

        return self.read_yaml(self.history_path)

    def _load_history(self):
        # check the existance of history file
        if os.path.isfile(self.history_path):
            self.history = self.read_yaml(self.history_path)

            # If the project name wasn't used before add to history
            if not self.project_name in self.history:
                self.logger.info(f"[ history ] Add new project {self.project_name}")
                self.history[self.project_name] = {}
                self.write_yaml(self.history, self.history_path)
            else:
                self.logger.info(f"[ history ] Loaded successfully")
        else:
            # if the history was never created
            self.logger.info("[ history ] Initializing file")
            self.history = {self.project_name: {}}
            self.write_yaml(self.history, self.history_path)

    def _update_history(self, yaml_path):
        # project_path/configuration/data/data_riiid_v1.0.yaml
        yaml_info = yaml_path.split('/')

        ## data
        module = yaml_info[-2]

        ## data_riiid_v1.0.yaml
        yaml_name = yaml_info[-1]

        # update and write the history
        self.history[self.project_name][module] = yaml_name
        self.write_yaml(self.history, self.history_path)

    def _delete_history(self, module):
        del self.history[self.project_name][module]
        self.write_yaml(self.history, self.history_path)

    def _synchronize_history(self):
        """synchronize the history with current existing modules"""
        for history_module in list(self.history[self.project_name].keys()):
            # If the module listed at history doesn't exist delete
            if history_module not in self.modules:
                self._delete_history(history_module)

        self.write_yaml(self.history, self.history_path)



    def _initialize_configuration_folder(self):
        # configuration folder
        if not os.path.isdir(self.config_path):
            self.logger.info("[ Configuration ] folder created")
            os.mkdir(self.config_path)

    def _initialize_config_dict(self, version):
        """Basic template for configuration dictionary"""
        # Configuration dictionary
        config_dict = {}

        # datetime YYYY-MM-DD
        config_dict['DATETIME'] = datetime.today().strftime("%Y-%m-%d")

        # version
        config_dict['VERSION'] = version

        return config_dict

    def _get_yaml_name(self, module, experiment_name, version):
        """Return yaml file name using module, name, version information"""
        return f"{module}_{experiment_name}_v{version}.yaml"

    def _get_config_info(self, yaml_name):
        """Return module, name, version information using yaml name"""
        # data_riiid_v1.0.yaml
        # check valid extension
        if yaml_name[-5:] != '.yaml':
            raise ValueError(f'Extension should be [ .yaml ] but given [ {yaml_name[-5:]} ]')

        # data_riiid_v1.0
        yaml_header = yaml_name[:-5]

        # ['data', 'riiid', 'v1.0']
        yaml_list = yaml_header.split('_')

        # check valid format of yaml name
        if len(yaml_list) < 3:
            raise ValueError(f'Yaml format should be following [ (module)_(experiment name)_v(version).yaml ] but given [ {yaml_name} ]')

        # module - 'data'
        module = yaml_list[0]

        # version - 1.0
        version = yaml_list[-1]

        # check valid format of version
        if version[0] != 'v':
            raise ValueError(f'Version should be [v(version)] but given [ {version} ]')

        # check valid type of version
        try:
            version = float(version[1:])
        except:
            raise ValueError(f'Version should be float but given [ {version[1:]} ] as {type(version[1:])}')

        # experiment_name - 'riiid'
        ex_left_index = len(module) + 1
        ex_right_index = -1 * len(yaml_list[-1]) - 1

        experiment_name = yaml_header[ex_left_index:ex_right_index]

        return module, version, experiment_name



    def read_pickle(self, pickle_path):
        return pd.read_pickle(pickle_path)

    def write_pickle(self, df, pickle_path):
        df.to_pickle(pickle_path)

    def read_yaml(self, yaml_path):
        with open(yaml_path, 'r') as f:
            config_dict = yaml.load(f, Loader=yaml.FullLoader)
        return config_dict

    def write_yaml(self, config_dict, yaml_path):
        with open(yaml_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
