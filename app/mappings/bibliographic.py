import rdflib

from app.helpers.transformers import date_transform, value_transform
from app.helpers.mappers import local_id_mapper


def title_mapper(graph, subject, objects) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for object in objects:
        type = graph.namespace_manager.compute_qname(
            graph.value(
                predicate=rdflib.URIRef(
                    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
                ),
                subject=object,
            )
        )[2]
        value = str(
            graph.value(
                predicate=rdflib.URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
                subject=object,
            )
        )
        if type == "Title":
            mapping["mhs:Dynamic.dc_title"] = [value]
            mapping["mhs:Descriptive.mh:Title"] = [value]
        else:
            mapping["mhs:Dynamic.dc_titles.alternatief[]"] = [
                *mapping.get("mhs:Dynamic.dc_titles.alternatief[]", []),
                value,
            ]

    return mapping


def license_mapper(graph, subject, licenses) -> dict[str, list[str]]:
    type = graph.namespace_manager.compute_qname(
        graph.value(
            predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            subject=subject,
        )
    )[2]
    license_list = list(licenses)
    mapping = {}
    if license_list:
        mapping = {
            "mhs:Dynamic.dc_rights_licenses.multiselect[]": [
                str(graph.namespace_manager.compute_qname(license)[2])
                for license in license_list
            ]
        }
    elif type == "IntellectualEntity":
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
    return mapping


def contribution_mapper(graph, subject, contributors) -> dict[str, list[str]]:

    mapping: dict[str, list[str]] = {}

    for contributor in contributors:
        contributor_role = graph.value(
            subject=contributor,
            predicate=rdflib.URIRef("http://id.loc.gov/ontologies/bibframe/role"),
        )

        for obj in graph.predicate_objects(subject=contributor_role):
            if obj[0] == rdflib.URIRef("http://www.w3.org/2000/01/rdf-schema#label"):
                role_label = obj[1].toPython()

        role_mapping = {
            "composer": "Componist",
            "arrangeur": "Arrangeur",
            "adaptation": "Arrangeur",
            "harmonization": "Arrangeur",
            "author": "Auteur",
            "lyricist": "Schrijver",
            "translator": "Vertaler",
        }
        if mapped_role := role_mapping.get(str(role_label)):
            role = f"mhs:Dynamic.dc_creators.{mapped_role}[]"
        else:
            role = f"mhs:Dynamic.dc_creators.Maker[]"

        # check if contributor is person or company
        contributor_details = graph.value(
            subject=contributor,
            predicate=rdflib.URIRef("http://id.loc.gov/ontologies/bibframe/agent"),
        )

        agent_type = graph.value(
            subject=contributor_details,
            predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        )

        if agent_type == rdflib.URIRef(
            "http://id.loc.gov/ontologies/bibframe/Organization"
        ):
            name = str(
                graph.value(
                    subject=contributor_details,
                    predicate=rdflib.URIRef(
                        "http://www.w3.org/2000/01/rdf-schema#label"
                    ),
                )
            )

        if agent_type == rdflib.URIRef("http://id.loc.gov/ontologies/bibframe/Person"):
            contributor_given_name = graph.value(
                subject=contributor_details,
                predicate=rdflib.URIRef("https://schema.org/givenName"),
            )
            contributor_family_name = graph.value(
                subject=contributor_details,
                predicate=rdflib.URIRef("https://schema.org/familyName"),
            )

            name = str(
                " ".join([str(contributor_given_name), str(contributor_family_name)])
            )

        mapping[role] = [*mapping.get(role, []), name]

    return mapping


