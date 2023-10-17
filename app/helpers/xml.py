import metsrw
import rdflib
from lxml import etree
from rdflib.term import Node

from app.helpers.graph import get_cp_id_from_graph, get_representations
from app.helpers.mappers import creator_mapper, geometry_mapper, local_id_mapper
from app.helpers.transformers import dimension_transform, language_code_transform

MH_VERSION = "22.1"

NSMAP = {
    "mhs": f"https://zeticon.mediahaven.com/metadata/{MH_VERSION}/mhs/",
    "mh": f"https://zeticon.mediahaven.com/metadata/{MH_VERSION}/mh/",
}

MAPPING: dict = {
    "http://purl.org/dc/terms/title": {
        "targets": [
            "mhs:Descriptive.mh:Title",
            "mhs:Dynamic.dc_title",
            "mhs:Dynamic.dc_titles.registratie[]",
        ]
    },
    "http://purl.org/dc/terms/publisher": {
        "targets": ["mhs:Dynamic.dc_publisher.Uitgever[]"]
    },
    "http://purl.org/dc/terms/abstract": {"targets": ["mhs:Dynamic.dc_description"]},
    "http://purl.org/dc/terms/alternative": {
        "targets": ["mhs:Dynamic.dc_titles.alternatief[]"]
    },
    "http://purl.org/dc/terms/contributor": {
        "targets": ["mhs:Dynamic.dc_contributors.Bijdrager[]"]
    },
    "http://purl.org/dc/terms/created": {"targets": ["mhs:Dynamic.dcterms_created"]},
    "http://purl.org/dc/terms/creator": {
        "targets": ["mhs:Dynamic.dc_creators.Maker[]"]
    },
    "http://purl.org/dc/terms/description": {
        "targets": [
            "mhs:Dynamic.dc_description_lang",
            "mhs:Descriptive.mh:Description",
        ]
    },
    "http://purl.org/dc/terms/issued": {"targets": ["mhs:Dynamic.dcterms_issued"]},
    "http://purl.org/dc/terms/language": {
        "targets": ["mhs:Dynamic.dc_languages.multiselect[]"],
        "transformer": language_code_transform,
    },
    "http://purl.org/dc/terms/license": {
        "targets": ["mhs:Dynamic.dc_rights_licenses.multiselect[]"]
    },
    "http://purl.org/dc/terms/rights": {"targets": ["mhs:Dynamic.dc_rights_comment"]},
    "http://purl.org/dc/terms/rightsHolder": {
        "targets": ["mhs:Dynamic.dc_rights_rightsHolders.Licentiehouder[]"]
    },
    "http://purl.org/dc/terms/spatial": {
        "targets": ["mhs:Dynamic.dc_coverages.ruimte[]"]
    },
    "http://purl.org/dc/terms/subject": {
        "targets": ["mhs:Dynamic.dc_subjects.Trefwoord[]"]
    },
    "http://purl.org/dc/terms/temporal": {
        "targets": ["mhs:Dynamic.dc_coverages.tijd[]"]
    },
    "http://www.loc.gov/premis/v3#fixity": {"targets": ["mhs:Dynamic.md5_viaa"]},
    "https://schema.org/height": {
        "targets": ["mhs:Dynamic.dimensions.height_in_mm"],
        "transformer": dimension_transform,
    },
    "https://schema.org/width": {
        "targets": ["mhs:Dynamic.dimensions.width_in_mm"],
        "transformer": dimension_transform,
    },
    "https://schema.org/depth": {
        "targets": ["mhs:Dynamic.dimensions.depth_in_mm"],
        "transformer": dimension_transform,
    },
    "https://schema.org/artForm": {
        "targets": ["mhs:Dynamic.artform"],
    },
    "https://schema.org/artMedium": {
        "targets": ["mhs:Dynamic.artmedium"],
    },
    "https://schema.org/creator": {
        "mapping_strategy": creator_mapper,
    },
    "http://www.loc.gov/premis/rdf/v3/identifier": {
        "mapping_strategy": local_id_mapper,
    },
    "http://www.w3id.org/omg#hasGeometry": {
        "mapping_strategy": geometry_mapper,
    },
}


