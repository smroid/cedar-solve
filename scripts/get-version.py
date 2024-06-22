"""
Parse the version string from the project metadata and print it in a format
that can be consumed in GitHub workflows.

Only intended to be used by CI pipeline.
"""
import build.util

if __name__ == '__main__':
    version = build.util.project_wheel_metadata('.').get('Version')
    # formatted for capture in GitHub actions like:
    # - id: get-version
    #   run: python scripts/get-version.py >> "$GITHUB_OUTPUT"
    print(f"version={version}")
