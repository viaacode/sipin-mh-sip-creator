import rdflib


def dimension_transform(graph, graph_result) -> str:
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

    return "0"


def language_code_transform(bcp47_code) -> str:
    return bcp47_code[0:2]


def creator_transform(graph, graph_result) -> str:
    for obj in graph_result:
        if obj[0].toPython() == "https://schema.org/creator":
            creator_name = graph.value(
                subject=obj[1], predicate=rdflib.URIRef("https://schema.org/name")
            ).toPython()
        if obj[0].toPython() == "https://schema.org/roleName":
            creator_target = f"Dynamic.dc_creators.{obj[1].toPython()}[]"
        else:
            creator_target = "Dynamic.dc_creators.Maker[]"
    return (creator_target, creator_name)