def lxmlns(ns: str) -> str:
    """Return namespace"""
    return f"{{{NSMAP[ns]}}}"


def qname_text(ns: str, local_name: str) -> str:
    if ns == "mets":
        return f'{{{"http://www.loc.gov/METS/"}}}{local_name}'
    return f"{lxmlns(ns)}{local_name}"


def build_mh_mets(g: rdflib.Graph, pid: str, archive_location: str) -> str:
    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )
    mets = metsrw.METSDocument()

    mets.agents.append(metsrw.Agent("CUSTODIAN", type="ORGANIZATION", name="meemoo"))

    root_folder = metsrw.FSEntry(use="Original", type="MaterialArtwork")

    mets_fs = metsrw.FSEntry(
        fileid="FILEID-MATERIALARTWORK-METS",
        use="Disk",
        path="mets.xml",
        type="Representation",
        label="Original",
        file_uuid="FILEID-MATERIALARTWORK-METS",
    )
    mets_med = metsrw.FSEntry(type="Media")
    mets_med.add_dmdsec(
        build_minimal_sidecar(f"{pid}_mets"),
        "OTHER",
        **{
            "othermdtype": "mhs:Sidecar",
            "id": f"DMDID-MATERIALARTWORK-METS",
        },
    )
    mets_med.add_child(mets_fs)
    root_folder.add_child(mets_med)
    root_folder.add_dmdsec(
        build_mh_sidecar(g, [ie], pid),
        "OTHER",
        **{
            "othermdtype": "mhs:Sidecar",
            "id": f"DMDID-MATERIALARTWORK",
        },
    )

    representations = get_representations(g)

    for representation in representations:
        representation_index = representation.label.split("_")[1]
        for file_index, file in enumerate(representation.files):
            representation_media = metsrw.FSEntry(type="Media")
            representation_media.add_dmdsec(
                build_mh_sidecar(
                    g,
                    [representation.node, file.node],
                    f"{pid}_{representation_index}_{file_index}",
                ),
                "OTHER",
                **{
                    "othermdtype": "mhs:Sidecar",
                    "id": f"DMDID-MATERIALARTWORK-REPRESENTATION-{representation_index}-{file_index}",
                },
            )
            file_representation = metsrw.FSEntry(
                fileid=f"FILEID-MATERIALARTWORK-REPRESENTATION-{representation_index}-{file_index}",
                use=archive_location,
                path=f"{representation.label}/{file.filename}",
                type="Representation",
                label="Original",
                file_uuid=f"FILEID-MATERIALARTWORK-REPRESENTATION-{representation_index}-{file_index}",
                checksumtype="MD5",
                checksum=file.fixity,
            )
            representation_media.add_child(file_representation)
            root_folder.add_child(representation_media)

    mets.append_file(root_folder)

    m = mets.serialize(normative_structmap=False)

    xml = etree.tostring(
        m, xml_declaration=True, encoding="UTF-8", pretty_print=True
    ).decode()

    return xml


def build_minimal_sidecar(external_id: str) -> str:
    root = etree.Element(
        etree.QName(NSMAP["mhs"], "Sidecar"),
        nsmap=NSMAP,
        attrib={"version": MH_VERSION},
    )

    administrative_node = etree.Element(
        etree.QName(NSMAP["mhs"], "Administrative"), nsmap=NSMAP
    )
    id_node = etree.Element(etree.QName(NSMAP["mh"], "ExternalId"), nsmap=NSMAP)

    descriptive_node = etree.Element(
        etree.QName(NSMAP["mhs"], "Descriptive"), nsmap=NSMAP
    )
    title_node = etree.Element(etree.QName(NSMAP["mh"], "Title"), nsmap=NSMAP)

    root.append(administrative_node)
    root.append(descriptive_node)
    administrative_node.append(id_node)
    descriptive_node.append(title_node)
    id_node.text = external_id
    title_node.text = external_id

    xml = etree.tostring(root, pretty_print=True).decode()

    return xml


