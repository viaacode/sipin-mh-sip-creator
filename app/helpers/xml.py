import rdflib
import metsrw
from lxml import etree

from app.helpers.graph import (
    get_cp_id_from_graph,
    get_local_ids_from_graph,
    get_representations,
)

from app.helpers.transformers import (
    dimension_transform,
    language_code_transform,
    creator_transform,
)

MH_VERSION = "22.1"

NSMAP = {
    "mhs": f"https://zeticon.mediahaven.com/metadata/{MH_VERSION}/mhs/",
    "mh": f"https://zeticon.mediahaven.com/metadata/{MH_VERSION}/mh/",
}

MAPPING = {
    "http://purl.org/dc/terms/title": {
        "targets": [
            "Descriptive.mh:Title",
            "Dynamic.dc_title",
            "Dynamic.dc_titles.registratie[]",
        ]
    },
    "http://purl.org/dc/terms/publisher": {
        "targets": ["Dynamic.dc_publisher.Uitgever[]"]
    },
    "http://purl.org/dc/terms/abstract": {"targets": ["Dynamic.dc_description"]},
    "http://purl.org/dc/terms/alternative": {
        "targets": ["Dynamic.dc_titles.alternatief[]"]
    },
    "http://purl.org/dc/terms/contributor": {
        "targets": ["Dynamic.dc_contributors.Bijdrager[]"]
    },
    "http://purl.org/dc/terms/created": {"targets": ["Dynamic.dcterms_created"]},
    "http://purl.org/dc/terms/creator": {"targets": ["Dynamic.dc_creators.Maker[]"]},
    "http://purl.org/dc/terms/description": {
        "targets": [
            "Dynamic.dc_description_lang",
            "Descriptive.mh:Description",
        ]
    },
    "http://purl.org/dc/terms/issued": {"targets": ["Dynamic.dcterms_issued"]},
    "http://purl.org/dc/terms/language": {
        "targets": ["Dynamic.dc_languages.multiselect[]"],
        "transformer": language_code_transform,
    },
    "http://purl.org/dc/terms/license": {
        "targets": ["Dynamic.dc_rights_licenses.multiselect[]"]
    },
    "http://purl.org/dc/terms/rights": {"targets": ["Dynamic.dc_rights_comment"]},
    "http://purl.org/dc/terms/rightsHolder": {
        "targets": ["Dynamic.dc_rights_rightsHolders.Licentiehouder[]"]
    },
    "http://purl.org/dc/terms/spatial": {"targets": ["Dynamic.dc_coverages.ruimte[]"]},
    "http://purl.org/dc/terms/subject": {
        "targets": ["Dynamic.dc_subjects.Trefwoord[]"]
    },
    "http://purl.org/dc/terms/temporal": {"targets": ["Dynamic.dc_coverages.tijd[]"]},
    "http://www.loc.gov/premis/v3#fixity": {"targets": ["Dynamic.md5_viaa"]},
    "https://schema.org/height": {
        "targets": ["Dynamic.height"],
        "transformer": dimension_transform,
    },
    "https://schema.org/width": {
        "targets": ["Dynamic.width"],
        "transformer": dimension_transform,
    },
    "https://schema.org/depth": {
        "targets": ["Dynamic.depth"],
        "transformer": dimension_transform,
    },
    "https://schema.org/artForm": {
        "targets": ["Dynamic.artform"],
    },
    "https://schema.org/artMedium": {
        "targets": ["Dynamic.artmedium"],
    },
    "https://schema.org/creator": {
        "targets": ["Dynamic.dc_creators.Maker[]"],
        "transformer": creator_transform,
    },
}


def lxmlns(ns: str) -> str:
    """Return namespace"""
    return f"{{{NSMAP[ns]}}}"


def qname_text(ns: str, local_name: str) -> str:
    if ns == "mets":
        return f'{{{"http://www.loc.gov/METS/"}}}{local_name}'
    return f"{lxmlns(ns)}{local_name}"


def build_mh_mets(g: rdflib.Graph, pid: str) -> str:
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
        build_mh_sidecar(g, ie, pid),
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
                    representation.node,
                    f"{pid}_{representation_index}_{file_index}",
                    is_ie=False,
                ),
                "OTHER",
                **{
                    "othermdtype": "mhs:Sidecar",
                    "id": f"DMDID-MATERIALARTWORK-REPRESENTATION-{representation_index}-{file_index}",
                },
            )
            file_representation = metsrw.FSEntry(
                fileid=f"FILEID-MATERIALARTWORK-REPRESENTATION-{representation_index}-{file_index}",
                use="Disk",
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
    subject,
    pid: str,
    dynamic_tags: dict[str, str] = {},
    is_ie: bool = True,
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
    for predicate in MAPPING.keys():
        for key in MAPPING[predicate]["targets"]:
            for obj in g.objects(predicate=rdflib.URIRef(predicate), subject=subject):
                if MAPPING[predicate].get("transformer"):
                    if type(obj) == rdflib.URIRef:
                        result = g.predicate_objects(subject=obj)
                        obj = MAPPING[predicate]["transformer"](g, result)
                        if type(obj) == str:
                            obj = rdflib.Literal(obj)
                        if type(obj) == tuple:
                            key = obj[0]
                            obj = rdflib.Literal(obj[1])
                    else:
                        obj = rdflib.Literal(MAPPING[predicate]["transformer"](obj))
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
    # Create Dynamic node if needed
    dynamic_tag = root.find("mhs:Dynamic", namespaces=NSMAP)
    if not dynamic_tag:
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

    if is_ie:
        # Add local id's to the XML
        local_ids = get_local_ids_from_graph(g)

        # TODO
        if len(list(local_ids)) == 1:
            main_local_id = local_ids.pop(
                "MEEMOO-LOCAL-ID", local_ids[list(local_ids)[0]]
            )
        else:
            main_local_id = local_ids.pop("MEEMOO-LOCAL-ID", "")

        if main_local_id:
            local_id_tag = etree.Element("dc_identifier_localid")
            dynamic_tag.append(local_id_tag)
            local_id_tag.text = main_local_id

        if local_ids:
            local_ids_tag = etree.Element("dc_identifier_localids")
            dynamic_tag.append(local_ids_tag)
            for id_type, id in local_ids.items():
                id_tag = etree.Element(id_type)
                local_ids_tag.append(id_tag)
                id_tag.text = id

    for key in dynamic_tags:
        key_tag = etree.Element(key)
        dynamic_tag.append(key_tag)
        key_tag.text = dynamic_tags[key]

    # Add sp_name/workflow
    sp_tag = etree.Element("sp_name")
    dynamic_tag.append(sp_tag)
    sp_tag.text = "sipin"

    xml = etree.tostring(root, pretty_print=True).decode()

    return xml
