"""ParticipantData: A long-form key-value store for participants.

Example table, focusing on one participant and one project cohort.

|    key    |       value       | survey_id | survey_ordinal |
|-----------|-------------------|-----------|----------------|
| progress  | 100               | Survey_C  |              1 |
| progress  | 1                 | Survey_D  |              2 |
| link      | http://qualtrics1 | Survey_C  |              1 |
| link      | http://qualtrics2 | Survey_D  |              2 |
| condition | control           | Survey_C  |              1 |
| condition | control           | Survey_D  |              2 |
| consent   | true              | Survey_C  |              1 |
| toi_1     | 5                 | Survey_C  |              1 |
| toi_2     | 4                 | Survey_C  |              1 |
| feedback  | it was fun, wooo  | Survey_D  |              2 |

"""
from google.appengine.api import memcache
import collections
import logging

from gae_models import SqlModel, SqlField as Field
import config
import mysql_connection
import util

# A small cached set of participation results pickles to less than 400 bytes.
# Memcache limits values to 1 MB. Conservatively limit how many date ranges we
# store to avoid passing the memory limit. Another good reason to keep this
# low is to avoid lots of cycles looping through keys when invalidating date
# ranges on pd write.
PARTICIPATION_CACHE_MAX_LENGTH = 1000

class ParticipantData(SqlModel):
    """Some datum about a participant.

    Participant id references the Participant table.

    There are no instances of this class, strictly speaking. The select()
    method returns a list of dictionaries, which is good enough.
    """
    table = 'participant_data'

    # Note on defaults: We attempt to be strict; if a field _should_ always
    # have a value in production, it's not allowed to be null, even if some
    # operations or tests could conceivably be run without that field having
    # a value.
    py_table_definition = {
        'table_name': table,
        'fields': [
            #     name,            type,      length, unsigned, null,  default, on_update
            Field('uid',           'varchar', 50,     None,     False, None,    None),
            Field('short_uid',     'varchar', 50,     None,     False, None,    None),
            Field('created',       'datetime',None,   None,     False, SqlModel.sql_current_timestamp, None),
            Field('modified',      'datetime',None,   None,     False, SqlModel.sql_current_timestamp, SqlModel.sql_current_timestamp),
            # 'progress', 'link', 'condition', 'consent' are whitelisted,
            # anything else is a survey response and is kept secret.
            Field('key',           'varchar', 50,     None,     False, None,    None),
            # Potentials values for various keys:
            # progress:     integer 0 to 100
            # link:         url
            # condition:    some short string, e.g. 'control'
            # consent:      'true' or 'false'
            # Otherwise the key represents a data column / question from
            # qualtrics and the value is the participant's response. This is
            # sensitive data!
            Field('value',         'text',    None,   None,     False, None,    None),
            Field('participant_id','varchar', 50,     None,     False, None,    None),
            Field('program_label', 'varchar', 50,     None,     False, None,    None),
            # NULL when using Copilot
            Field('project_id',    'varchar', 50,     None,     True,  SqlModel.sql_null,    None),
            # NULL when using Copilot
            Field('cohort_label',  'varchar', 50,     None,     True,  SqlModel.sql_null,    None),
            Field('project_cohort_id','varchar',50,   None,     False, None,    None),
            Field('code',          'varchar', 50,     None,     False, None,    None),
            Field('survey_id',     'varchar', 50,     None,     True,  SqlModel.sql_null,    None),
            Field('survey_ordinal','tinyint', 3,      True,     True,  SqlModel.sql_null,    None),
            Field('testing',       'bool',    None,   None,     False, 0,       None),
        ],
        'primary_key': ['uid'],
        'indices': [
            # @todo(chris): stress-test the table and optimize indices once the
            # schema is well established.
            {
                'unique': True,
                'name': 'participant-survey-key',
                'fields': ['participant_id', 'survey_id', 'key'],
            },
            {
                'name': 'participant_id',
                'fields': ['participant_id'],
            },
            {
                'name': 'project_cohort-modified',
                'fields': ['project_cohort_id', 'modified'],
            },
        ],
        'engine': 'InnoDB',
        'charset': 'utf8',
    }

    @classmethod
    def get_by_participant(klass, participant_id, project_cohort_id=None):
        """Get whitelisted pd for a participant, optionally scoped by pc."""

        pc_clause = 'AND `project_cohort_id` = %s' if project_cohort_id else ''

        # Only certain types of participant data are readable by anyone without
        # direct access to the database. This keeps participant responses
        # secure.
        query = """
            SELECT    *
            FROM      `participant_data`
            WHERE     `key` IN ('progress', 'link', 'condition', 'ep_assent',
                                'last_login', 'saw_baseline',
                                'saw_demographics', 'saw_validation')
              AND     `participant_id` = %s
              {pc_clause}
        """.format(pc_clause=pc_clause)

        params = [participant_id]
        if project_cohort_id:
            params.append(project_cohort_id)

        with mysql_connection.connect() as sql:
            row_dicts = sql.select_query(query, tuple(params))

        return [klass.row_dict_to_obj(d) for d in row_dicts]

    @classmethod
    def is_progress_downgrade(klass, pd):
        """Progress means the furthest a participant has reached in a given
        survey, so this value should never decrease. Assumes that all progress
        values are integerable strings.
        """
        if pd.key != 'progress' or pd.value == '100':
            return False

        existing_pd = next((pd for pd in ParticipantData.get(
            key='progress',
            participant_id=pd.participant_id,
            survey_id=pd.survey_id,
        )), None)
        if existing_pd and int(existing_pd.value) > int(pd.value):
            return True

        return False

    @classmethod
    def is_valid_progress_value(klass, value):
        # Then `value` should be an integer between 0 and 100 inclusive.
        try:
            integerValue = int(value)
            if integerValue not in range(0, 101):
                logging.info("Progress value out of range.")
                return False
        except ValueError:
            logging.info("Progress value not an integer.")
            return False
        return True

    @classmethod
    def participation(klass, **kwargs):
        """Summarize participation for a single scope, pc or survey.

        This attempts to retrive results from memcache first. It falls back
        on participation_from_sql on cache miss.

        Cache is structured like cache_key: {date_range: result, ...}
        """
        cacheable_kwargs = (
            set(('project_cohort_id', 'start', 'end')),
            set(('survey_id', 'start', 'end')),
        )
        set_keys = set(k for k in kwargs.keys() if kwargs[k] is not None)
        is_cacheable = set_keys in cacheable_kwargs

        if is_cacheable:
            survey_id = kwargs.get('survey_id', None)
            project_cohort_id = kwargs.get('project_cohort_id', None)
            date_key = klass.date_key(kwargs['start'], kwargs['end'])

            # Find any cached data by the relevant entity id.
            cache_key = klass.participation_cache_key(
                survey_id or project_cohort_id)
            cache_value = memcache.get(cache_key) or {}

            # Cache value is results keyed by date range. Choose the right one,
            # if available.
            result = cache_value.get(date_key, None)

            # If we found anything, use it, and skip sql entirely.
            if result:
                return result

        sql_results = klass.participation_from_sql(**kwargs)

        if is_cacheable:
            if len(cache_value) > PARTICIPATION_CACHE_MAX_LENGTH:
                cache_value = klass.truncate_cached(cache_value)
            cache_value[date_key] = sql_results
            memcache.set(cache_key, cache_value)

        return sql_results

    @classmethod
    def participation_by_project_cohort(klass, ids_or_codes, *args, **kwargs):
        """Summarize participation for multiple project cohorts at once.

        This attempts to retrive results from memcache first. It falls back
        on participation_by_project_cohort_from_sql on cache miss.

        Cache is structured like cache_key: {date_range: result, ...}
        """
        results = []
        # Assume we'll have to go to sql for all this data, unless we find it
        # cached.
        ids_for_sql = list(ids_or_codes)  # copy
        cache_data_to_update = {}
        is_cacheable = 'start' in kwargs and 'end' in kwargs

        if is_cacheable:
            date_key = klass.date_key(kwargs['start'], kwargs['end'])
            id_by_cache_key = {
                klass.participation_by_pc_cache_key(id_or_code): id_or_code
                for id_or_code in ids_or_codes
            }

            # Get all the data we're interested in via a batch operation.
            cache_data = memcache.get_multi(id_by_cache_key.keys())

            # Then check each value to see if a matching date range is present.
            for cache_key, id_or_code in id_by_cache_key.items():
                # Find any cached data by the relevant entity id.
                cache_value = cache_data.get(cache_key, {})

                cache_result = cache_value.get(date_key, None)

                if cache_result is None:
                    # We didn't find a result for this id. Queue it for sql and
                    # caching.
                    cache_data_to_update[cache_key] = cache_value
                else:
                    # We found a result for this id. Don't look it up from sql.
                    results += cache_result  # store it for return
                    ids_for_sql.remove(id_or_code)

        # We may have found all relevant data in memcache, in which case this
        # will be empty, and sql is skipped. Anything not found in memcache
        # means ids remain in this list, and we query from sql.
        if ids_for_sql:
            sql_results = klass.participation_by_project_cohort_from_sql(
                ids_for_sql,
                **kwargs
            )
            # Add the sql results to whatever was found in memcache for return.
            # @todo: messes up ordering?
            results += sql_results

            if is_cacheable:
                if len(cache_value) > PARTICIPATION_CACHE_MAX_LENGTH:
                    cache_value = klass.truncate_cached(cache_value)

                # Any data from sql should be cached. Find the right result row,
                # mix it into existing cached data for that id/code, then cache
                # it as memcache.set(cache_key, {date_key: result, ...}), but
                # with a batch operation.
                for id_or_code in ids_for_sql:
                    matching_results = [
                        r for r in sql_results
                        if (id_or_code == r['project_cohort_id'] or
                            id_or_code == r['code'])
                    ]
                    cache_key = klass.participation_by_pc_cache_key(id_or_code)
                    cache_value = cache_data_to_update[cache_key]
                    cache_value[date_key] = matching_results

                memcache.set_multi(cache_data_to_update)

        return results

    @classmethod
    def participation_cache_key(klass, entity_id):
        return u'participation:{}'.format(entity_id)

    @classmethod
    def participation_by_pc_cache_key(klass, entity_id):
        return u'participation_by_pc:{}'.format(entity_id)

    @classmethod
    def date_key(klass, start, end):
        return '{},{}'.format(
            start.strftime(config.iso_datetime_format),
            end.strftime(config.iso_datetime_format),
        )

    @classmethod
    def truncate_cached(klass, cache_value):
        """See comments on PARTICIPATION_CACHE_MAX_LENGTH."""
        # Format is '{ISO datetime},{ISO datetime}', so naive string
        # sort will give us all the oldest date ranges first.
        sorted_keys = sorted(cache_value.keys())

        # Keep only a fraction the max allowed keys to avoid calling this
        # truncation function every time.
        num_to_keep = PARTICIPATION_CACHE_MAX_LENGTH // 10

        # Throw away keys up to the most recent set.
        for k in sorted_keys[:-num_to_keep]:
            del cache_value[k]

        return cache_value

    @classmethod
    def split_date_key(klass, date_key):
        return date_key.split(',')

    @classmethod
    def participation_from_sql(klass, **kwargs):
        """Get counts of participants reaching each marker.

        Args:
            program_label: str applicable program
            cohort_label: str applicable cohort (requires program also)
            project_cohort_id: str applicable pc
            survey_id: str applicable survey
            start: datetime filters for pd modified after this date
            end: datetime filters for pd modified before this date

        Returns: List of dictionaries, each representing a distinct value of
        progress (e.g. 33, 100) and associated counts.
        """
        # All kwargs default to None.
        kwargs = collections.defaultdict(lambda: None, kwargs)

        # Determine and check for a single scope.
        scope_keys = ('program_label', 'project_cohort_id', 'survey_id')
        scope_filters = {k: kwargs[k] for k in scope_keys if kwargs[k]}
        if len(scope_filters) != 1:
            raise Exception("Invalid scope filters: {}".format(scope_filters))
        query_params = scope_filters.values()

        # Optionally include cohort label, which must co-occur with a program.
        if kwargs['cohort_label']:
            if kwargs['program_label']:
                query_params.append(kwargs['cohort_label'])
            else:
                raise Exception("Cannot specify a cohort without a program.")

        # Optionally add a time range. Note that SQL stores and compares
        # datetime strings in a different format.
        query_params += [kwargs[k].strftime(config.sql_datetime_format)
                         for k in ('start', 'end') if kwargs[k]]

        query = """
            SELECT  `value`
            ,       `survey_ordinal`
            ,       COUNT(`uid`) as n
            FROM `participant_data`
            WHERE `key` = 'progress'
              AND `testing` = 0
              AND `{scope_key}` = %s
              {cohort}
              {start}
              {end}
            GROUP BY `survey_ordinal`, `value`
            # Cast value to number before ordering, otherwise string sorting
            # gives you things like: 1, 100, 33.
            # http://stackoverflow.com/questions/5417381/mysql-sort-string-number
            ORDER BY `survey_ordinal`, `value` * 1
        """.format(
            scope_key=scope_filters.keys()[0],
            cohort='AND `cohort_label` = %s' if kwargs['cohort_label'] else '',
            start='AND `modified` >= %s' if kwargs['start'] else '',
            end='AND `modified` < %s' if kwargs['end'] else '',
        )

        with mysql_connection.connect() as sql:
            result = sql.select_query(query, tuple(query_params))
        return result

    @classmethod
    def participation_by_project_cohort_from_sql(
        klass,
        ids_or_codes,
        using_codes=False,
        start=None,
        end=None
    ):
        """Like participation() but for many project cohorts at once.

        Args:
            ids_or_codes: list applicable pc ids or pc codes
            using_codes: bool default False, True if first argument is codes
            start: datetime optional, filters for pd modified after this date
            end: datetime optional, filters for pd modified before this date

        Returns: List of dictionaries, each representing a distinct value of
        progress (e.g. 33, 100) and associated counts.
        """
        if len(ids_or_codes) == 0:
            return []

        query = """
            SELECT  `project_cohort_id`
            ,       MAX(`code`) as code
            ,       `value`
            ,       `survey_ordinal`
            ,       COUNT(`uid`) as n
            FROM `participant_data`
            WHERE `key` = 'progress'
              AND `testing` = 0
              AND `{match_field}` IN({interps})
              {start}
              {end}
            GROUP BY `project_cohort_id`, `survey_ordinal`, `value`
            # Cast value to number before ordering, otherwise string sorting
            # gives you things like: 1, 100, 33.
            # http://stackoverflow.com/questions/5417381/mysql-sort-string-number
            ORDER BY `project_cohort_id`, `survey_ordinal`, `value` * 1
        """.format(
            match_field='code' if using_codes else 'project_cohort_id',
            interps=','.join(['%s'] * len(ids_or_codes)),
            start='AND `modified` >= %s' if start else '',
            end='AND `modified` < %s' if end else '',
        )
        query_params = list(ids_or_codes)
        if start:
            query_params.append(start.strftime(config.sql_datetime_format))
        if end:
            query_params.append(end.strftime(config.sql_datetime_format))

        with mysql_connection.connect() as sql:
            result = sql.select_query(query, tuple(query_params))
        return result

    @classmethod
    def completion_by_cohort(klass, program_label):
        """Get counts of participants having reached progress 100.

        Returns: List of dictionaries, one for each cohort.
        """

        query = """
            SELECT  SUM(`value` = 100) as complete
            ,       `cohort_label`
            ,       `survey_ordinal`
            FROM `participant_data`
            WHERE `key` = 'progress'
              AND `program_label` = %s
              AND `testing` = 0
            GROUP BY `cohort_label`, `survey_ordinal`
            ORDER BY `cohort_label`, `survey_ordinal`
        """

        with mysql_connection.connect() as sql:
            result = sql.select_query(query, (program_label,))
        for row in result:
            # These come back as Decimal objects, want integers.
            row['complete'] = int(row['complete'])
        return result

    @classmethod
    def completion_ids_anonymous(klass, project_cohort_id, start, end):
        """Get list of anonymous participant ids having entered the survey,
        whether or not they finished it.

        Args:
            project_cohort_id: str applicable pc
            start: datetime filters for pd modified after this date
            end: datetime filters for pd modified before this date

        Returns: list of rows with 'participant_id', 'survey_ordinal', and
            'value' (which is progress).
        """
        # Optionally add a time range. Note that SQL stores and compares
        # datetime strings in a different format.
        query = """
            SELECT  `participant_id`
            ,       `survey_ordinal`
            ,       `value`
            FROM `participant_data` pd
            WHERE `key` = 'progress'
              AND `testing` = 0
              AND `project_cohort_id` = %s
              AND `modified` >= %s
              AND `modified` < %s
            ORDER BY `survey_ordinal`, `value`, `participant_id`
        """
        query_params = (
            project_cohort_id,
            start.strftime(config.sql_datetime_format),
            end.strftime(config.sql_datetime_format),
        )

        with mysql_connection.connect() as sql:
            result = sql.select_query(query, tuple(query_params))
        return result

    @classmethod
    def completion_ids(klass, **kwargs):
        """Get list of identifiable names/ids having entered the survey, whether
        or not they finished it.

        Args:
            project_cohort_id: str applicable pc
            survey_id: str applicable survey
            start: datetime filters for pd modified after this date
            end: datetime filters for pd modified before this date

        Returns: List of dictionaries, each with keys 'participant_id' and
        'survey_ordinal'.
        """
        # All kwargs default to None.
        kwargs = collections.defaultdict(lambda: None, kwargs)

        # Determine and check for a single scope.
        scope_keys = ('project_cohort_id', 'survey_id')
        scope_filters = {k: kwargs[k] for k in scope_keys if kwargs[k]}
        if len(scope_filters) != 1:
            raise Exception("Invalid scope filters: {}".format(scope_filters))
        query_params = scope_filters.values()

        # Optionally add a time range. Note that SQL stores and compares
        # datetime strings in a different format.
        query_params += [kwargs[k].strftime(config.sql_datetime_format)
                         for k in ('start', 'end') if kwargs[k]]

        query = """
            SELECT  p.`name` as token
            ,       pd.`value` as percent_progress
            ,       pd.`survey_ordinal` as module
            FROM `participant_data` pd
            JOIN `participant` p
              ON pd.`participant_id` = p.`uid`
            WHERE pd.`key` = 'progress'
              AND pd.`testing` = 0
              AND pd.`{scope_key}` = %s
              {start}
              {end}
            ORDER BY module, percent_progress * 1, token
        """.format(
            scope_key=scope_filters.keys()[0],
            start='AND pd.`modified` > %s' if kwargs['start'] else '',
            end='AND pd.`modified` < %s' if kwargs['end'] else '',
        )

        with mysql_connection.connect() as sql:
            result = sql.select_query(query, tuple(query_params))
        return result

    @classmethod
    def combine_survey_descriptor(self, survey_id, survey_descriptor):
        """The API will accept a "descriptor" that is combined with the survey
        id in the database, which has the effect of allowing multiple sets of
        pd to be recorded per survey. This represents the convention of how
        the id and the descriptor are combined."""
        return '{}:{}'.format(survey_id, survey_descriptor)

    @classmethod
    def separate_survey_descriptor(self, compound_survey_id):
        parts = compound_survey_id.split(':')
        return (parts[0], None) if len(parts) == 1 else parts

    def after_put(self, init_kwargs, *args, **kwargs):
        """Reset memcache for related objects.

        Includes project cohort and survey participation.
        """
        if self.key != 'progress':
            # Caching only relevant to progress.
            return

        keys = (
            self.participation_cache_key(self.survey_id),
            self.participation_cache_key(self.project_cohort_id),
            self.participation_by_pc_cache_key(self.project_cohort_id),
            self.participation_by_pc_cache_key(self.code),
        )
        for k in keys:
            cache_value = memcache.get(k) or {}
            needs_update = False
            for date_key in cache_value.keys():
                start, end = self.split_date_key(date_key)
                created = self.created.strftime(config.iso_datetime_format)
                if created >= start and created < end:
                    needs_update = True
                    del cache_value[date_key]
            if needs_update:
                memcache.set(k, cache_value)
