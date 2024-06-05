import pytest

from app.helpers.graph import (
    get_cp_info_from_graph,
    get_representations,
    parse_graph,
    GraphException,
    get_sip_info,
    get_pid_from_graph,
)


@pytest.fixture
def json_ld_graph():
    with open("./tests/resources/example.jsonld", "r") as f:
        json_ld = f.read()
    return json_ld


@pytest.fixture
def turtle_graph():
    with open("./tests/resources/example.ttl", "r") as f:
        ttl = f.read()
    return ttl


@pytest.fixture
def material_artwork_ttl_graph():
    with open("./tests/resources/materialartwork.ttl", "r") as f:
        ttl = f.read()
    return ttl

@pytest.fixture
def newspaper_ttl_graph():
    with open("./tests/resources/newspaper.ttl", "r") as f:
        ttl = f.read()
    return ttl


@pytest.fixture
def threed_ttl_graph():
    with open("./tests/resources/3d.ttl", "r") as f:
        ttl = f.read()
    return ttl

@pytest.fixture
def bibliographic_ttl_graph():
    with open("./tests/resources/bibliographic.ttl", "r") as f:
        ttl = f.read()
    return ttl


def test_parse_json_graph_json_ld(json_ld_graph):
    assert parse_graph(json_ld_graph, "json-ld")


def test_parse_turtle_graph_turtle(turtle_graph):
    assert parse_graph(turtle_graph, "turtle")


def test_parse_turtle_graph_ttl(turtle_graph):
    assert parse_graph(turtle_graph, "ttl")


def test_parse_turtle_graph_text_turtle(turtle_graph):
    assert parse_graph(turtle_graph, "text/turtle")


def test_parse_json_graph_default(json_ld_graph):
    assert parse_graph(json_ld_graph)


def test_parse_json_graph_invalid_format(json_ld_graph):
    assert parse_graph(json_ld_graph, "foobar")


def test_parse_turtle_graph_invalid_format(turtle_graph):
    with pytest.raises(GraphException):
        assert parse_graph(turtle_graph, "")


def test_get_cp_info_from_graph(json_ld_graph):
    graph = parse_graph(json_ld_graph, "json-ld")

    cp = get_cp_info_from_graph(graph)

    assert cp
    assert cp.id == "OR-5h7bt1n"
    assert cp.label == "KMSKA"


def test_get_pid_from_turtle_graph(material_artwork_ttl_graph):
    graph = parse_graph(material_artwork_ttl_graph, "turtle")

    pid = get_pid_from_graph(graph)

    assert pid == "7m03z1634f"


def test_get_pid_from_graph(json_ld_graph):
    graph = parse_graph(json_ld_graph, "json-ld")

    pid = get_pid_from_graph(graph)

    assert pid == ""


def test_get_representations(json_ld_graph):
    graph = parse_graph(json_ld_graph, "json-ld")

    representations = get_representations(graph)

    assert len(representations) == 1
    assert len(representations[0].files) == 1
    assert (
        representations[0].id
        == "https://data.hetarchief.be/id/object/uuid-4e475706-2752-4f77-9069-1f71c0e22572"
    )
    assert representations[0].files[0].fixity == "18513a8d61c6f2cbaaeeedd754b01d6b"
    assert representations[0].files[0].filename == "D523F963.jpg"
    assert (
        representations[0].files[0].id
        == "https://data.hetarchief.be/id/object/uuid-945a16cd-eeb6-4a4c-95bb-4656a9f0909d"
    )


def test_get_sip_info(json_ld_graph):
    graph = parse_graph(json_ld_graph)

    sip = get_sip_info(graph)

    assert sip.id == "uuid-de61d4af-d19c-4cc7-864d-55573875b438"
    assert sip.profile == "basic"
    assert len(sip.representations) == 1


def test_get_sip_info_3d(threed_ttl_graph):
    graph = parse_graph(threed_ttl_graph, format="ttl")

    sip = get_sip_info(graph)

    assert sip.profile == "material-artwork"
    assert len(sip.representations) == 4
    assert sip.batch_id == "PRD-BD-OR-x921j0n-2022-11-10-001"
    assert sip.format == "3D-model"

def test_newspaper_ordering(newspaper_ttl_graph):
    graph = parse_graph(newspaper_ttl_graph, format="ttl")

    sip = get_sip_info(graph)

    assert len(sip.representations) == 3
    assert sip.representations[0].label <= sip.representations[1].label <= sip.representations[2].label
    assert len(sip.representations[2].files) == 22
    