def build_mh_sidecar(
    g: rdflib.Graph,
    subjects,
    pid: str,
    dynamic_tags: dict[str, str] = {},
) -> str:
    """
    Builds a MH 2.0 sidecar based on metadata from a graph
    """
    root = etree.Element(
        etree.QName(NSMAP["mhs"], "Sidecar"),
        nsmap=NSMAP,
        attrib={"version": MH_VERSION},
    )

    # Add external ID
    administrative_node = etree.Element(
        etree.QName(NSMAP["mhs"], "Administrative"), nsmap=NSMAP
    )
    id_node = etree.Element(etree.QName(NSMAP["mh"], "ExternalId"), nsmap=NSMAP)
    root.append(administrative_node)
    administrative_node.append(id_node)
    id_node.text = pid

    # Add mappable fields to the XML
    for subject in subjects:
        for predicate in MAPPING.keys():
            map = {}
            if MAPPING[predicate].get("mapping_strategy"):
                map = MAPPING[predicate]["mapping_strategy"](
                    g, g.objects(predicate=rdflib.URIRef(predicate), subject=subject)
                )
            else:
                for key in MAPPING[predicate]["targets"]:
                    for obj in g.objects(
                        predicate=rdflib.URIRef(predicate), subject=subject
                    ):
                        if MAPPING[predicate].get("transformer"):
                            if type(obj) == rdflib.URIRef:
                                result = g.predicate_objects(subject=obj)
                                obj = MAPPING[predicate]["transformer"](result)
                                obj = rdflib.Literal(obj)
                            else:
                                obj = rdflib.Literal(
                                    MAPPING[predicate]["transformer"](obj)
                                )
                        if (
                            type(obj) == rdflib.Literal
                            and obj.language
                            and obj.language != "nl"
                        ):
                            # Skip non dutch fields.
                            continue
                        map[key] = [*map.get(key, []), str(obj)]
            add_fields_to_xml(root, map)

    # Add some extra dynamic metadata
    # Create Dynamic node if needed
    dynamic_tag = root.find("mhs:Dynamic", namespaces=NSMAP)
    if dynamic_tag is None:
        dynamic_tag = etree.Element(etree.QName(NSMAP["mhs"], "Dynamic"), nsmap=NSMAP)
        root.append(dynamic_tag)

    # Add PID
    pid_tag = etree.Element("PID")
    dynamic_tag.append(pid_tag)
    pid_tag.text = pid.split("_")[0]

    # Add CP-id to the XML
    cp_tag = etree.Element("CP_id")
    dynamic_tag.append(cp_tag)
    cp_tag.text = get_cp_id_from_graph(g)

    for key, value in dynamic_tags.items():
        key_tag = etree.Element(key)
        dynamic_tag.append(key_tag)
        key_tag.text = value

    # Add sp_name/workflow
    sp_tag = etree.Element("sp_name")
    dynamic_tag.append(sp_tag)
    sp_tag.text = "sipin"

    xml = etree.tostring(root, pretty_print=True).decode()

    return xml


def add_fields_to_xml(root, fields: dict[str, str]):
    for key, values in fields.items():
        for value in values:
            splitted = key.split(".")
            xml_tag = root
            for tag in splitted:
                if (
                    not tag.endswith("[]")
                    and xml_tag.find(tag, namespaces=NSMAP) is not None
                ):
                    xml_tag = xml_tag.find(tag, namespaces=NSMAP)
                    continue
                tag = tag.removesuffix("[]")

                prefix = tag.rpartition(":")[0]
                tag = tag.rpartition(":")[2]
                new = etree.Element(etree.QName(NSMAP.get(prefix), tag), nsmap=NSMAP)

                xml_tag.append(new)
                xml_tag = new
            xml_tag.text = value
