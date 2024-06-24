import metsrw
import rdflib
from lxml import etree

from rdflib.term import Node

from app.helpers.graph import get_cp_info_from_graph, get_representations

from app.models.sip import SIP

from app.mappings import material_artwork, newspaper, basic, bibliographic

MH_VERSION = "22.1"

NSMAP = {
    "mhs": f"https://zeticon.mediahaven.com/metadata/{MH_VERSION}/mhs/",
    "mh": f"https://zeticon.mediahaven.com/metadata/{MH_VERSION}/mh/",
}


def build_mh_mets(
    g: rdflib.Graph,
    pid: str,
    archive_location: str,
    additional_metadata: dict[str, dict[str, str]] = {},
) -> str:
    profile = material_artwork
    mapping = profile.MAPPING

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )
    mets = metsrw.METSDocument()

    mets.agents.append(metsrw.Agent("CUSTODIAN", type="ORGANIZATION", name="meemoo"))

    root_folder = metsrw.FSEntry(use="Original", type="MaterialArtwork")

    mets_fs = metsrw.FSEntry(
        fileid=f"FILEID-{profile.NAME.upper()}-METS",
        use="Disk",
        path="mets.xml",
        type="Representation",
        label="Original",
        file_uuid=f"FILEID-{profile.NAME.upper()}-METS",
    )
    mets_med = metsrw.FSEntry(type="Media")
    mets_med.add_dmdsec(
        build_minimal_sidecar(f"{pid}_mets"),
        "OTHER",
        **{
            "othermdtype": "mhs:Sidecar",
            "id": f"DMDID-{profile.NAME.upper()}-METS",
        },
    )
    mets_med.add_child(mets_fs)
    root_folder.add_child(mets_med)
    root_folder.add_dmdsec(
        build_mh_sidecar(mapping, g, [ie], pid, additional_metadata),
        "OTHER",
        **{
            "othermdtype": "mhs:Sidecar",
            "id": f"DMDID-{profile.NAME.upper()}",
        },
    )

    representations = get_representations(g)

    for representation in representations:
        representation_index = representation.label.split("_")[1]
        for file_index, file in enumerate(representation.files):
            representation_media = metsrw.FSEntry(type="Media")
            representation_media.add_dmdsec(
                build_mh_sidecar(
                    mapping,
                    g,
                    [representation.node, file.node, *representation.events],
                    f"{pid}_{representation_index}_{file_index}",
                ),
                "OTHER",
                **{
                    "othermdtype": "mhs:Sidecar",
                    "id": f"DMDID-{profile.NAME.upper()}-REPRESENTATION-{representation_index}-{file_index}",
                },
            )
            file_representation = metsrw.FSEntry(
                fileid=f"FILEID-{profile.NAME.upper()}-REPRESENTATION-{representation_index}-{file_index}",
                use=archive_location,
                path=f"{representation.label}/{file.filename}",
                type="Representation",
                label="Original",
                file_uuid=f"FILEID-{profile.NAME.upper()}-REPRESENTATION-{representation_index}-{file_index}",
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


def build_basic_mh_mets(
    g: rdflib.Graph,
    pid: str,
    archive_location: str,
    additional_metadata: dict[str, dict[str, str]] = {},
) -> str:
    profile = basic
    mapping = profile.MAPPING

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )
    mets = metsrw.METSDocument()

    mets.agents.append(metsrw.Agent("CUSTODIAN", type="ORGANIZATION", name="meemoo"))

    root_folder = metsrw.FSEntry(use="Original", type=profile.NAME)

    mets_fs = metsrw.FSEntry(
        fileid=f"FILEID-{profile.NAME.upper()}-METS",
        use="Disk",
        path="mets.xml",
        type="Representation",
        label="Original",
        file_uuid=f"FILEID-{profile.NAME.upper()}-METS",
    )
    mets_med = metsrw.FSEntry(type="Media")
    mets_med.add_dmdsec(
        build_minimal_sidecar(f"{pid}_mets"),
        "OTHER",
        **{
            "othermdtype": "mhs:Sidecar",
            "id": f"DMDID-{profile.NAME.upper()}-METS",
        },
    )
    mets_med.add_child(mets_fs)
    root_folder.add_child(mets_med)
    root_folder.add_dmdsec(
        build_mh_sidecar(mapping, g, [ie], pid, additional_metadata),
        "OTHER",
        **{
            "othermdtype": "mhs:Sidecar",
            "id": f"DMDID-{profile.NAME.upper()}",
        },
    )

    representations = get_representations(g)

    for representation in representations:
        representation_index = 1
        for file_index, file in enumerate(representation.files):
            representation_media = metsrw.FSEntry(type="Media")
            representation_media.add_dmdsec(
                build_mh_sidecar(
                    mapping,
                    g,
                    [representation.node, file.node, *representation.events],
                    f"{pid}_{representation_index}_{file_index}",
                ),
                "OTHER",
                **{
                    "othermdtype": "mhs:Sidecar",
                    "id": f"DMDID-{profile.NAME.upper()}-REPRESENTATION-{representation_index}-{file_index}",
                },
            )
            file_representation = metsrw.FSEntry(
                fileid=f"FILEID-{profile.NAME.upper()}-REPRESENTATION-{representation_index}-{file_index}",
                use=archive_location,
                path=f"representation_1/{file.filename}",
                type="Representation",
                label="Original",
                file_uuid=f"FILEID-{profile.NAME.upper()}-REPRESENTATION-{representation_index}-{file_index}",
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


def build_newspaper_mh_mets(
    g: rdflib.Graph,
    pid: str,
    archive_location: str,
    additional_metadata: dict[str, dict[str, str]] = {},
) -> str:
    profile = newspaper
    mapping = profile.MAPPING

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )
    mets = metsrw.METSDocument()

    mets.agents.append(metsrw.Agent("CUSTODIAN", type="ORGANIZATION", name="meemoo"))

    root_folder = metsrw.FSEntry(use="Original", type=profile.NAME)

    mets_fs = metsrw.FSEntry(
        fileid=f"FILEID-{profile.NAME.upper()}-METS",
        use="Disk",
        path="mets.xml",
        type="Representation",
        label="Original",
        file_uuid=f"FILEID-{profile.NAME.upper()}-METS",
    )
    mets_med = metsrw.FSEntry(type="Media")
    mets_med.add_dmdsec(
        build_minimal_sidecar(f"{pid}_mets"),
        "OTHER",
        **{
            "othermdtype": "mhs:Sidecar",
            "id": f"DMDID-{profile.NAME.upper()}-METS",
        },
    )
    mets_med.add_child(mets_fs)
    root_folder.add_child(mets_med)
    root_folder.add_dmdsec(
        build_mh_sidecar(mapping, g, [ie], pid, additional_metadata),
        "OTHER",
        **{
            "othermdtype": "mhs:Sidecar",
            "id": f"DMDID-{profile.NAME.upper()}",
        },
    )

    representations = get_representations(g)
    pages: dict[int, list] = {}

    for representation in representations:
        for idx, file in enumerate(representation.files):
            repr_files = pages.get(file.order, [])
            repr_files.append((representation, file))
            pages[file.order] = repr_files

    for page in pages:
        newspaper_page = metsrw.FSEntry(type="NewspaperPage")
        newspaper_page.add_dmdsec(
            build_minimal_sidecar(f"{pid}_{page}"),
            "OTHER",
            **{
                "othermdtype": "mhs:Sidecar",
                "id": f"DMDID-{profile.NAME.upper()}-PAGE-{page}",
            },
        )
        root_folder.add_child(newspaper_page)

        for file_index, repr_file in enumerate(pages[page]):
            representation_media = metsrw.FSEntry(type="Media")
            representation_media.add_dmdsec(
                build_mh_sidecar(
                    mapping,
                    g,
                    [repr_file[0].node, repr_file[1].node, *repr_file[0].events],
                    f"{pid}_{page}_{file_index}",
                ),
                "OTHER",
                **{
                    "othermdtype": "mhs:Sidecar",
                    "id": f"DMDID-{profile.NAME.upper()}-REPRESENTATION-{page}-{file_index}",
                },
            )
            file_representation = metsrw.FSEntry(
                fileid=f"FILEID-{profile.NAME.upper()}-REPRESENTATION-{page}-{file_index}",
                use=archive_location,
                path=f"{repr_file[0].label}/{repr_file[1].filename}",
                type="Representation",
                label="Original",
                file_uuid=f"FILEID-{profile.NAME.upper()}-REPRESENTATION-{page}-{file_index}",
                checksumtype="MD5",
                checksum=repr_file[1].fixity,
            )
            representation_media.add_child(file_representation)
            newspaper_page.add_child(representation_media)

    mets.append_file(root_folder)

    m = mets.serialize(normative_structmap=False)

    xml = etree.tostring(
        m, xml_declaration=True, encoding="UTF-8", pretty_print=True
    ).decode()

    return xml


