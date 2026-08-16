from types import MappingProxyType


FIVE_ELEMENTS_GENERATES = MappingProxyType({"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"})
FIVE_ELEMENTS_CONTROLS = MappingProxyType({"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"})


def validate_element(value):
    if value not in FIVE_ELEMENTS_GENERATES:
        raise ValueError("unknown five element: {}".format(value))
    return value
