import rdflib
from lxml import etree
from app.helpers.graph import get_cp_id_from_graph


def build_mh_mets():
    # Build MH mets to be used in the MH 2.0 complex, coming in v0.2
    pass


def build_mh_sidecar(g: rdflib.Graph) -> str:
    """
    Builds a MH 2.0 sidecar based on metadata from a graph
    """
    NSMAP = {
        "mhs": "https://zeticon.mediahaven.com/metadata/22.1/mhs/",
        "mh": "https://zeticon.mediahaven.com/metadata/22.1/mh/",
    }

    mapping_dict = {
        "http://purl.org/dc/terms/publisher": "Dynamic.dc_publisher.Uitgever[]",
        "http://purl.org/dc/terms/abstract": "Dynamic.dc_description",
        "http://purl.org/dc/terms/alternative": "Dynamic.dc_titles.alternatief[]",
        "http://purl.org/dc/terms/contributor": "Dynamic.dc_contributors.Bijdrager[]",
        "http://purl.org/dc/terms/created": "Dynamic.dcterms_created",
        "http://purl.org/dc/terms/creator": "Dynamic.dc_creators.Maker[]",
        "http://purl.org/dc/terms/description": "Dynamic.dc_description_lang",
        "http://purl.org/dc/terms/issued": "Dynamic.dcterms_issued",
        "http://purl.org/dc/terms/language": "Dynamic.dc_languages.multiselect[]",
        "http://purl.org/dc/terms/license": "Dynamic.dc_rights_licenses.multiselect[]",
        "http://purl.org/dc/terms/rights": "Dynamic.dc_rights_comment",
        "http://purl.org/dc/terms/rightsHolder": "Dynamic.dc_rights_rightsHolders",
        "http://purl.org/dc/terms/spatial": "Dynamic.dc_coverages.ruimte",
        "http://purl.org/dc/terms/subject": "Dynamic.dc_subjects.Trefwoord[]",
        "http://purl.org/dc/terms/temporal": "Dynamic.dc_coverages.tijd",
        "http://purl.org/dc/terms/title": "Dynamic.dc_title",
        "http://purl.org/dc/terms/title": "Dynamic.dc_titles.registratie",
        "http://www.loc.gov/premis/v3#fixity": "Dynamic.md5_viaa",
    }

    root = etree.Element(
        etree.QName(NSMAP["mhs"], "Sidecar"), nsmap=NSMAP, attrib={"version": "22.1"}
    )

    # Add mappable fields to the XML
    for predicate in mapping_dict.keys():
        for obj in g.objects(predicate=rdflib.URIRef(predicate)):
            if obj.language and obj.language != "nl":
                # Skip non dutch fields.
                continue
            key = mapping_dict[predicate]
            splitted = key.split(".")
            xml_tag = root
            for i in range(len(splitted)):
                if i == 0:
                    if xml_tag.find(f"mhs:{splitted[i]}", namespaces=NSMAP) is not None:
                        xml_tag = xml_tag.find(f"mhs:{splitted[i]}", namespaces=NSMAP)
                        continue
                    new = etree.Element(
                        etree.QName(NSMAP["mhs"], splitted[i]), nsmap=NSMAP
                    )
                else:
                    if (
                        not splitted[i].endswith("[]")
                        and xml_tag.find(splitted[i]) is not None
                    ):
                        xml_tag = xml_tag.find(splitted[i])
                        continue
                    if splitted[i].endswith("[]"):
                        splitted[i] = splitted[i][:-2]

                    new = etree.Element(splitted[i])

                xml_tag.append(new)
                xml_tag = new
            xml_tag.text = obj

    # Add CP-id to the XML
    cp_tag = etree.Element("CP_id")
    root.find("mhs:Dynamic", namespaces=NSMAP).append(cp_tag)
    cp_tag.text = get_cp_id_from_graph(g)

    xml = etree.tostring(root, pretty_print=True).decode()

    return xml
