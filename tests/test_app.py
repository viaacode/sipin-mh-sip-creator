from unittest.mock import patch

from rdflib import Graph

from app.app import EventListener
from app.models.sip import SIP


def test_build_mets_xml_for_profile_bibliographic():
    # Skip __init__ of EventListener
    listener = EventListener.__new__(EventListener)

    metadata_graph = Graph()

    sip = SIP(
        id="id",
        profile="bibliographic",
        batch_id="batch-id",
        format="print",
        content_category="Musical Scores - Print",
    )
    with patch(
        "app.app.xml.build_bibliographic_mh_mets",
        return_value="<mets>mets</mets>",
    ) as mock_build_bibliographic_mh_mets:
        result = listener._build_mh_mets(
            metadata_graph=metadata_graph,
            sip=sip,
            pid="pid",
            archive_location="Disk",
            path="/unzip/path/example.bag.zip",
        )

    assert result == "<mets>mets</mets>"

    mock_build_bibliographic_mh_mets.assert_called_once_with(
        metadata_graph,
        "pid",
        "Disk",
        {
            "dynamic": {
                "batch_id": "batch-id",
                "ContentCategory": "Musical Scores - Print",
            },
            "descriptive": {
                "OriginalFilename": "example.bag.zip",
            },
        },
    )
