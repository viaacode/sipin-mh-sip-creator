import lxml
import pytest

from app.helpers.graph import parse_graph
from app.helpers.xml import build_mh_sidecar


@pytest.fixture
def json_ld_graph():
    with open("./tests/resources/example.jsonld", "r") as f:
        json_ld = f.read()
    return json_ld


@pytest.fixture
def mh_sidecar_xml():
    with open("./tests/resources/sidecar.xml", "r") as f:
        xml = f.read()
    return xml


def test_build_mh_sidecar(json_ld_graph, mh_sidecar_xml):
    g = parse_graph(json_ld_graph, "json-ld")

    sidecar = build_mh_sidecar(g)

    assert sidecar == mh_sidecar_xml
