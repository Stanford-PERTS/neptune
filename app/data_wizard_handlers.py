"""Data Wizard handlers. Here if we want to start this project up again."""


class DataRequests(RestHandler):
    model = DataRequest

    def post(self, override_permissions=False):
        # Create the data request entity the standard RESTful way.
        req = super(DataRequests, self).post(override_permissions)

        # req might be None if there was an error
        if not req:
            return

        # If the recipient doesn't already exist, they'll need an invitation.
        if User.email_exists(req.email):
            recipient = User.get_by_auth('email', req.email)
        else:
            recipient = User.invite(
                to_address=req.email,
                subject="Invitation to submit data: {}".format(req.title),
                template='datarequest_invitation.html',
                template_data={'data_request': req.to_client_dict()},
                continue_url=req.link,
            )

            # Give them access so the wizard link will let them in.
            recipient.owned_data_requests.append(req.uid)

        # Either way, they get a notification.
        notifier.received_data_request(recipient, req)


class UploadDataTableUrl(ApiHandler):
    def get(self):
        # The bucket must be created in the app, and it must be set so that all
        # files uploaded to it are public. All of this is easy with the
        # developer's console; look for the three-vertical-dots icon after
        # creating the bucket.
        bucket = app_identity.get_application_id() + '-upload/data_tables'

        # Valid for 10 minutes, to which a user can POST their file to
        # Google Cloud Storage (even though it's using the blobstore API).
        upload_url = blobstore.create_upload_url(
            success_path='/api/data_tables',
            gs_bucket_name=bucket,
            max_bytes_per_blob=pow(10, 7),  # 10 Megabytes
            max_bytes_total=(5 * pow(10, 7)),  # 50 Megabytes
        )
        self.response.write(json.dumps(upload_url))


class DownloadDataTable(blobstore_handlers.BlobstoreDownloadHandler):
    """View a file, adding convenient download headers."""
    def get(self, id):
        data_table = DataTable.get_by_id(id)

        # Although this inherits from webapp's "Blobstore" handler, the files
        # actually reside in Google Cloud Storage. That's why we convert from
        # the gcs file name.
        blob_key = blobstore.create_gs_key(data_table.gs_object_name)

        # Attach headers that make the file 1) immediately download rather than
        # opening in the browser and 2) have a pretty file name.
        self.response.headers['Content-Disposition'] = (
            "attachment; filename=" + str(data_table.filename))
        self.send_blob(blob_key)


class DataTables(RestHandler, blobstore_handlers.BlobstoreUploadHandler):
    model = DataTable

    def post(self):
        """Called when a file upload is complete.

        Inherits from a webapp2 convenience class:
        https://cloud.google.com/appengine/docs/python/tools/webapp/blobstorehandlers#BlobstoreUploadHandler
        """
        user = self.get_current_user()
        if not user:
            raise PermissionDenied()

        # Count the lines in the file. Go line by line and don't store the
        # actual data to avoid using too much memory.
        blobInfo = self.get_uploads()[0]
        num_lines = 0
        with blobInfo.open() as blobReader:
            try:
                while blobReader.next():
                    num_lines += 1
            except StopIteration as e:
                # blobReader seems to raise StopIteration at the end of the
                # file. All we want to do it count lines, though, so until
                # we have evidence that this counts badly, ignore it.
                pass

        file_info = self.get_file_infos()[0]
        data_table = DataTable.create(
            user_id=user.uid,
            filename=file_info.filename,
            gs_object_name=file_info.gs_object_name,
            size=file_info.size,
            content_type=file_info.content_type,
            num_rows=num_lines - 1,  # assuming first line is header
        )

        ndb.put_multi([data_table, user])

        self.response.write(json.dumps(data_table.to_client_dict()))


data_wizard_routes = [
    Route('/api/data_requests', DataRequests),
    Route('/api/data_requests/<id>', DataRequests),
    # @todo: not clear how to associate data request to users, since when
    # they're created we might not know the user's uid.
    # Route('/api/<parent_type:users>/<rel_id>/data_tables',
    #       RelatedQuery(DataTable, 'user_id')),
    Route('/api/data_tables/upload_url', UploadDataTableUrl),
    Route('/api/data_tables', DataTables),
    Route('/api/data_tables/<id>', DataTables),
    Route('/api/data_tables/<id>/csv', DownloadDataTable),
    Route('/api/<parent_type:users>/<rel_id>/data_tables',
          RelatedQuery(DataTable, 'user_id')),
    Route('/api/<parent_type:organizations>/<rel_id>/data_tables',
          RelatedQuery(DataTable, 'organization_id')),
]
