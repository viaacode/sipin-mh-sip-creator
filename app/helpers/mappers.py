import rdflib


def local_id_mapper(graph, objects) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    local_ids = {}
    for object in objects:
        type = graph.namespace_manager.compute_qname(
            graph.value(
                predicate=rdflib.URIRef(
                    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
                ),
                subject=object,
            )
        )[2]
        value = graph.value(
            predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#value"),
            subject=object,
        )
        local_ids[type] = str(value)

    main_local_id = local_ids.pop("MEEMOO-LOCAL-ID", "")

    if not main_local_id and len(list(local_ids)) == 1:
        main_local_id = local_ids[list(local_ids)[0]]

    if main_local_id:
        mapping["mhs:Dynamic.dc_identifier_localid"] = main_local_id

    if local_ids:
        for id_type, id in local_ids.items():
            mapping[f"mhs:Dynamic.dc_identifier_localids.{id_type}"] = [
                *mapping.get(f"mhs:Dynamic.dc_identifier_localids.{id_type}", []),
                id,
            ]

    return mapping


def creator_mapper(graph, creators) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}

    for creator in creators:
        creator_role = graph.value(
            subject=creator, predicate=rdflib.URIRef("https://schema.org/roleName")
        )
        if creator_role is None:
            creator_role = "mhs:Dynamic.dc_creators.Maker[]"
        creator_details = graph.value(
            subject=creator, predicate=rdflib.URIRef("https://schema.org/creator")
        )
        creator_name = graph.value(
            subject=creator_details, predicate=rdflib.URIRef("https://schema.org/name")
        )

        role = f"mhs:Dynamic.dc_creators.{str(creator_role)}[]"
        name = str(creator_name)

        mapping[role] = [*mapping.get(role, []), name]

    return mapping


def license_mapper(graph, licenses):
    license_list = list(licenses)
    mapping = {}
    if license_list:
        mapping = {
            "mhs:Dynamic.dc_rights_licenses.multiselect[]": [
                str(license) for license in license_list
            ]
        }
    else:
        mapping = {
            "mhs:Dynamic.dc_rights_licenses.multiselect[]": [
                "VIAA-ONDERWIJS",
                "VIAA-ONDERZOEK",
                "VIAA-INTRA_CP-CONTENT",
                "VIAA-INTRA_CP-METADATA-ALL",
                "VIAA-PUBLIEK-METADATA-LTD",
                "BEZOEKERTOOL-CONTENT",
                "BEZOEKERTOOL-METADATA-ALL",
            ]
        }

def geometry_mapper(graph, geometries) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}

    for geometry in geometries:
        faces = graph.value(
            subject=geometry,
            predicate=rdflib.URIRef("https://www.w3id.org/gom#hasFaces"),
        )
        vertices = graph.value(
            subject=geometry,
            predicate=rdflib.URIRef("https://www.w3id.org/gom#hasVertices"),
        )

        if faces:
            mapping["mhs:Dynamic.mesh_geometry.number_of_triangles"] = [str(faces)]

        if vertices:
            mapping["mhs:Dynamic.mesh_geometry.number_of_vertices"] = [str(vertices)]

    return mapping


def title_mapper(graph, titles) -> dict[str, list[str]]:
    type_map = {
        "BroadcastEvent": "programma",
        "ArchiveComponent": "archief",
        "Episode": "episode",
        "CreativeWorkSeason": "seizoen",
        "CreativeWorkSeries": "serie",
        "Collection": "collectie",
    }
    mapping = {}
    for title in titles:
        name = graph.value(
            subject=title, predicate=rdflib.URIRef("https://schema.org/name")
        )
        type = graph.value(
            subject=title,
            predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        )
        type_text = type_map[graph.namespace_manager.compute_qname(type)[2]]
        parts = list(
            graph.objects(
                subject=title, predicate=rdflib.URIRef("https://schema.org/hasPart")
            )
        )
        if len(parts) > 1:
            for part in parts:
                if graph.value(subject=part, object=type, predicate=None):
                    part_name = graph.value(
                        subject=part,
                        predicate=rdflib.URIRef("https://schema.org/name"),
                    )
                    part_type = f"deel{type_text}"
                    mapping[f"mhs:Dynamic.dc_titles.{part_type}"] = [str(part_name)]
        if season_number := graph.value(
            subject=title, predicate=rdflib.URIRef("https://schema.org/seasonNumber")
        ):
            mapping[f"mhs:Dynamic.dc_titles.{type_text}nummer"] = [str(season_number)]
        if series_position := graph.value(
            subject=title, predicate=rdflib.URIRef("https://schema.org/position")
        ):
            mapping[f"mhs:Dynamic.dc_titles.{type_text}nummer"] = [str(series_position)]

        mapping[f"mhs:Dynamic.dc_titles.{type_text}"] = [str(name)]

    return mapping
