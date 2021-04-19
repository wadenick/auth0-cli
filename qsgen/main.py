import os
import sys
import yaml
import json
import frontmatter

QS_SUBPATH = 'articles/quickstart'

YAML_FILE_NAME = 'index.yml'
YAML_TITLE_KEY = 'title'
YAML_ARTICLES_KEY = 'articles'
YAML_GITHUB_KEY = 'github'
YAML_ORG_KEY = 'org'
YAML_REPO_KEY = 'repo'
YAML_BRANCH_KEY = 'branch'
YAML_PATH_KEY = 'path'

JSON_FILE_PATH = '../internal/cli/data/quickstarts.json'
JSON_NAME_KEY = 'name'
JSON_PATH_KEY = 'path'
JSON_SAMPLES_KEY = 'samples'
JSON_ORG_KEY = 'org'
JSON_REPO_KEY = 'repo'
JSON_BRANCH_KEY = 'branch'


def map_json(yaml_dict):
    return {
        JSON_NAME_KEY:
        yaml_dict[YAML_TITLE_KEY],
        JSON_PATH_KEY:
        yaml_dict[YAML_PATH_KEY],
        JSON_SAMPLES_KEY:
        yaml_dict[YAML_ARTICLES_KEY],
        JSON_ORG_KEY:
        yaml_dict[YAML_GITHUB_KEY][YAML_ORG_KEY],
        JSON_REPO_KEY:
        yaml_dict[YAML_GITHUB_KEY][YAML_REPO_KEY],
        JSON_BRANCH_KEY:
        yaml_dict[YAML_GITHUB_KEY].get(YAML_BRANCH_KEY) or 'master'
    }


def get_root_path(base_path):
    return os.path.join(base_path, QS_SUBPATH)


def get_type_path(root_path, qs_type):
    return os.path.join(root_path, qs_type)


def get_qs_path(type_path, qs):
    return os.path.join(type_path, qs)


def get_yaml_path(qs_path):
    return os.path.join(qs_path, YAML_FILE_NAME)


def get_qs_types(root_path):
    qs_types = [
        name for name in os.listdir(root_path)
        if os.path.isdir(os.path.join(root_path, name))
    ]
    qs_types.sort()
    return qs_types


def load_yaml(yaml_path):
    with open(yaml_path, 'r') as stream:
        yaml_string = stream.read().replace('\t', '  ')
        yaml_dict = yaml.safe_load(yaml_string)
    return {
        key: value
        for key, value in yaml_dict.items()
        if key in [YAML_TITLE_KEY, YAML_ARTICLES_KEY, YAML_GITHUB_KEY]
    }


def load_all_for_type(root_path, qs_type):
    type_path = get_type_path(root_path, qs_type)
    qs_folders = [
        folder for folder in os.listdir(type_path)
        if not folder.startswith('_')
        and os.path.isdir(os.path.join(type_path, folder))
    ]
    yaml_list = []

    for folder_name in qs_folders:
        folder_path = os.path.join(type_path, folder_name)
        yaml_path = get_yaml_path(get_qs_path(type_path, folder_name))
        if os.path.exists(yaml_path):
            yaml = load_yaml(yaml_path)
            yaml[YAML_PATH_KEY] = folder_name
            yaml[YAML_ARTICLES_KEY] = []

            if YAML_PATH_KEY in yaml.get(YAML_GITHUB_KEY, {}):
                yaml[YAML_ARTICLES_KEY].append(
                    yaml[YAML_GITHUB_KEY][YAML_PATH_KEY])

            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if file_name.endswith('.md') and os.path.isfile(file_path):
                    with open(file_path) as f:
                        fm_yaml = frontmatter.load(f)
                        if YAML_PATH_KEY in fm_yaml.get(
                                YAML_GITHUB_KEY,
                            {}) and fm_yaml[YAML_GITHUB_KEY][
                                YAML_PATH_KEY] not in yaml[YAML_ARTICLES_KEY]:
                            yaml[YAML_ARTICLES_KEY].append(
                                fm_yaml[YAML_GITHUB_KEY][YAML_PATH_KEY])

            yaml[YAML_ARTICLES_KEY].sort()
            yaml_list.append(yaml)

    yaml_list = sorted(yaml_list, key=lambda x: x[YAML_TITLE_KEY].lower())

    return [
        map_json(value) for value in yaml_list
        if value.get(YAML_GITHUB_KEY) is not None and value[YAML_ARTICLES_KEY]
    ]


def load_all(root_path, qs_types):
    return {
        qs_type: load_all_for_type(root_path, qs_type)
        for qs_type in qs_types
    }


def write_json(dictionary):
    json_string = json.dumps(dictionary, indent=2)
    with open(JSON_FILE_PATH, 'w') as writer:
        writer.write(json_string)


def generate_json(base_path):
    root_path = get_root_path(base_path)
    qs_types = get_qs_types(root_path)
    all = load_all(root_path, qs_types)
    write_json(all)
    print(f'File written to {os.path.abspath(JSON_FILE_PATH)}')


if __name__ == "__main__":
    # TODO: Split into 2 commands, 'check' and 'gen'
    if (len(sys.argv) != 2):
        raise Exception(
            f'Wrong number of parameters; expected 1, got {len(sys.argv) - 1}')
    generate_json(sys.argv[1])