def carrier_mapper(graph, subject, carriers) -> dict[str, list[str]]:

    mapping: dict[str, list[str]] = {}

    for carrier in carriers:
        extents = graph.objects(
            predicate=rdflib.URIRef("http://id.loc.gov/ontologies/bibframe/extent"),
            subject=carrier,
        )
        for extent in extents:
            unit = graph.value(
                subject=extent,
                predicate=rdflib.URIRef("http://id.loc.gov/ontologies/bibframe/unit"),
            )
            unit_label = str(
                graph.value(
                    subject=unit,
                    predicate=rdflib.URIRef(
                        "http://www.w3.org/2000/01/rdf-schema#label"
                    ),
                )
            )

            extent_string = str(
                graph.value(
                    subject=extent,
                    predicate=rdflib.URIRef(
                        "http://www.w3.org/2000/01/rdf-schema#label"
                    ),
                )
            )
            if unit_label == "sheets":
                mapping["mhs:Dynamic.number_of_pages"] = [extent_string]

            if unit_label == "cm":
                width_and_height = extent_string.split(" x ")
                width_in_mm = str(round(float(width_and_height[0]) * 10))
                height_in_mm = str(round(float(width_and_height[1]) * 10))

                mapping["mhs:Dynamic.dimensions.height_in_mm"] = [height_in_mm]
                mapping["mhs:Dynamic.dimensions.width_in_mm"] = [width_in_mm]

            if unit_label == "mm":
                width_and_height = extent_string.split(" x ")
                width_in_mm = str(round(float(width_and_height[0])))
                height_in_mm = str(round(float(width_and_height[1])))

                mapping["mhs:Dynamic.dimensions.height_in_mm"] = [height_in_mm]
                mapping["mhs:Dynamic.dimensions.width_in_mm"] = [width_in_mm]

    return mapping


def provision_activity_mapper(graph, subject, activities) -> dict[str, list[str]]:

    mapping: dict[str, list[str]] = {}

    for activity in activities:
        place = graph.value(
            subject=activity,
            predicate=rdflib.URIRef("http://id.loc.gov/ontologies/bibframe/place"),
        )
        place_code = graph.value(
            subject=place,
            predicate=rdflib.URIRef("http://id.loc.gov/ontologies/bibframe/code"),
        )
        place_name = graph.value(
            subject=place,
            predicate=rdflib.URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
        )

        key = "mhs:Dynamic.dc_coverages.ruimte[]"
        if place_code:
            mapping[key] = [*mapping.get(key, []), str(place_code)]

        if place_name:
            mapping[key] = [*mapping.get(key, []), str(place_name)]

    return mapping


NAME: str = "Bibliographic"

MAPPING: dict = {
    "http://id.loc.gov/ontologies/bibframe/title": {
        "mapping_strategy": title_mapper,
        "targets": [
            "mhs:Descriptive.mh:Title",
            "mhs:Dynamic.dc_title",
        ],
    },
    "http://id.loc.gov/ontologies/bibframe/summary": {
        "targets": [
            "mhs:Dynamic.dc_description_lang",
            "mhs:Descriptive.mh:Description",
        ]
    },
    # "http://id.loc.gov/ontologies/bibframe/genreForm": {
    #     "targets": ["mhs:Dynamic.dc_types.multiselect[]"],
    # },
    "http://id.loc.gov/ontologies/bibframe/provisionActivity": {
        "targets": ["mhs:Dynamic.dcterms_issued"],
        "transformer": date_transform,
    },
    "http://id.loc.gov/ontologies/bibframe/originDate": {
        "targets": ["mhs:Dynamic.dcterms_created"],
    },
    "http://id.loc.gov/ontologies/bibframe/subject": {
        "targets": ["mhs:Dynamic.dc_subjects.Trefwoord[]"],
    },
    "http://id.loc.gov/ontologies/bibframe/contribution": {
        "mapping_strategy": contribution_mapper,
    },
    "https://data.hetarchief.be/ns/bibliographic/numberOfPages": {
        "targets": ["mhs:Dynamic.number_of_pages"],
    },
    "http://id.loc.gov/ontologies/bibframe/carrier": {
        "mapping_strategy": carrier_mapper
    },
    "http://id.loc.gov/ontologies/bibframe/usageAndAccessPolicy": {
        "mapping_strategy": license_mapper,
        "targets": ["mhs:Dynamic.dc_rights_licenses.multiselect[]"],
    },
    "http://id.loc.gov/ontologies/bibframe/provisionActivity": {
        "mapping_strategy": provision_activity_mapper,
    },
    "http://www.loc.gov/premis/rdf/v3/identifier": {
        "mapping_strategy": local_id_mapper,
    },
}
