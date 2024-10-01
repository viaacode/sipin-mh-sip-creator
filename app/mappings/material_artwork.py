from app.helpers.mappers import (
    creator_mapper,
    geometry_mapper,
    local_id_mapper,
    title_mapper,
    license_mapper,
    instrument_mapper,
)
from app.helpers.transformers import (
    dimension_transform,
    language_code_transform,
    name_transform,
)

NAME: str = "MaterialArtwork"

MAPPING: dict = {
    "http://purl.org/dc/terms/title": {
        "targets": [
            "mhs:Descriptive.mh:Title",
            "mhs:Dynamic.dc_title",
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
            "mhs:Descriptive.mh:Description",
        ]
    },
    "http://purl.org/dc/terms/issued": {"targets": ["mhs:Dynamic.dcterms_issued"]},
    "http://purl.org/dc/terms/language": {
        "targets": ["mhs:Dynamic.dc_languages.multiselect[]"],
        "transformer": language_code_transform,
    },
    "http://purl.org/dc/terms/license": {
        "mapping_strategy": license_mapper,
        "targets": ["mhs:Dynamic.dc_rights_licenses.multiselect[]"],
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
    "https://schema.org/weight": {
        "targets": ["mhs:Dynamic.dimensions.weight_in_kg"],
        "transformer": dimension_transform,
    },
    "https://schema.org/artform": {
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
    "https://data.hetarchief.be/ns/object/light-metering": {
        "targets": ["mhs:Dynamic.light_metering"]
    },
    "https://data.hetarchief.be/ns/object/scan-setup": {
        "targets": ["mhs:Dynamic.scanning.scansetup"]
    },
    "https://data.hetarchief.be/ns/object/height-calibration-object": {
        "targets": [
            "mhs:Dynamic.mesh_geometry.height_calibration_object",
            "mhs:Dynamic.mesh_geometry.height_calibration_object_in_mm",
        ],
        "transformer": dimension_transform,
    },
    "http://id.loc.gov/vocabulary/preservation/eventRelatedAgentRole/exe": {
        "targets": ["mhs:Dynamic.post_processing_software"],
        "transformer": name_transform,
    },
    "https://schema.org/isPartOf": {"mapping_strategy": title_mapper},
    "http://www.loc.gov/premis/rdf/v3/note": {"targets": ["mhs:Dynamic.qc_note"]},
    "https://schema.org/instrument": {"mapping_strategy": instrument_mapper},
    "http://id.loc.gov/vocabulary/preservation/eventRelatedAgentRole/imp": {
        "targets": ["mhs:Dynamic.sp_name"]
    },
}
