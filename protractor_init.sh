#!/bin/bash

# Start server processes required for protractor tests. Follow this command
# with `grunt protractor`.

set -e

nohup bash -c "webdriver-manager start &"
echo "Make sure the sdk is running on :8080"

