CREATE TABLE IF NOT EXISTS fake_entities
(
    id           uuid NOT NULL PRIMARY KEY,
    field        varchar(255) NOT NULL,
    created_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL
);
