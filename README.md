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

## Example of usage

### ML Pipeline Managing
- data
- train
- test

```python
# create config and load
config.create(module='data', version=1.0)
config.create(module='train', version=1.0)
config.create(module='test', version=1.0)
data_config = config.get(module='data', version=1.0)

# Add information to the data
data_config['url'] = 'duck.quark.happy.com'
data_config['db'] = 'postgressql'
data_config['encoding type note'] = "I'm working on blah blah blah"
data_config['scaling'] = {'mean': 1.0, 'var': 0.5}

# update yaml
config.update(module='data', version=1.0, config_dict=data_config)
```

### ML Model Hyperparameter Managing
```python
for model in ['lgbm', 'svm', 'linear regression']:
    config.create(module=model, version=1.0)
```

- Hyperparameter Setting

```python
lgbm_config = config.get(module='lgbm', version=1.0)
for ex in ['type 1', 'type 2', 'type 3']:
    lgbm_config['hyperparameter setting'] = {'type': ex, 'and': 'much more'}
    config.create(module='lgbm', version=1.0, experiment_name=f'hyperparameter {ex}', config_dict=lgbm_config)
```

- Hyperparameter Grid Search Setting

```python
del lgbm_config['hyperparameter setting']

# Version  1.0
lgbm_config['lr'] = [0.1, 0.001, 0.0001]
lgbm_config['max_depth'] = [1, 5, 100]
lgbm_config['bagging_fraction'] = [0.1, 0.5, 0.7]

config.create(module='lgbm', version=1.0, experiment_name='gridsearch', config_dict=lgbm_config)

# Version  1.2
lgbm_config['lr'] = [0.001, 0.005, 0.007, 0.009, 0.0001]
lgbm_config['max_depth'] = [5, 10, 20, 30, 50]
lgbm_config['bagging_fraction'] = [0.5, 0.55, 0.56, 0.57, 0.7]

config.create(module='lgbm', version=1.2, experiment_name='gridsearch', config_dict=lgbm_config)
```

### Read all yaml files in specific module

```python
for yaml_name in config.show('lgbm'):
    print(config.get_yaml(yaml_name))
```
