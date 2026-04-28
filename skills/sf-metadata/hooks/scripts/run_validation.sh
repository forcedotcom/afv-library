#!/bin/bash
#
# Run Metadata Validation Script
#
# Usage:
#   ./run_validation.sh <metadata_file>
#
# Example:
#   ./run_validation.sh force-app/main/default/objects/MyObject__c/MyObject__c.object-meta.xml
#
# Validates Salesforce metadata files and provides scoring feedback.
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -z "$1" ]; then
    echo "Usage: $0 <metadata_file>"
    echo ""
    echo "Validates Salesforce metadata files:"
    echo "  - *.object-meta.xml  (Custom Objects)"
    echo "  - *.field-meta.xml   (Custom Fields)"
    echo "  - *.profile-meta.xml (Profiles)"
    echo "  - *.permissionset-meta.xml (Permission Sets)"
    echo ""
    echo "Example:"
    echo "  $0 force-app/main/default/objects/Account/Account.object-meta.xml"
    exit 1
fi

FILE_PATH="$1"

if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File not found: $FILE_PATH"
    exit 1
fi

# Run the Python validator
python3 "$SCRIPT_DIR/validate_metadata.py" "$FILE_PATH"