def build_bibliographic_mh_mets(
    g: rdflib.Graph,
    pid: str,
    archive_location: str,
    additional_metadata: dict[str, dict[str, str]] = {},
) -> str:
    profile = bibliographic
    mapping = profile.MAPPING

    ie = g.value(
        predicate=rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        object=rdflib.URIRef("http://www.loc.gov/premis/rdf/v3/IntellectualEntity"),
    )
    mets = metsrw.METSDocument()

    mets.agents.append(metsrw.Agent("CUSTODIAN", type="ORGANIZATION", name="meemoo"))

    root_folder = metsrw.FSEntry(use="Original", type=profile.NAME)

    mets_fs = metsrw.FSEntry(
        fileid=f"FILEID-{profile.NAME.upper()}-METS",
        use="Disk",
        path="mets.xml",
        type="Representation",
        label="Original",
        file_uuid=f"FILEID-{profile.NAME.upper()}-METS",
    )
    mets_med = metsrw.FSEntry(type="Media")
    mets_med.add_dmdsec(
        build_minimal_sidecar(f"{pid}_mets"),
        "OTHER",
        **{
            "othermdtype": "mhs:Sidecar",
            "id": f"DMDID-{profile.NAME.upper()}-METS",
        },
    )
    mets_med.add_child(mets_fs)
    root_folder.add_child(mets_med)
    root_folder.add_dmdsec(
        build_mh_sidecar(mapping, g, [ie], pid, additional_metadata),
        "OTHER",
        **{
            "othermdtype": "mhs:Sidecar",
            "id": f"DMDID-{profile.NAME.upper()}",
        },
    )

    representations = get_representations(g)
    pages: dict[int, list] = {}

    for representation in representations:
        for idx, file in enumerate(representation.files):
            repr_files = pages.get(file.order, [])
            repr_files.append((representation, file))
            pages[file.order] = repr_files

    for page in pages:
        bibliographic_page = metsrw.FSEntry(type="BibliographicPage")
        bibliographic_page.add_dmdsec(
            build_minimal_sidecar(f"{pid}_{page}"),
            "OTHER",
            **{
                "othermdtype": "mhs:Sidecar",
                "id": f"DMDID-{profile.NAME.upper()}-PAGE-{page}",
            },
        )
        root_folder.add_child(bibliographic_page)

        for file_index, repr_file in enumerate(pages[page]):
            representation_media = metsrw.FSEntry(type="Media")
            representation_media.add_dmdsec(
                build_mh_sidecar(
                    mapping,
                    g,
                    [repr_file[0].node, repr_file[1].node, *repr_file[0].events],
                    f"{pid}_{page}_{file_index}",
                ),
                "OTHER",
                **{
                    "othermdtype": "mhs:Sidecar",
                    "id": f"DMDID-{profile.NAME.upper()}-REPRESENTATION-{page}-{file_index}",
                },
            )
            file_representation = metsrw.FSEntry(
                fileid=f"FILEID-{profile.NAME.upper()}-REPRESENTATION-{page}-{file_index}",
                use=archive_location,
                path=f"{repr_file[0].label}/{repr_file[1].filename}",
                type="Representation",
                label="Original",
                file_uuid=f"FILEID-{profile.NAME.upper()}-REPRESENTATION-{page}-{file_index}",
                checksumtype="MD5",
                checksum=repr_file[1].fixity,
            )
            representation_media.add_child(file_representation)
            bibliographic_page.add_child(representation_media)

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
    mapping: dict,
    g: rdflib.Graph,
    subjects,
    pid: str,
    additional_metadata: dict[str, dict[str, str]] = {},
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
        for predicate in mapping.keys():
            map = {}
            if mapping[predicate].get("mapping_strategy"):
                map = mapping[predicate]["mapping_strategy"](
                    g,
                    subject,
                    g.objects(predicate=rdflib.URIRef(predicate), subject=subject),
                )
            else:
                for key in mapping[predicate]["targets"]:
                    for obj in g.objects(
                        predicate=rdflib.URIRef(predicate), subject=subject
                    ):
                        if mapping[predicate].get("transformer"):
                            if type(obj) == rdflib.URIRef:
                                result = g.predicate_objects(subject=obj)
                                obj = mapping[predicate]["transformer"](result)
                                obj = rdflib.Literal(obj)
                            else:
                                obj = rdflib.Literal(
                                    mapping[predicate]["transformer"](obj)
                                )
                        else:
                            if type(obj) == rdflib.URIRef:
                                obj = g.value(
                                    subject=obj,
                                    predicate=rdflib.URIRef(
                                        "http://www.w3.org/2000/01/rdf-schema#label"
                                    ),
                                    default=g.namespace_manager.compute_qname(obj)[2],
                                )

                                # obj = g.namespace_manager.compute_qname(obj)[2]
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
    cp = get_cp_info_from_graph(g)

    if cp:
        cp_id_tag = etree.Element("CP_id")
        cp_tag = etree.Element("CP")
        dynamic_tag.append(cp_id_tag)
        dynamic_tag.append(cp_tag)
        cp_id_tag.text = cp.id
        cp_tag.text = cp.label

    if additional_metadata.get("dynamic"):
        for key, value in additional_metadata["dynamic"].items():
            if value:
                key_tag = etree.Element(key)
                dynamic_tag.append(key_tag)
                key_tag.text = value

    if additional_metadata.get("descriptive"):
        descriptive_tag = root.find("mhs:Descriptive", namespaces=NSMAP)
        if descriptive_tag is None:
            descriptive_tag = etree.Element(
                etree.QName(NSMAP["mhs"], "Descriptive"), nsmap=NSMAP
            )
            root.append(descriptive_tag)
        for key, value in additional_metadata["descriptive"].items():
            if value:
                key_tag = etree.Element(etree.QName(NSMAP["mh"], key), nsmap=NSMAP)
                descriptive_tag.append(key_tag)
                key_tag.text = value

    # Set ingest_workflow to sipin
    sp_tag = etree.Element("ingest_workflow")
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
