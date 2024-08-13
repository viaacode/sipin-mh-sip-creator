import lxml
import pytest
import rdflib
from freezegun import freeze_time

from app.helpers.graph import parse_graph
from app.helpers.xml import build_bibliographic_mh_mets, build_mh_sidecar, build_mh_mets, build_minimal_sidecar, build_newspaper_mh_mets, build_basic_mh_mets
from app.mappings import material_artwork


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
def newspaper_ttl_graph():
    with open("./tests/resources/newspaper.ttl", "r") as f:
        ttl = f.read()
    return ttl

@pytest.fixture
def basic_ttl_graph():
    with open("./tests/resources/basic.ttl", "r") as f:
        ttl = f.read()
    return ttl

@pytest.fixture
def three_dimensional_ttl_graph():
    with open("./tests/resources/3d.ttl", "r") as f:
        ttl = f.read()
    return ttl

@pytest.fixture
def bibliographic_ttl_graph():
    with open("./tests/resources/bibliographic.ttl", "r") as f:
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
def basic_mets_xml():
    with open("./tests/resources/basic_mets.xml", "r") as f:
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
        material_artwork.MAPPING,
        g,
        [ie],
        "testpid",
        {"dynamic": {"md5": "18513a8d61c6f2cbaaeeedd754b01d6b"}, "descriptive": {"OriginalFilename": "abc.zip"}},
    )

    assert sidecar == mh_sidecar_xml


def test_build_mh_sidecar_ttl(material_artwork_ttl_graph, mh_sidecar_fit_xml):
    g = parse_graph(material_artwork_ttl_graph, "ttl")

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )

    sidecar = build_mh_sidecar(material_artwork.MAPPING, g, [ie], "testpid")

    assert sidecar == mh_sidecar_fit_xml


def test_build_material_artwork_mets(material_artwork_ttl_graph):
    g = parse_graph(material_artwork_ttl_graph, "ttl")

    mets = build_mh_mets(g, "testpid", "Disk")

    assert "Disk" in mets
    assert not "Tape" in mets
    assert mets


def test_build_3d_mets(three_dimensional_ttl_graph):
    g = parse_graph(three_dimensional_ttl_graph, "ttl")

    mets = build_mh_mets(g, "testpid", "Disk", {f"dynamic":{"batch_id": "batch-idke"}})

    assert "16354987" in mets
    assert "13548987" in mets


@freeze_time("2023-11-28")
def test_build_minimal_mets(material_artwork_minimal_rep_graph, mets_xml):
    g = parse_graph(material_artwork_minimal_rep_graph, "ttl")

    mets = build_mh_mets(g, "testpid", "Disk", {f"dynamic":{"batch_id": "batch-idke"}})

    assert "2023-11-28" in mets
    assert sorted(mets) == sorted(mets_xml)


def test_build_minimal_sidecar(minicar_xml):
    minicar = build_minimal_sidecar("abcdefgh")

    assert minicar == minicar_xml


def test_localids_in_sidecar(local_id_graphs):
    g = parse_graph(local_id_graphs["graph"], "ttl")

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )

    sidecar = build_mh_sidecar(material_artwork.MAPPING, g, [ie], "testpid")

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

    sidecar = build_mh_sidecar(material_artwork.MAPPING, g, [rep], "testpid")

    assert sidecar == mh_sidecar_material_artwork_minimal_rep_xml
    
def test_build_newspaper_mets(newspaper_ttl_graph):
    g = parse_graph(newspaper_ttl_graph, "ttl")

    mets = build_newspaper_mh_mets(g, "testpid", "Tape")

    assert "Disk" in mets
    assert "Tape" in mets
    assert mets.count("Disk") == 27
    assert mets.count("Tape") == 4
    assert mets

@freeze_time("2024-02-20")
def test_build_basic_mets(basic_ttl_graph, basic_mets_xml):
    g = parse_graph(basic_ttl_graph, "ttl")

    mets = build_basic_mh_mets(g, "testpid", "Disk")

    assert "Disk" in mets
    assert not "Tape" in mets
    assert mets
    assert sorted("".join(mets.split())) == sorted("".join(basic_mets_xml.split()))



@freeze_time("2024-02-20")
def test_build_bibliographic_mets(bibliographic_ttl_graph):
    g = parse_graph(bibliographic_ttl_graph, "ttl")

    mets = build_bibliographic_mh_mets(g, "testpid", "Disk")

    assert "Disk" in mets
    assert not "Tape" in mets
    assert mets