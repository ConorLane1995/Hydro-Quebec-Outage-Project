CREATE EXTENSION IF NOT EXISTS postgis;
ALTER DATABASE outages SET timezone TO 'UTC';

CREATE TABLE versions (
    feed             text            NOT NULL CHECK (feed IN ('bis', 'aip')),
    version_utc      timestamptz     NOT NULL,
    version_raw      text            NOT NULL CHECK (version_raw ~ '^[0-9]{14}$'),
    source           text            NOT NULL DEFAULT 'own' CHECK (source IN ('own', 'hdoyle21')),
    source_path      text            NOT NULL,
    n_records        integer         NOT NULL CHECK (n_records >= 0),
    parsed_at        timestamptz     NOT NULL DEFAULT now(),
    parser_version   text            NOT NULL,
    PRIMARY KEY (feed, version_utc)
);

CREATE TABLE snapshot_records (
    -- identity
    feed             text            NOT NULL,
    version_utc      timestamptz     NOT NULL,
    pos              integer         NOT NULL CHECK (pos >= 0),

    -- raw columns - hold the 10 positional fields as text
    customers_raw    text            NOT NULL,
    start_raw        text            NOT NULL,
    eta_raw          text            NOT NULL,
    type             text            NOT NULL CHECK (type IN ('P', 'I')),
    coords_raw       text            NOT NULL,
    status           text            NOT NULL,
    cat              text            NOT NULL,
    cause            text            NOT NULL,
    muni_id          text            NOT NULL,
    msg_id           text            NOT NULL,

    -- Parsed columns - nullable as they can be absent
    customers        integer         CHECK (customers >= 0),
    start_utc        timestamptz,
    eta_utc          timestamptz,
    geom             geometry(Point, 4326),

    PRIMARY KEY (feed, version_utc, pos),
    FOREIGN KEY (feed, version_utc)
        REFERENCES  versions (feed, version_utc)     
        ON DELETE CASCADE
);

CREATE INDEX snapshot_records_start_raw_idx ON snapshot_records (start_raw);
CREATE INDEX snapshot_records_geom_idx ON snapshot_records USING gist (geom);