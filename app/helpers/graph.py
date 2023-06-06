import rdflib
import json

from app.models.file import File
from app.models.representation import Representation


class GraphException(Exception):
    pass


def parse_graph(data: str, format: str = "json-ld") -> rdflib.Graph:
    """Parses a string into a graph. The format of the graph serialization should be passed.
    If format is None, empty or invalid, json-ld will be used.
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
