import lxml
import pytest
import metsrw
import rdflib

from app.helpers.graph import parse_graph
from app.helpers.xml import build_mh_sidecar, build_mh_mets, build_minimal_sidecar


@pytest.fixture
def json_ld_graph():
    with open("./tests/resources/example.jsonld", "r") as f:
        json_ld = f.read()
    return json_ld


@pytest.fixture
def material_artwork_ttl_graph():
    with open("./tests/resources/materialartwork.ttl", "r") as f:
        ttl = f.read()
    return ttl


@pytest.fixture
def three_dimensional_ttl_graph():
    with open("./tests/resources/3d.ttl", "r") as f:
        ttl = f.read()
    return ttl


@pytest.fixture
def material_artwork_minimal_rep_graph():
    with open("./tests/resources/materialartwork_minimal_rep.ttl", "r") as f:
        ttl = f.read()
    return ttl


@pytest.fixture
def mh_sidecar_xml():
    with open("./tests/resources/sidecar.xml", "r") as f:
        xml = f.read()
    return xml


@pytest.fixture
def mh_sidecar_fit_xml():
    with open("./tests/resources/sidecar_fit.xml", "r") as f:
        xml = f.read()
    return xml


@pytest.fixture
def mets_xml():
    with open("./tests/resources/mets.xml", "r") as f:
        xml = f.read()
    return xml


@pytest.fixture
def minicar_xml():
    with open("./tests/resources/minicar.xml", "r") as f:
        xml = f.read()
    return xml


@pytest.fixture(
    params=[
        (1, 1, "./tests/resources/local_id_tests/materialartwork_1_id.ttl"),
        (1, 0, "./tests/resources/local_id_tests/materialartwork_1_localid.ttl"),
        (1, 17, "./tests/resources/local_id_tests/materialartwork_complete.ttl"),
        (0, 17, "./tests/resources/local_id_tests/materialartwork_multiple_ids.ttl"),
        (0, 0, "./tests/resources/local_id_tests/materialartwork_no_id.ttl"),
    ]
)
def local_id_graphs(request):
    with open(request.param[2], "r") as f:
        ttl = f.read()
    return {
        "graph": ttl,
        "amount_of_localids": request.param[1],
        "has_main_localid": request.param[0],
    }


@pytest.fixture
def mh_sidecar_material_artwork_minimal_rep_xml():
    with open("./tests/resources/sidecar_material_artwork_minimal_rep.xml", "r") as f:
        xml = f.read()
    return xml


def test_build_mh_sidecar(json_ld_graph, mh_sidecar_xml):
    g = parse_graph(json_ld_graph, "json-ld")

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )

    sidecar = build_mh_sidecar(
        g, [ie], "testpid", {"md5": "18513a8d61c6f2cbaaeeedd754b01d6b"}
    )

    assert sidecar == mh_sidecar_xml


def test_build_mh_sidecar_ttl(material_artwork_ttl_graph, mh_sidecar_fit_xml):
    g = parse_graph(material_artwork_ttl_graph, "ttl")

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )

    sidecar = build_mh_sidecar(g, [ie], "testpid")

    assert sidecar == mh_sidecar_fit_xml


def test_build_material_artwork_mets(material_artwork_ttl_graph):
    g = parse_graph(material_artwork_ttl_graph, "ttl")

    mets = build_mh_mets(g, "testpid", "Disk")

    assert "Disk" in mets
    assert not "Tape" in mets
    assert mets


def test_build_3d_mets(three_dimensional_ttl_graph):
    g = parse_graph(three_dimensional_ttl_graph, "ttl")

    mets = build_mh_mets(g, "testpid", "Disk", {"batch_id": "batch-idke"})

    assert "16354987" in mets
    assert "13548987" in mets
    assert mets


def test_build_minimal_sidecar(minicar_xml):
    minicar = build_minimal_sidecar("abcdefgh")

    assert minicar == minicar_xml


def test_localids_in_sidecar(local_id_graphs):
    g = parse_graph(local_id_graphs["graph"], "ttl")

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )

    sidecar = build_mh_sidecar(g, [ie], "testpid")

    root = lxml.etree.fromstring(sidecar)

    localids = root.findall(".//dc_identifier_localids/*")
    assert len(localids) == local_id_graphs["amount_of_localids"]

    localid = root.findall(".//dc_identifier_localid")
    assert len(localid) == local_id_graphs["has_main_localid"]

    pass


def test_build_mh_sidecar_material_artwork_minimal_rep(
    material_artwork_minimal_rep_graph, mh_sidecar_material_artwork_minimal_rep_xml
):
    g = parse_graph(material_artwork_minimal_rep_graph, "ttl")

    rep = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/Representation"),
    )

    sidecar = build_mh_sidecar(g, [rep], "testpid")

    assert sidecar == mh_sidecar_material_artwork_minimal_rep_xml
