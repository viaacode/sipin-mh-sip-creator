import rdflib

from app.models.file import File
from app.models.sip import SIP
from app.models.representation import Representation


def parse_graph(jsonld: str) -> rdflib.Graph:
    """Parses a JSON-LD string into a graph.

    Args:
        jsonld (str): The graph represented as a JSON-LD string.

    Returns:
        rdflib.Graph: The parsed graph.
    """

    g = rdflib.Graph()
    g.parse(data=jsonld, format="json-ld")
    return g


def get_cp_id_from_graph(graph: rdflib.Graph) -> str:
    """Retrieves the CP-id from a given graph.

    Args:
        graph (rdflib.Graph): The metadata graph of the SIP.

    Returns:
        str: The CP-id (OR-XXXXXXX)
    """
    cp = graph.value(
        object=rdflib.URIRef("http://www.w3.org/ns/org#Organization"),
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
    )
    cp_id = graph.value(
        subject=cp, predicate=rdflib.URIRef("https://schema.org/identifier")
    )
    return str(cp_id)


def get_sip_info(graph: rdflib.Graph) -> SIP:
    sip_node = graph.value(
        object=rdflib.URIRef("https://data.hetarchief.be/ns/sip/SIP"),
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
    )

    sip_id = graph.namespace_manager.compute_qname(sip_node)[2]

    sip_profile = ""
    for sip_type in graph.objects(
        subject=sip_node, predicate=rdflib.URIRef("http://purl.org/dc/terms/conformsTo")
    ):
        if sip_type.startswith(graph.namespace_manager.compute_qname(sip_node)[1]):
            sip_profile = graph.namespace_manager.compute_qname(sip_type)[2]

    sip_representations = get_representations(graph)

    sip = SIP(sip_id, sip_profile, sip_representations)

    return sip


def get_local_ids_from_graph(graph: rdflib.Graph) -> dict[str, str]:
    """Retrieves the localids from a given graph.

    Args:
        graph (rdflib.Graph): The metadata graph of the SIP.

    Returns:
        dict[str, str]: A dict where the key is the type of localid, and the value the localid
    """
    localids = {}
    for identifier_object in graph.objects(
        predicate=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/identifier")
    ):
        type = graph.namespace_manager.compute_qname(
            graph.value(
                predicate=rdflib.URIRef(
                    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
                ),
                subject=identifier_object,
            )
        )[2]
        value = graph.value(
            predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#value"),
            subject=identifier_object,
        )
        localids[type] = str(value)
    return localids


def get_representations(graph: rdflib.Graph) -> list[Representation]:
    """Retrieves the representations from a given graph.
    For each representation a list of files is retrieved.

    Args:
        graph (rdflib.Graph): The metadata graph of the SIP.

    Returns:
        list[Representation]: List of the different representations in the SIP.
    """
    representations = []
    for representation in graph.subjects(
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/Representation")
    ):
        r = Representation(str(representation))
        representations.append(r)
        for file in graph.objects(
            subject=representation,
            predicate=rdflib.URIRef(
                "http://id.loc.gov/vocabulary/preservation/relationshipSubType/inc"
            ),
        ):
            f = File(
                str(file),
                str(
                    graph.value(
                        subject=file,
                        predicate=rdflib.URIRef(
                            "http://www.loc.gov/premis/rdf/v3/originalName"
                        ),
                    )
                ),
                str(
                    graph.value(
                        subject=graph.value(
                            subject=file,
                            predicate=rdflib.URIRef(
                                "http://www.loc.gov/premis/rdf/v3/fixity"
                            ),
                        )
                    )
                ),
            )
            r.files.append(f)
    return representations
