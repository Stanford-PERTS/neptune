"""GraphQL Model config"""

# DatastoreModel and SqlModel have low-ish default limits on result sizes. Since
# we limit access to GraphQL to certain structured cases, it should be safe to
# set very high limits to override those defaults.

default_n = float('inf')
