CREATE DATABASE IF NOT EXISTS destiny;

CREATE TABLE IF NOT EXISTS destiny.data_sources
(
    source_id String,
    name String,
    category LowCardinality(String),
    url String,
    license String,
    access_status LowCardinality(String),
    notes String,
    retrieved_at Nullable(DateTime)
)
ENGINE = ReplacingMergeTree
ORDER BY source_id;

CREATE TABLE IF NOT EXISTS destiny.five_elements
(
    element String,
    generating String,
    controlling String,
    direction String,
    season String,
    source_id String,
    rule_version String
)
ENGINE = ReplacingMergeTree
ORDER BY element;

CREATE TABLE IF NOT EXISTS destiny.heavenly_stems
(
    ordinal UInt8,
    name String,
    polarity LowCardinality(String),
    element LowCardinality(String),
    direction String,
    source_id String,
    rule_version String
)
ENGINE = ReplacingMergeTree
ORDER BY ordinal;

CREATE TABLE IF NOT EXISTS destiny.earthly_branches
(
    ordinal UInt8,
    name String,
    polarity LowCardinality(String),
    element LowCardinality(String),
    zodiac String,
    lunar_month UInt8,
    hour_start UInt8,
    direction String,
    hidden_stems Array(String),
    source_id String,
    rule_version String
)
ENGINE = ReplacingMergeTree
ORDER BY ordinal;

CREATE TABLE IF NOT EXISTS destiny.trigrams
(
    earlier_heaven_ordinal UInt8,
    name String,
    symbol String,
    binary_code FixedString(3),
    element LowCardinality(String),
    direction_later_heaven String,
    family_role String,
    source_id String,
    rule_version String
)
ENGINE = ReplacingMergeTree
ORDER BY earlier_heaven_ordinal;

CREATE TABLE IF NOT EXISTS destiny.hexagrams
(
    king_wen_ordinal UInt8,
    name String,
    symbol String,
    unicode_codepoint String,
    source_id String,
    rule_version String
)
ENGINE = ReplacingMergeTree
ORDER BY king_wen_ordinal;

CREATE TABLE IF NOT EXISTS destiny.solar_terms
(
    ordinal UInt8,
    name String,
    solar_longitude UInt16,
    season LowCardinality(String),
    source_id String,
    rule_version String
)
ENGINE = ReplacingMergeTree
ORDER BY ordinal;

CREATE TABLE IF NOT EXISTS destiny.sexagenary_cycle
(
    ordinal UInt8,
    name String,
    stem String,
    branch String,
    nayin String,
    source_id String,
    rule_version String
)
ENGINE = ReplacingMergeTree
ORDER BY ordinal;

CREATE TABLE IF NOT EXISTS destiny.rule_definitions
(
    rule_id String,
    system LowCardinality(String),
    school String,
    version String,
    title String,
    definition String,
    source_id String,
    review_status LowCardinality(String),
    valid_from DateTime,
    valid_to Nullable(DateTime)
)
ENGINE = ReplacingMergeTree(valid_from)
ORDER BY (system, rule_id, version);

CREATE TABLE IF NOT EXISTS destiny.knowledge_passages
(
    passage_id String,
    work_title String,
    edition String,
    chapter String,
    passage_order UInt32,
    original_text String,
    annotation String,
    source_id String,
    license String,
    review_status LowCardinality(String),
    ingested_at DateTime
)
ENGINE = ReplacingMergeTree(ingested_at)
ORDER BY (work_title, edition, chapter, passage_order);

