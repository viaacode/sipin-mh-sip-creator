import rdflib


def local_id_mapper(graph, objects):
    mapping = {}
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


def creator_mapper(graph, creators):
    mapping = {}

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


def geometry_mapper(graph, geometries):
    mapping = {}

    for geometry in geometries:
        faces = graph.value(subject=geometry, predicate=rdflib.URIRef("https://www.w3id.org/gom#hasFaces"))
        vertices = graph.value(subject=geometry, predicate=rdflib.URIRef("https://www.w3id.org/gom#hasVertices"))

        if faces:
            mapping["mhs:Dynamic.mesh_geometry.number_of_triangles"] = [str(faces)]
        
        if vertices:
            mapping["mhs:Dynamic.mesh_geometry.number_of_vertices"] = [str(vertices)]
        

    return mapping
