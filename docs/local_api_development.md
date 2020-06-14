# Developing with Google APIs locally

Code that connects to Google services, like Cloud Storage or BigQuery, typically makes use of environment variables available in production to get an access token, and that token authorizes API calls.

When working locally, if you want API calls to succeed (i.e. you're not mocking them), you need to set a few things up. These steps are described in [this SO post][1] but also recorded here in greater detail.

1. Get a private key for the App Engine Default Service Account from the cloud console. Download it in .p12 format then transform it (in a mounted crypt file) like this:

```
cat ~/Downloads/Neptune-072c0b11bc53.p12 | openssl pkcs12 -nodes -nocerts -passin pass:notasecret | openssl rsa > /Volumes/NO NAME/neptune_local_private_key.pem
rm ~/Downloads/Neptune-072c0b11bc53.p12
```

2. Start the sdk with additional flags:

```
dev_appserver.py . -A=neptuneplatform \
  --appidentity_email_address=neptuneplatform@appspot.gserviceaccount.com \
  --appidentity_private_key_path=/Volumes/NO NAME/neptune_local_private_key.pem \
  [OTHER TYPICAL FLAGS HERE]
```

An example call with full flags:

```
dev_appserver.py . -A=neptuneplatform --port=8080 --admin_port=8008 \
  --storage_path=.gae_sdk --enable_console=yes --enable_host_checking=no \
  --support_datastore_emulator=true \
  --appidentity_email_address=neptuneplatform@appspot.gserviceaccount.com \
  --appidentity_private_key_path="/Volumes/NO NAME/app engine credentials/neptune/service accounts/default_service_account.private_key.pem"
```

3. Calls to `google.appengine.api.app_identity.get_access_token()` should now return real tokens that can read/write to the production app.

4. Store the private key safely in a crypt and DO NOT COMMIT it to the repo.

[1]: https://stackoverflow.com/questions/20349189/unable-to-access-bigquery-from-local-app-engine-development-server/22723127#22723127

5. If using client libraries, like `cloudstorage`, their normal behavior is to work against a local stub of the service. Most of the time this is great, but if you really want it to communicate with the production app, you need to shortcut its stubbing functionality. In the case of `cloudstorage`, have `cloudstorage.common.local_run()` always return `False`, just make sure to remove this hack when done.

