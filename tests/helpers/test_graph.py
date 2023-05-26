import pytest

from app.helpers.graph import (
    get_cp_id_from_graph,
    get_representations,
    parse_graph,
    get_local_ids_from_graph,
)


@pytest.fixture
def json_ld_graph():
    with open("./tests/resources/example.jsonld", "r") as f:
        json_ld = f.read()
    return json_ld


def test_parse_graph(json_ld_graph):
    assert parse_graph(json_ld_graph, "json-ld")


def test_get_cp_id_from_graph(json_ld_graph):
    graph = parse_graph(json_ld_graph, "json-ld")

    cp_id = get_cp_id_from_graph(graph)

    assert cp_id == "OR-m30wc4t"


def test_get_local_ids_from_graph(json_ld_graph):
    excepted = {"Object_number": "v_2021073114124363", "local_id": "ce980d9"}
    graph = parse_graph(json_ld_graph, "json-ld")

    local_ids = get_local_ids_from_graph(graph)
    assert local_ids == excepted


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
