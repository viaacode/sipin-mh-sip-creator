import rdflib


def dimension_transform(graph_result) -> str:
    unit = ""
    value = 0
    for obj in graph_result:
        if obj[0] == rdflib.URIRef("https://schema.org/unitCode"):
            unit = obj[1].toPython()
        if obj[0] == rdflib.URIRef("https://schema.org/value"):
            value = obj[1].toPython()

    if unit == "MMT":
        return str(round(value))
    if unit == "CMT":
        return str(round(value * 10))
    if unit == "MTR":
        return str(round(value * 1000))

    if unit == "KGM":
        return str(value)

    return "0"


def language_code_transform(bcp47_code) -> str:
    return bcp47_code[0:2]


def name_transform(graph_result) -> str:
    name = ""
    for obj in graph_result:
        if obj[0] == rdflib.URIRef("https://schema.org/name"):
            name = obj[1].toPython()
    return name
