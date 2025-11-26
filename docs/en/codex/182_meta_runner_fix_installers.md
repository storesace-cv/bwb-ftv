# Fixing Meta Runner installers on TeamCity

This guide explains how to debug and fix common problems when importing a TeamCity
Meta Runner package. Use it after following the platform-specific installation
instructions and the runner still fails to appear under **Administration →
Meta-Runners**.

## 1. Confirm the data directory

1. Determine the TeamCity installation directory (for example
   `/Applications/TeamCity` on macOS or `/opt/TeamCity` on Linux) and export it:
   ```bash
   export TEAMCITY_HOME=/path/to/TeamCity
   ```
2. Inspect `conf/teamcity-startup.properties` to check whether a custom data
   directory is configured:
   ```bash
   grep -E '^teamcity.data.path' "${TEAMCITY_HOME}/conf/teamcity-startup.properties"
   ```
3. If no override is present, TeamCity uses the default `~/.BuildServer` path for
   the account that starts the server. Set a helper variable so later commands
   remain concise:
   ```bash
   export TEAMCITY_DATA_PATH="${HOME}/.BuildServer"
   ```

Incorrect data paths are the most common reason a freshly installed Meta Runner
fails to appear because TeamCity silently ignores files in other directories.

## 2. Verify the unpacked XML file

1. Unpack the `.runner` archive locally and ensure the file is named
   `meta-runner.xml`. Some archives contain the file inside `META-INF` – extract
   only the XML:
   ```bash
   unzip -j CustomRunner.runner meta-runner.xml
   ```
2. Open the XML and confirm the `<meta-runner>` root element exists and that the
   `<name>` tag matches the expected display name. Rename the file if you need a
   unique identifier inside `_metaRunners`:
   ```bash
   mv meta-runner.xml "${TEAMCITY_DATA_PATH}/config/_metaRunners/CustomRunner.xml"
   ```
3. Set file ownership to the account that runs TeamCity so the server can read it:
   ```bash
   sudo chown teamcity:teamcity "${TEAMCITY_DATA_PATH}/config/_metaRunners/CustomRunner.xml"
   ```

TeamCity ignores files with missing `<meta-runner>` nodes or incorrect
permissions.

## 3. Reload the server cache

1. Restart the TeamCity services so the new definition is picked up:
   ```bash
   "${TEAMCITY_HOME}/bin/runAll.sh" stop
   "${TEAMCITY_HOME}/bin/runAll.sh" start
   ```
   If you manage TeamCity via `systemd`, restart the service instead:
   ```bash
   sudo systemctl restart teamcity
   ```
2. After the restart, open **Administration → Meta-Runners** and confirm the new
   entry is listed. If not, review `logs/teamcity-server.log` inside the data
   directory for parsing errors around the time of the restart.

## 4. Cleaning duplicate or broken installers

If the UI shows an outdated version or the runner disappears immediately after a
restart, clean the directory manually:

1. Remove any stale XML files from `${TEAMCITY_DATA_PATH}/config/_metaRunners`.
2. Clear the directory `.BuildServer/system/caches/metaRunners` if it exists.
3. Restart TeamCity again and re-import the desired runner package.

Following these steps resolves most installation issues without having to rebuild
or repackage the Meta Runner archive.
