def get_attribute_by_path(dictionary, attribute_path, default=None):
    current_attr = dictionary
    for key in list(filter(lambda x: x, attribute_path.split('.'))):
        current_attr = current_attr.get(key)
        if current_attr is None:
            return default
    else:
        return current_attr
