#!/bin/bash

# Variables here come from a variety of sources:
#
# * Hard-coded in the codeship project settings, via the web UI:
#   - GOOGLE_KEY_MASTER
#   - GOOGLE_KEY_DEV
# * Always set by codeship (or just linux) on the build machine:
#   - HOME
# * Text files created by branch_environment.py (only in codeship):
#   - project_id.txt
#   - app_engin_version.txt

# This ensures that lines which have an error cause this whole script to
# exit with an error.
# http://stackoverflow.com/questions/3474526/stop-on-first-error
set -e

PROJECT_ID=$(cat project_id.txt)
APP_ENGINE_VERSION=$(cat app_engine_version.txt)
DEPLOY_CRON=true

if [ "$PROJECT_ID" == "neptuneplatform" ]
then
  if [ "$APP_ENGINE_VERSION" != "production" ]
  then
    # Do not confuse things with multiple crons in the same project.
    DEPLOY_CRON=false
  fi
  GOOGLE_KEY="$GOOGLE_KEY_MASTER"
else
  GOOGLE_KEY="$GOOGLE_KEY_DEV"
fi

# Do not write the key to the clone, because we don't want it deployed.
echo "${GOOGLE_KEY}" > "$HOME/google-key.json"
gcloud auth activate-service-account --key-file="$HOME/google-key.json"

gcloud app deploy app.yaml --project="${PROJECT_ID}" --version="${APP_ENGINE_VERSION}" --no-promote

if [ "$DEPLOY_CRON" = true ]
then
  gcloud app deploy cron.yaml --project="${PROJECT_ID}"
fi