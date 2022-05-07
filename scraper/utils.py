def get_attribute_by_path(dictionary, attribute_path, default=None):
    current_attr = dictionary
    for key in list(filter(lambda x: x, attribute_path.split('.'))):
        current_attr = current_attr.get(key)
        if not current_attr:
            return default
    else:
        return current_attr
