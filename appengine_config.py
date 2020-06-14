from google.appengine.ext import vendor
import sys
import os.path

# Add any libraries installed in the "lib" folder.
vendor.add('lib')

subdirs = [
    ('app',),  # /app, python server code
    ('gae_server',),
    # include subdirectories, e.g. dir1/dir2, like this:
    #('dir1', 'dir2')
]

for path_parts in subdirs:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), *path_parts))

def gae_mini_profiler_should_profile_production():
    return os.environ.get('INCLUDE_PROFILER', None) == 'true'

def gae_mini_profiler_should_profile_development():
    return os.environ.get('INCLUDE_PROFILER', None) == 'true'

def webapp_add_wsgi_middleware(app):
    import gae_mini_profiler.profiler
    profiler_app = gae_mini_profiler.profiler.ProfilerWSGIMiddleware(app)
    return profiler_app
