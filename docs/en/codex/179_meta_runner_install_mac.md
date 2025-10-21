# Installing the Meta Runner on macOS

This guide explains how to install a TeamCity Meta Runner on a Mac workstation or server running the TeamCity distribution.
Meta Runners bundle a sequence of build steps so they can be reused across projects. Once installed they appear as custom build
steps alongside the built-in runners.

## Requirements

- macOS 12 Monterey or later.
- A TeamCity server already extracted from the Linux/macOS distribution (for example under `/Applications/TeamCity`).
- Access to an administrator account on the TeamCity server UI.
- The Meta Runner package (`*.runner` archive or the raw `meta-runner.xml` file) that you want to import.

> **Tip:** The TeamCity *data directory* (the location that stores configuration files and meta-runners) defaults to
> `~/.BuildServer` unless overridden in `conf/teamcity-startup.properties`. All paths below refer to that directory.

## 1. Confirm the data directory location

1. Open **Terminal**.
2. If you know the TeamCity installation directory, export it for convenience:
   ```bash
   export TEAMCITY_HOME=/Applications/TeamCity
   ```
3. Check whether the installation overrides the data directory:
   ```bash
   grep -E '^teamcity.data.path' "${TEAMCITY_HOME}/conf/teamcity-startup.properties"
   ```
   - If the command prints nothing, TeamCity uses the default `~/.BuildServer` path.
   - If it prints a value, note the path referenced after `teamcity.data.path=`. That will be used in the next steps.

Set a shell variable with the resolved path so subsequent commands are shorter:
```bash
export TEAMCITY_DATA_PATH="${HOME}/.BuildServer"  # replace if you found a custom value
```

## 2. Install through the web UI (recommended)

1. Sign in to TeamCity as a user with the **System Administrator** role.
2. Navigate to **Administration → Meta-Runners**.
3. Click **Upload Meta Runner**.
4. Select the `.runner` archive provided by your team (for example `meta-runner-power-pack.runner`) and confirm.
5. TeamCity immediately unpacks the archive into `${TEAMCITY_DATA_PATH}/config/_metaRunners`.
6. Open any build configuration and add a new build step. The Meta Runner should now appear under **Runner type** using the
   name defined inside the package.

## 3. Offline installation from Terminal

If the server cannot reach the TeamCity UI or you only have shell access, copy the definition manually.

1. Ensure the meta-runner directory exists:
   ```bash
   mkdir -p "${TEAMCITY_DATA_PATH}/config/_metaRunners"
   ```
2. If you have a `.runner` archive, extract the `meta-runner.xml` file:
   ```bash
   unzip MetaRunner.runner meta-runner.xml
   ```
3. Copy the XML definition into the TeamCity data directory. The filename becomes the displayed ID, so choose something unique:
   ```bash
   cp meta-runner.xml "${TEAMCITY_DATA_PATH}/config/_metaRunners/MetaRunner.xml"
   ```
4. Restart the TeamCity server to force it to reload custom runners:
   ```bash
   "${TEAMCITY_HOME}/bin/runAll.sh" stop
   "${TEAMCITY_HOME}/bin/runAll.sh" start
   ```

After the restart, open the TeamCity UI and verify the new runner appears in **Administration → Meta-Runners**.

## 4. Updating an existing Meta Runner

1. Download the new `.runner` archive or `meta-runner.xml`.
2. Delete the old XML from `${TEAMCITY_DATA_PATH}/config/_metaRunners`.
3. Upload the new package through the UI or replace the XML manually.
4. Restart (or at least reload the UI page) so TeamCity refreshes cached definitions.

## 5. Removal

To remove a Meta Runner, delete its XML file and restart TeamCity:
```bash
rm "${TEAMCITY_DATA_PATH}/config/_metaRunners/MetaRunner.xml"
"${TEAMCITY_HOME}/bin/runAll.sh" stop
"${TEAMCITY_HOME}/bin/runAll.sh" start
```

## 6. Troubleshooting

| Symptom | Resolution |
|---------|------------|
| The runner does not appear after uploading. | Confirm the XML file is present inside `${TEAMCITY_DATA_PATH}/config/_metaRunners` and that the server was restarted if you installed it manually. See also [Fixing Meta Runner installers](182_meta_runner_fix_installers.md) for deeper troubleshooting. |
| Permission denied when copying files. | Ensure your macOS account owns `${TEAMCITY_DATA_PATH}`. If TeamCity runs under a dedicated user, switch to that account before copying. |
| TeamCity fails to start after adding the XML. | Validate the XML file syntax (it must contain the `<meta-runner>` root element). Remove the file and restart to recover. |
| Multiple runners have the same display name. | Rename the `<name>` element inside the XML or keep a single copy of the runner in the directory. |

Following these steps installs the Meta Runner on macOS and makes it available for reuse across TeamCity build configurations.
