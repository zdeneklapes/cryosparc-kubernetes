def delete_none(_dict):
    """
    Delete None values recursively from all of the dictionaries
    Source: https://stackoverflow.com/a/66127889/14471542
    """
    for key, value in list(_dict.items()):
        if isinstance(value, dict):
            delete_none(value)
        elif value is None:
            del _dict[key]
        elif isinstance(value, list):
            for v_i in value:
                if isinstance(v_i, dict):
                    delete_none(v_i)

    return _dict


def transform_dict(data):
    """
    Transform dictionary keys from snake_case to camelCase
    :param data:
    :return:
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = ''.join(word.capitalize() for word in key.split('_'))
            new_key = new_key[0].lower() + new_key[1:]
            new_dict[new_key] = transform_dict(value)
        return new_dict
    elif isinstance(data, list):
        return [transform_dict(item) for item in data]
    else:
        return data

if __name__ == '__main__':
    # Example input dictionary
    input_dict = {
        "first_name": "john",
        "last_name": "doe",
        "address": {
            "street_address": "123 Main St",
            "city_name": "example city"
        }
    }

    output_dict = transform_dict(input_dict)
    print(output_dict)