CREATE TABLE IF NOT EXISTS destiny.validation_cases
(
    case_id String,
    system LowCardinality(String),
    school String,
    input_json String,
    expected_json String,
    source_id String,
    expert_status LowCardinality(String),
    rule_version String,
    updated_at DateTime
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (system, case_id);

CREATE TABLE IF NOT EXISTS destiny.geo_features
(
    feature_id String,
    feature_type LowCardinality(String),
    name String,
    longitude Float64,
    latitude Float64,
    elevation_m Nullable(Float32),
    geometry_wkt String,
    properties_json String,
    observed_at Nullable(DateTime),
    source_id String,
    license String
)
ENGINE = MergeTree
ORDER BY (feature_type, feature_id);

CREATE TABLE IF NOT EXISTS destiny.user_inputs
(
    tenant_id String,
    case_id String,
    input_type LowCardinality(String),
    payload_encrypted String,
    consent_version String,
    created_at DateTime,
    expires_at Nullable(DateTime)
)
ENGINE = MergeTree
ORDER BY (tenant_id, case_id, created_at);

CREATE TABLE IF NOT EXISTS destiny.fengshui_mountains
(
    ordinal UInt8,
    name String,
    center_degree Float32,
    start_degree Float32,
    end_degree Float32,
    category LowCardinality(String),
    trigram String,
    element LowCardinality(String),
    direction String,
    source_id String,
    rule_version String
)
ENGINE = ReplacingMergeTree
ORDER BY ordinal;

CREATE TABLE IF NOT EXISTS destiny.luoshu_palaces
(
    palace_number UInt8,
    name String,
    trigram String,
    direction String,
    element LowCardinality(String),
    family_role String,
    source_id String,
    rule_version String
)
ENGINE = ReplacingMergeTree
ORDER BY palace_number;

CREATE TABLE IF NOT EXISTS destiny.fengshui_properties
(
    tenant_id String,
    property_id String,
    name String,
    longitude Nullable(Float64),
    latitude Nullable(Float64),
    construction_year Nullable(UInt16),
    occupied_on Nullable(Date),
    facing_degree Nullable(Float32),
    magnetic_declination Nullable(Float32),
    measurement_method LowCardinality(String),
    measurement_uncertainty Nullable(Float32),
    encrypted_address String,
    created_at DateTime,
    updated_at DateTime
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (tenant_id, property_id);

CREATE TABLE IF NOT EXISTS destiny.floorplan_features
(
    tenant_id String,
    property_id String,
    floor_id String,
    feature_id String,
    feature_type LowCardinality(String),
    label String,
    geometry_json String,
    orientation_degree Nullable(Float32),
    properties_json String,
    created_at DateTime
)
ENGINE = MergeTree
ORDER BY (tenant_id, property_id, floor_id, feature_id);

CREATE TABLE IF NOT EXISTS destiny.fengshui_assessments
(
    tenant_id String,
    assessment_id String,
    property_id String,
    school LowCardinality(String),
    rule_version String,
    input_json String,
    calculation_json String,
    conclusion_json String,
    review_status LowCardinality(String),
    calculated_at DateTime
)
ENGINE = ReplacingMergeTree(calculated_at)
ORDER BY (tenant_id, assessment_id);

CREATE TABLE IF NOT EXISTS destiny.corpus_documents
(
    run_id String,
    document_id String,
    source_id LowCardinality(String),
    title String,
    category_id LowCardinality(String),
    category_name LowCardinality(String),
    source_url String,
    fetched_from String,
    cache_status LowCardinality(String),
    usage_scope LowCardinality(String),
    parser_version String,
    content_sha256 FixedString(64),
    character_count UInt64,
    byte_count UInt64,
    subcontent_count UInt32,
    available_subcontent_count UInt32,
    unavailable_subcontent_ids Array(String),
    fetched_at Nullable(DateTime),
    ingested_at DateTime,
    license_name String DEFAULT '',
    license_url String DEFAULT '',
    attribution_url String DEFAULT '',
    language LowCardinality(String) DEFAULT 'zh'
)
ENGINE = ReplacingMergeTree(ingested_at)
ORDER BY (run_id, document_id);

ALTER TABLE destiny.corpus_documents ADD COLUMN IF NOT EXISTS license_name String DEFAULT '';
ALTER TABLE destiny.corpus_documents ADD COLUMN IF NOT EXISTS license_url String DEFAULT '';
ALTER TABLE destiny.corpus_documents ADD COLUMN IF NOT EXISTS attribution_url String DEFAULT '';
ALTER TABLE destiny.corpus_documents ADD COLUMN IF NOT EXISTS language LowCardinality(String) DEFAULT 'zh';

CREATE TABLE IF NOT EXISTS destiny.corpus_chunks
(
    run_id String,
    chunk_id String,
    document_id String,
    source_id LowCardinality(String),
    title String,
    category_id LowCardinality(String),
    chunk_index UInt32,
    char_start UInt64,
    char_end UInt64,
    character_count UInt32,
    content String,
    content_sha256 FixedString(64),
    document_sha256 FixedString(64),
    usage_scope LowCardinality(String),
    ingested_at DateTime,
    INDEX content_ngram content TYPE ngrambf_v1(3, 256, 2, 0) GRANULARITY 1
)
ENGINE = ReplacingMergeTree(ingested_at)
ORDER BY (run_id, document_id, chunk_index);

CREATE TABLE IF NOT EXISTS destiny.corpus_ingestion_runs
(
    run_id String,
    source_id LowCardinality(String),
    corpus_sha256 FixedString(64),
    document_count UInt32,
    chunk_count UInt64,
    character_count UInt64,
    byte_count UInt64,
    unavailable_document_count UInt32,
    unavailable_subcontent_count UInt32,
    chunk_target_size UInt32,
    chunk_max_size UInt32,
    builder_version String,
    status LowCardinality(String),
    created_at DateTime
)
ENGINE = ReplacingMergeTree(created_at)
ORDER BY run_id;
