import rdflib

from app.models.file import File
from app.models.sip import SIP
from app.models.representation import Representation


class GraphException(Exception):
    pass


def parse_graph(data: str, format: str = "json-ld") -> rdflib.Graph:
    """Parses a string into a graph. The format of the graph serialization should be passed.
    If format is an empty string or an invalid format, json-ld will be used.
    Valid formats include:  "xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig", "nquads", "json-ld", "hext".

    Args:
        data (str): The serialized graph.
        format (str, optional): The serialization format of the graph representation. Defaults to "json-ld"

    Raises:
        GraphException: When the graph can't be parsed using the supplied format or when the graph is not json-ld, but the format is empty/invalid.

    Returns:
        rdflib.Graph: The parsed graph.
    """
    g = rdflib.Graph()

    try:
        return g.parse(data=data, format=format)
    except rdflib.plugin.PluginException:
        # An invalid format is given. Retry using json-ld.
        try:
            return g.parse(data=data, format="json-ld")
        except Exception:
            raise GraphException(
                "Graph can't be parsed as the supplied format is invalid and the graph is not json-ld.",
                data,
                format,
            )
    except Exception:
        raise GraphException(
            "Graph can't be parsed using the supplied format.", data, format
        )


def get_cp_id_from_graph(graph: rdflib.Graph) -> str:
    """Retrieves the CP-id of the archivist from a given graph. Returns an empty string if no CP-id is found.

    Args:
        graph (rdflib.Graph): The metadata graph of the SIP.

    Returns:
        str: The CP-id (OR-XXXXXXX) or an empty string.
    """
    organizations = graph.subjects(
        object=rdflib.URIRef("http://www.w3.org/ns/org#Organization"),
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
    )

    for organization in organizations:
        agents = graph.subjects(
            object=organization, predicate=rdflib.URIRef("https://schema.org/agent")
        )
        for agent in agents:
            role = graph.value(
                subject=agent, predicate=rdflib.URIRef("https://schema.org/roleName")
            )

            if str(role) == "ARCHIVIST":
                cp_id = graph.value(
                    subject=organization,
                    predicate=rdflib.URIRef("https://schema.org/identifier"),
                )

                return str(cp_id)
    return ""


def get_sp_id_from_graph(graph: rdflib.Graph) -> str:
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

    # sip_ies = get_intellectual_entities(graph)
    sip_representations = get_representations(graph)

    sip = SIP(sip_id, sip_profile, [], sip_representations)

    return sip


def get_pid_from_graph(graph: rdflib.Graph) -> str:
    """Retrieves the PID from a given graph. Returns an empty string if no PID is found.

    Args:
        graph (rdflib.Graph): The metadata graph of the SIP.

    Returns:
        str: The PID or an empty string.
    """
    pid_node = graph.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("https://data.hetarchief.be/id/object/MEEMOO-PID"),
    )
    if pid_node:
        pid = graph.value(subject=pid_node)
        return str(pid)

    return ""


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
        label = graph.value(
            subject=representation,
            predicate=rdflib.URIRef("http://www.w3.org/2004/02/skos/core#hiddenLabel"),
        )

        r = Representation(
            id=str(representation), label=str(label), node=representation
        )

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
