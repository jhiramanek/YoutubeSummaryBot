import json
from json import JSONEncoder
import jsonschema
from jsonschema import validate

# define record schema
recordSchema = {
    "type": "object",
    "properties": {
        "chunk_id": {"type": "number"},
        "title": {"type": "string"},
        "video_id": {"type": "string"},
        "chunk_summary": {"type": "string"}
    },
}

# define record schema
tagSchema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "decription": {"type": "string"},
        "title": {"type": "string"},
        "video_id": {"type": "string"},
        "Tag": {"type": "string"}
    },
}


class Record:
    def __init__(self, chunk_id, title, video_id, chunk_summary):
        self.chunk_id = chunk_id
        self.title = title
        self.video_id = video_id
        self.chunk_summary = chunk_summary


class Tag:
    def __init__(self, id, desc, title, video_id, tag):
        self.id = id
        self.description = desc
        self.title = title
        self.video_id = video_id
        self.tag = tag


class TagEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Tag):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


class RecordEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Record):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


def validate_record_json(record_json):
    try:
        record = json.loads(record_json)
        validate(record, recordSchema)
        return True
    except jsonschema.ValidationError as err:
        print(f"Validation error: {err.message}")
        return False
    except json.JSONDecodeError as err:
        print(f"JSON decode error: {err}")
        return False


def validate_tag_json(tag_json):
    try:
        tags = json.loads(tag_json)
        validate(tags, tagSchema)
        return True
    except jsonschema.ValidationError as err:
        print(f"Validation error: {err.message}")
        return False
    except json.JSONDecodeError as err:
        print(f"JSON decode error: {err}")
        return False


def get_record_json(chunk_id, title, video_id, chunk_summary):
    record_instance = Record(chunk_id, title,
                             video_id, chunk_summary)
    recordjson = json.dumps(record_instance, indent=4, cls=RecordEncoder)
    if validate_record_json(recordjson):
        return recordjson
    else:
        print("Invalid record: ", recordjson)
        return None


def get_tags_json(id, desc, title, video_id, tags):
    tag_instance = Tag(id, desc, title, video_id, tags)
    tagjson = json.dumps(tag_instance, indent=4, cls=TagEncoder)
    if validate_tag_json(tagjson):
        return tagjson
    else:
        print("Invalid record: ", tagjson)
        return None
