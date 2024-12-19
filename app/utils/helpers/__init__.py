def dynamo_to_json(dynamo_data):
    if isinstance(dynamo_data, list):
        return [dynamo_to_json(item) for item in dynamo_data]

    if not isinstance(dynamo_data, dict):
        return dynamo_data

    if not any(key in dynamo_data for key in ("S", "N", "L", "M")):
        return {k: dynamo_to_json(v) for k, v in dynamo_data.items()}

    for type_key, value in dynamo_data.items():
        if type_key == "S":
            return value
        elif type_key == "N":
            return float(value) if "." in value else int(value)
        elif type_key == "L":
            return [dynamo_to_json(item) for item in value]
        elif type_key == "M":
            return {k: dynamo_to_json(v) for k, v in value.items()}

    return None


def json_to_dynamo(data):
    if isinstance(data, str):
        return {"S": data}
    elif isinstance(data, (int, float)):
        return {"N": str(data)}
    elif isinstance(data, list):
        return {"L": [json_to_dynamo(item) for item in data]}
    elif isinstance(data, dict):
        return {k: json_to_dynamo(v) for k, v in data.items()}
    elif data is None:
        return {"NULL": True}
    elif isinstance(data, bool):
        return {"BOOL": data}
    else:
        return {"S": str(data)}


__all__ = ["dynamo_to_json", "json_to_dynamo"]
