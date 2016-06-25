from collections import namedtuple


Module = namedtuple("Module", "file_name declarations")
Enum = namedtuple("Enum", "name tags")
Tag = namedtuple("Tag", "name")
Record = namedtuple("Record", "name attributes")
Attribute = namedtuple("Attribute", "name type")
Function = namedtuple("Function", "name parameters return_type")
Parameter = namedtuple("Parameter", "name type")
Type = namedtuple("Type", "name")
List = namedtuple("List", "type")
Dict = namedtuple("Dict", "keys_type values_type")
Union = namedtuple("Union", "name types")
Nullable = namedtuple("Nullable", "type")
