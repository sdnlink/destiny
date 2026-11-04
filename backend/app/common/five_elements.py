from types import MappingProxyType


FIVE_ELEMENTS_GENERATES = MappingProxyType({"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"})
FIVE_ELEMENTS_CONTROLS = MappingProxyType({"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"})

# 体用五行关系：唯一实现。梅花引擎与七步工作流都从这里取，避免各写一份。
ELEMENT_RELATION_LABELS = MappingProxyType({
    "same_element": "体用比和",
    "use_generates_body": "用生体",
    "body_generates_use": "体生用",
    "use_controls_body": "用克体",
    "body_controls_use": "体克用",
})


def validate_element(value):
    if value not in FIVE_ELEMENTS_GENERATES:
        raise ValueError("unknown five element: {}".format(value))
    return value


def element_relation(body_element, use_element):
    """返回体（自身）与用（事项）之间的五行关系。"""
    validate_element(body_element)
    validate_element(use_element)
    if body_element == use_element:
        code = "same_element"
    elif FIVE_ELEMENTS_GENERATES[use_element] == body_element:
        code = "use_generates_body"
    elif FIVE_ELEMENTS_GENERATES[body_element] == use_element:
        code = "body_generates_use"
    elif FIVE_ELEMENTS_CONTROLS[use_element] == body_element:
        code = "use_controls_body"
    elif FIVE_ELEMENTS_CONTROLS[body_element] == use_element:
        code = "body_controls_use"
    else:
        raise ValueError("unknown five-element relationship")
    return {"code": code, "label": ELEMENT_RELATION_LABELS[code]}
