import rdflib
from lxml import etree
from app.helpers.graph import (
    get_cp_id_from_graph,
    get_local_ids_from_graph,
    get_representations,
)

MH_VERSION = "22.1"

NSMAP = {
    "mhs": f"https://zeticon.mediahaven.com/metadata/{MH_VERSION}/mhs/",
    "mh": f"https://zeticon.mediahaven.com/metadata/{MH_VERSION}/mh/",
}

MAPPING = {
    "http://purl.org/dc/terms/title": [
        "Descriptive.mh:Title",
        "Dynamic.dc_title",
        "Dynamic.dc_titles.registratie[]",
    ],
    "http://purl.org/dc/terms/publisher": ["Dynamic.dc_publisher.Uitgever[]"],
    "http://purl.org/dc/terms/abstract": [
        "Dynamic.dc_description",
        "Descriptive.mh:Description",
    ],
    "http://purl.org/dc/terms/alternative": ["Dynamic.dc_titles.alternatief[]"],
    "http://purl.org/dc/terms/contributor": ["Dynamic.dc_contributors.Bijdrager[]"],
    "http://purl.org/dc/terms/created": ["Dynamic.dcterms_created"],
    "http://purl.org/dc/terms/creator": ["Dynamic.dc_creators.Maker[]"],
    "http://purl.org/dc/terms/description": ["Dynamic.dc_description_lang"],
    "http://purl.org/dc/terms/issued": ["Dynamic.dcterms_issued"],
    "http://purl.org/dc/terms/language": ["Dynamic.dc_languages.multiselect[]"],
    "http://purl.org/dc/terms/license": ["Dynamic.dc_rights_licenses.multiselect[]"],
    "http://purl.org/dc/terms/rights": ["Dynamic.dc_rights_comment"],
    "http://purl.org/dc/terms/rightsHolder": [
        "Dynamic.dc_rights_rightsHolders.Licentiehouder[]"
    ],
    "http://purl.org/dc/terms/spatial": ["Dynamic.dc_coverages.ruimte"],
    "http://purl.org/dc/terms/subject": ["Dynamic.dc_subjects.Trefwoord[]"],
    "http://purl.org/dc/terms/temporal": ["Dynamic.dc_coverages.tijd"],
    "http://www.loc.gov/premis/v3#fixity": ["Dynamic.md5_viaa"],
}


def build_mh_mets():
    # Build MH mets to be used in the MH 2.0 complex, coming in v0.2
    pass


def build_mh_sidecar(g: rdflib.Graph) -> str:
    """
    Builds a MH 2.0 sidecar based on metadata from a graph
    """
    root = etree.Element(
        etree.QName(NSMAP["mhs"], "Sidecar"),
        nsmap=NSMAP,
        attrib={"version": MH_VERSION},
    )

    # Add mappable fields to the XML
    for predicate in MAPPING.keys():
        for key in MAPPING[predicate]:
            for obj in g.objects(predicate=rdflib.URIRef(predicate)):
                if obj.language and obj.language != "nl":
                    # Skip non dutch fields.
                    continue
                splitted = key.split(".")
                xml_tag = root
                for tag in splitted:
                    if tag in ["Dynamic", "Descriptive"]:
                        if xml_tag.find(f"mhs:{tag}", namespaces=NSMAP) is not None:
                            xml_tag = xml_tag.find(f"mhs:{tag}", namespaces=NSMAP)
                            continue
                        new = etree.Element(etree.QName(NSMAP["mhs"], tag), nsmap=NSMAP)
                    else:
                        if (
                            not tag.endswith("[]")
                            and xml_tag.find(tag, namespaces=NSMAP) is not None
                        ):
                            xml_tag = xml_tag.find(tag)
                            continue
                        if tag.endswith("[]"):
                            tag = tag.removesuffix("[]")
                        if ":" in tag:
                            prefix = tag.split(":")[0]
                            tag = tag.split(":")[1]
                            new = etree.Element(
                                etree.QName(NSMAP[prefix], tag), nsmap=NSMAP
                            )
                        else:
                            new = etree.Element(tag)

                    xml_tag.append(new)
                    xml_tag = new
                xml_tag.text = obj

    # Add some extra dynamic metadata
    dynamic_tag = root.find("mhs:Dynamic", namespaces=NSMAP)

    # Add CP-id to the XML
    cp_tag = etree.Element("CP_id")
    dynamic_tag.append(cp_tag)
    cp_tag.text = get_cp_id_from_graph(g)

    # Add local id's to the XML
    local_ids = get_local_ids_from_graph(g)

    if len(list(local_ids)) == 1:
        main_local_id = local_ids[list(local_ids)[0]]
        main_local_id = local_ids.pop("LOCAL_ID", "")
    else:
        main_local_id = local_ids.pop("LOCAL_ID", "")

    if main_local_id:
        local_id_tag = etree.Element("dc_identifier_localid")
        dynamic_tag.append(local_id_tag)
        local_id_tag.text = main_local_id

    if local_ids:
        local_ids_tag = etree.Element("dc_identifier_localids")
        dynamic_tag.append(local_ids_tag)
        for type, id in local_ids.items():
            tag = etree.Element(type)
            local_ids_tag.append(tag)
            tag.text = id

    # Add the fixity to the XML
    representations = get_representations(g)
    fixity = representations[0].files[0].fixity
    fixity_tag = etree.Element("md5")
    dynamic_tag.append(fixity_tag)
    fixity_tag.text = fixity

    xml = etree.tostring(root, pretty_print=True).decode()

    return xml
