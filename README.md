# yaml_configuration_manager

🦆🦆🦆 A simple tool to manage yaml file by modules 🦆🦆🦆🦆

<img src="https://github.com/IllgamhoDuck/yaml_configuration_manager/blob/main/images/structure.png?raw=true" width="400">

## Program dependency
- pandas
- yaml
- datetime
- glob
- shutil
- logging

## 1. project name and path must be given
- `project path` should be the root path of the project folder
- You can directly use the code form ``

```python
from configuration_manager import ConfigurationManager

config = ConfigurationManager(project_name=PROJECT_NAME,
                              project_path=PROJECT_PATH)
```

## 2. Manage Modules
- create or delete modules

```python
config.create_module('data')
config.delete_module('data')
```

## 3. Manage YAML files
- If experiment name is not given project name will be used alternatively
- In case of using yaml name directly the format should follow
  - **`(module)_(experiment name)_v(version).yaml`**

<img src="https://github.com/IllgamhoDuck/yaml_configuration_manager/blob/main/images/yaml_format.png?raw=true" width="450">

```python
config.create(module=MODULE_NAME, version=1.0)
config.update(module=MODULE_NAME, version=1.0, config_dict=update_config)
config.get(module=MODULE_NAME, version=1.0)
config.delete(module=MODULE_NAME, version=1.0)

config.create_yaml(yaml)
config.update_yaml(yaml, update_config)
config.get_yaml(yaml)
config.delete_yaml(yaml)

config.show(MODULE_NAME)
config.show_all()
```

## 4. Manage Experiment
- All records will be saved at pandas DataFrame
- Record of the experiment will be saved manually
- Load & Delete is controlled by index of record dataframe

```python
config.show_experiment()

config.save_experiment(MODULE_NAME, 1.0, note="explanation about this experiment or yaml file")
config.load_experiment(2)
config.delete_experiment(5)
```

## 5. History
- Tracking the most recently used configuration files for each project

```python
config.show_history()
```
