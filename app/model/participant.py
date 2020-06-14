"""Participant: A person who participates in a survey. SQL-backed."""

import logging

from gae_models import SqlModel, SqlField as Field


class Participant(SqlModel):
    """A person who participates in a survey.

    Linked to ParticipantData via participant_id. Created when a
    participant signs in.

    The only relationship here is to an organization. This defines
    "participant" as a person within an organization. If they transfer to
    another org, they're a new person to us. But within the org, we could
    potentially track them, assuming they use a consistent name/id.

    There are no instances of this class, strictly speaking. The select()
    method returns a list of dictionaries, which is good enough.
    """
    table = 'participant'

    # Note on defaults: We attempt to be strict; if a field _should_ always
    # have a value in production, it's not allowed to be null, even if some
    # operations or tests could conceivably be run without that field having
    # a value.
    py_table_definition = {
        'table_name': table,
        'fields': [
            #     name,            type,      length, unsigned, null,  default, on_update
            Field('uid',           'varchar',  50,    None,     False, None,    None),
            Field('short_uid',     'varchar',  50,    None,     False, None,    None),
            Field('created',       'datetime', None,  None,     False, SqlModel.sql_current_timestamp, None),
            # Long enough for a SHA512 hex digest, may also be plain text.
            # May be a name or an identifier, like a network id or student id.
            Field('name',          'varchar',  128,   None,     True,  SqlModel.sql_null, None),
            Field('organization_id','varchar', 50,    None,     False, None,    None),
        ],
        'primary_key': ['uid'],
        'indices': [
            {
                'unique': True,
                'name': 'name_organization',
                'fields': ['name', 'organization_id'],
            },
        ],
        'engine': 'InnoDB',
        'charset': 'utf8',
    }
