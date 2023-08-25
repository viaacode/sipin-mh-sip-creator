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


def test_build_mh_sidecar(json_ld_graph, mh_sidecar_xml):
    g = parse_graph(json_ld_graph, "json-ld")

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )

    sidecar = build_mh_sidecar(
        g, ie, "testpid", {"md5": "18513a8d61c6f2cbaaeeedd754b01d6b"}
    )

    assert sidecar == mh_sidecar_xml


@pytest.mark.ttl
def test_build_mh_sidecar_ttl(material_artwork_ttl_graph, mh_sidecar_fit_xml):
    g = parse_graph(material_artwork_ttl_graph, "ttl")

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )

    sidecar = build_mh_sidecar(g, ie, "testpid")

    assert sidecar == mh_sidecar_fit_xml


@pytest.mark.ttl
def test_build_material_artwork_mets(material_artwork_ttl_graph):
    g = parse_graph(material_artwork_ttl_graph, "ttl")

    mets = build_mh_mets(g, "testpid", "Disk")

    assert "Disk" in mets
    assert not "Tape" in mets
    assert mets


@pytest.mark.ttl
def test_build_minimal_sidecar(minicar_xml):
    minicar = build_minimal_sidecar("abcdefgh")

    assert minicar == minicar_xml
