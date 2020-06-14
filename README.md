# neptune

Continuous Improvement Pool Modular Platform

## Setup

1. Clone repository, either via the desktop app or with `git clone https://github.com/PERTS/neptune.git`
2. Navigate to the new `neptune` (`cd neptune`) folder in the terminal.
3. `npm install`
4. Update the silk submodule with `git submodule update --init --recursive`
5. Install other dependencies (see below).
6. `npm run server:mysql` to start up MySQL
7. Create a MySQL user named "neptune", password "neptune", with full permissions.
8. `npm run server` to start up App Server
9. `npm start` will generate the `static` dev build (`grunt build`) and automatically rerun grunt tasks based on file changes.
10. Open the site [http://localhost:8080](http://localhost:8080)

### Dependencies

**Python packages**

`pip install --user pycrypto colour-runner webtest MySQL-python`

**MySQL-python**

As of MacOS El Capitan, for the python runtime of the SDK to connect to MySQL, you must take the extra step of [linking some libraries](https://stackoverflow.com/questions/6383310/python-mysqldb-library-not-loaded-libmysqlclient-18-dylib):

    sudo ln -s /usr/local/mysql/lib/libmysqlclient.18.dylib /usr/local/lib/libmysqlclient.18.dylib

Futhermore, the app connects to MySQL with expectations of a user with permissions on all databases beginning with 'neptune':

    CREATE USER 'neptune'@'localhost' IDENTIFIED BY 'neptune';
    GRANT ALL ON `neptune%`.* TO 'neptune'@'localhost';
    CREATE DATABASE `neptune_test`;


**SASS**

Installed as a ruby gem. On MacOS, ruby should be pre-installed. Then run

    gem install sass

If a grunt build throws the error "You need to have Ruby and Sass installed and in your PATH for this task to work" you may need to install the gem to a specific location and/or export additional folders to your PATH.

The following solved the issue for Chris, noting that he had ownership permission on `/usr/local/bin`:

    gem install -n /usr/local/bin sass

**nvm**

For managing versions of NodeJS. Make sure to read the [notes][1].

    curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.32.1/install.sh | bash

[1]: https://github.com/creationix/nvm "Node Version Manager"

**Java**

Part of the App Engine SDK is based on Java (the datastore emulator). Requires version >= 8. This probably works with JRE, which can be manually downloaded and installed, or let homebrew install JDK:

    brew cask install java

## Codeship Testing

To make use of automated testing locally (`codeship_setup.sh` and
`codeship_test.sh`), some extra tools are required.

## Commands

- Development
    - `npm run server` to start up local App Engine (port 8080)
    - `npm start` to start webpack-dev-server for Neptune/Participate (port 8888)
    - View app at [http://localhost:8888](http://localhost:8888)
- Build
    - `npm build` to build Neptune and Participate
    - `npm run build:neptune` to build only Neptune
    - `npm run build:participate` to build only Participate
- Run Build Locally
    - `npm run build` (or `:neptune` or `:participate`)
    - `npm run server` starts up local App Engine (port 8080)
    - View app at [http://localhost:8080](http://localhost:8080)
- Test
   - `npm test` for the jest CI runner
   - `npm test:cypress` for the cypress GUI runner
   - `npm test:CI` for a single-run of all tests: python, jest, and cypress
   - `./node_modules/.bin/cypress run` for the cypress CI runner


## Database Migration Files

For more details, see the [db-migrate documentation](https://db-migrate.readthedocs.io/en/latest/Getting%20Started/usage/#creating-migrations).

To generate a new migration file for neptune named "foo-bar":

```
node_modules/.bin/db-migrate create foo-bar --config=migrations/triton.json --migrations-dir=migrations/triton --env=test --sql-file
```

Then write SQL commands into the created `.sql` files to describe how to migrate forward/up (the change you're making) and backward/down (how to undo the change you're making).

To move your database forward/up or backward/down in the history of migrations, use this command to see what it would do. If you like the results, remove `--dry-run` and run the command again.

```
node_modules/.bin/db-migrate [up|down] --env test --dry-run
```

If the output of the dry run is not what you expect, it may be because of the `migrations` table in your database, which tracks which migrations have been applied, i.e. at what point in the migration history you are currently.


## Environments

Codeship is our CI service. Simply push your code to a remote branch and Codeship will run a build. Depending on the branch name, Codeship may also deploy your code to one of several different environments, each of which is totally isolated.

|  branch | CI deploys? |     project     |                 URL                 | namespace |
|---------|-------------|-----------------|-------------------------------------|-----------|
| master  | yes         | neptuneplatform | neptune.perts.net                   | [default] |
| dev     | yes         | neptune-dev     | neptune-dev.appspot.com             | [default] |
| dev-foo | yes         | neptune-dev     | dev-foo-dot-neptune-dev.appspot.com | dev-foo   |
| bar     | no          |                 |                                     |           |

The "namespace" column here refers to the string used to namespace each of the various features of the app, although the method to achieve that namespacing similarly varies and has its own jargon associated with it, as described below. In particular, this concept of namespace is not the same as but includes the Datastore "namespace".

### Branch Workflow

* `master` is our production environment.
* `dev` is a staging environment for integration testing and demonstrations.
* `dev-*` branches are sandboxes where developers can experiment with features.

Any other branch is not deployed so is only useful for local testing with the SDK.

### Automatic Environment Switching

Part of our npm postinstall script copies version-controlled git hooks into place. One of those hooks is `post-checkout`, which runs `branch_environment.py` with every `git checkout`. This means that all branch-dependent environment files and variables change automatically as you change branches.

### Codeship

Master deploys to `neptuneplatform`, which any branch starting with 'dev' is deployed to `neptune-dev`.

Codeship runs three scripts:

* `codeship_setup.py`
* `codeship_test.py`
* `codeship_deploy.py`

When debugging a build, remember to specify the version of NodeJS:

`nvm install 6.9.1` or whatever version is in package.json.

### Server Code

App Engine versions, which are different code bases running in parallel on the server. There is always a default version for the project, and the main URL for the project points at the default version. The default version for `neptuneplatform` is `production` and for `neptune-dev` it's `development`. You can address other versions like so: `https://<version>-dot-<project>.appspot.com`. See the summary table above for examples.

### Datastore

Datastore namespaces. When the namespace is unset, which is equivalent to the namespace being an empty string and is also equivalent in the cloud console UI to [default], it has the behavior we normally use. When the namespace is set, all reads and writes to the datastore are segregated into that namespace.

![Using datastore namespaces in the cloud console](https://www.evernote.com/l/AJ5uXNOWNaVCG48ZGpP1hxOyG9G0BLKTStYB/image.png)

### SQL

Multiple databases in the same instance. In a development environment (see `util.is_development`) the code will `CREATE DATABASE IF EXISTS` with every MySQL connection. This is not done in production to save on query time.

### GCS

Everything uses the same project-based upload bucket, but the paths are prefixed by branch name.

Beyond the upload bucket, GCS is not namespaced.

### Cron

Cron jobs specify a `target` so that job is run with the specified App Engine version. The cron job request handlers also use datastore and MySQL namespacing, so what jobs run and what data they use is sandboxed.

### Task Queues

Not tested, but should stay within the environment's namespace. See the [docs](https://cloud.google.com/appengine/docs/standard/python/multitenancy/multitenancy#Python_Using_namespaces_with_the_Task_Queue).

### Mandrill

Two api keys. The production key kept in a SecretValue so no one can see it. The other kept in version control (insecure) for development environments. If the dev key is ever compromised, we can turn it off without hurting production.

### Cleaning Up

We'll periodically want to delete things created by sandbox deployments:

* MySQL dbs
* Datastore namespaces
* App Engine versions
* folders in the GCS upload bucket

This is not yet automated.


## File Structure

### Static / Client Files

```
+ neptune
  + static                       # dev and prod builds, served as `/static`
    + app_manager
      + app.js
      + app.config.js
      + app.states.js
      + app.html.js              # generated, ng template cache module
      + app.scss
      + assets
        + app.[version].js       # bundled (concat, uglify, app js)
        + app.[version].css      # bundled (concat, uglify, app css)
        + images
        + programs
        + [component folders]
          + [component]
            + [component].js
            + [component].html
    + app_participate
      + ...similar to app_manager
    + nep_api                    # module dependencies
    + nep_cookies
    + nep_util
    + bower_components
    + ...any other `/static` level assets
  + templates
    + dist
      + index.html               # HTML entry served as `/`
      + participate.html         # HTML entry served as `/participate`

  + static_src                   # working source directory
    + app_manager                # apps start with `app_`
      + index.html               # -> templates/dist/index.html
      + app.js                   # app js entry point
      + app.config.js
      + app.states.js
      + app.scss                 # app scss entry point
        + [component folders]
          + [component_name]
            + [component].js
            + [component].html
            + [component].scss   # `@import from app.scss`
    + app_participate
      + index.html               # -> templates/dist/participate.html
      + ...similar to app_participate
    + nep_api                    # shared modules start with `nep_`
    + nep_cookies
    + nep_util
    + ...
    + assets                     # files to be coped to `/static`
      + programs
        + cg17
        + hg17
      + favicon.ico
      + privacy_policy.pdf
      + ...
    + bower_components           # `bower install` package location
    + karma                      # karma config tests
    + protractor                 # protractor config tests

```

## Datastore Indexes

When datastore indexes much change in production, we must update them before updating the code that uses them, otherwise production will throw errors related to the index being unavailable. This is done from the command line _from the neptune directory_. Be careful not to update a project's indexes with the wrong index.yaml file!

```
cd ~/Sites/neptune  # adjust for your file system
gcloud datastore indexes create index.yaml --project=neptuneplatform
```

## Versions

* 1.0 - Introduction of Babel into the build system, allowing ES6.
* 1.1 - Introduction of Switchboard
* 1.2 - Addition of `/api/emails`

## License

Neptune is [UNLICENSED](https://docs.npmjs.com/files/package.json#license):

> if you do not wish to grant others the right to use a private or unpublished package under any terms

This is notably not the same as being licensed with the [UNLICENSE](https://github.com/3rd-Eden/licenses/blob/master/licenses/UNLICENSE.txt).

## Tips and Tricks

### Fake participation

In api_handlers.Participation:

```
    def get_for_project_cohorts(self, ids_or_codes, user):
        return {
            id: [{
                'project_cohort_id': id,
                'value': '100',
                'survey_ordinal': 1,
                'n': 5,
            }]
            for id in ids_or_codes
        }
```

## Participation Codes

Attached to project cohorts. Generated by `code_phrase.py`. Needs to be monitored in case the space of codes fills up.

Things to check periodically:

* What is the current size of the space?
* How many exist in the datastore?
* Are collisions during generation attempts being logged? What do the logs say?
* If the space usage is too high:
  - Are there any "triton" codes that have no match in the triton db (from deleted classrooms)
  - Are there any from closed cohorts we can delete/reuse?
  - Are there any from orgs that are rejected?
  - Are there any from projects that are rejected?
  - Are there any that are themselves closed?
  - Are there any that are deleted?

### Checkup 2018-03-13

Current size of space:

Possibilities are two words from three lists in either order:

* fruit animal
* animal fruit
* animal adj
* adj animal
* fruit adj
* adj fruit

...minus the blacklisted combinations

2((13 * 39) + (39 * 41) + (41 * 13)) - 681 =

= 2(507 + 1599 + 533) - 681
= 5278 - 681
= 4597

How many in the datastore: 921

Usage: 20%

Conclusion: not worth optimizing.

### Checkup 2019-09-26

2((42 * 42) + (42 * 41) + (41 * 42)) - 691 = 9725

= 2(1764 + 1722 + 1722) - 691
= 2(5208) - 691

In datastore: 2124

Usage: 2124/9725 = 22%

Not worth optimizing.
