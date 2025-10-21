# Installing the Meta Runner on Ubuntu

This guide describes how to install a TeamCity Meta Runner on an Ubuntu Server that hosts the TeamCity distribution. Meta Runners encapsulate reusable build steps so teams can share complex sequences without duplicating configuration.

## Requirements

- Ubuntu Server 20.04 LTS or later with Bash shell access.
- TeamCity server already extracted from the Linux distribution (for example under `/opt/TeamCity`).
- Administrator privileges on the TeamCity web UI or shell access to the account that owns the TeamCity files.
- The Meta Runner package (`*.runner` archive or the raw `meta-runner.xml` file) that you plan to install.

> **Note:** The TeamCity *data directory* stores configuration files, build histories, and meta-runners. Unless overridden, it defaults to `~/.BuildServer`. The commands below assume this directory; adjust paths if your server uses a custom data path.

## 1. Locate the TeamCity data directory

1. Connect to the Ubuntu host via SSH.
2. If you know the TeamCity installation directory, export it so future commands are shorter:
   ```bash
   export TEAMCITY_HOME=/opt/TeamCity
   ```
3. Check whether the installation overrides the data directory:
   ```bash
   grep -E '^teamcity.data.path' "${TEAMCITY_HOME}/conf/teamcity-startup.properties"
   ```
   - If nothing prints, TeamCity uses the default `~/.BuildServer` path for the account that starts the server.
   - If a value prints, note the path shown after `teamcity.data.path=` and use it in the remaining steps.

Set a helper variable for the resolved directory to reduce repetition:
```bash
export TEAMCITY_DATA_PATH="${HOME}/.BuildServer"  # replace if the grep command returned a custom value
```

## 2. Install through the web UI (recommended)

1. Sign in to TeamCity with a user that has the **System Administrator** role.
2. Navigate to **Administration → Meta-Runners**.
3. Click **Upload Meta Runner**.
4. Choose the `.runner` archive provided by your team (for example `linux-build-runner.runner`) and confirm.
5. TeamCity unpacks the archive into `${TEAMCITY_DATA_PATH}/config/_metaRunners` immediately.
6. Open any build configuration and add a new build step. The Meta Runner should appear in the **Runner type** list under the name defined inside its XML.

## 3. Offline installation from the shell

Use the manual procedure if the TeamCity UI is unavailable or you only have terminal access to the server.

1. Ensure the meta-runner directory exists:
   ```bash
   mkdir -p "${TEAMCITY_DATA_PATH}/config/_metaRunners"
   ```
2. If you received a `.runner` archive, extract the XML definition:
   ```bash
   unzip MetaRunner.runner meta-runner.xml
   ```
3. Copy the XML file into the TeamCity data directory. The filename becomes the Meta Runner ID, so pick a descriptive and unique name:
   ```bash
   cp meta-runner.xml "${TEAMCITY_DATA_PATH}/config/_metaRunners/MetaRunner.xml"
   ```
4. Restart TeamCity so it reloads custom runners. Use whichever command matches your deployment:
   - If you run TeamCity via the bundled scripts:
     ```bash
     "${TEAMCITY_HOME}/bin/runAll.sh" stop
     "${TEAMCITY_HOME}/bin/runAll.sh" start
     ```
   - If TeamCity runs as a `systemd` service (for example `teamcity`):
     ```bash
     sudo systemctl restart teamcity
     ```

After the restart, verify the new entry under **Administration → Meta-Runners** in the TeamCity UI.

## 4. Updating an existing Meta Runner

1. Download the new `.runner` archive or `meta-runner.xml` file.
2. Remove the old XML file from `${TEAMCITY_DATA_PATH}/config/_metaRunners`.
3. Upload the new package through the UI or replace the XML manually.
4. Restart TeamCity (or at least reload the administration page) so the change takes effect.

## 5. Removal

To remove a Meta Runner, delete its XML definition and restart TeamCity:
```bash
rm "${TEAMCITY_DATA_PATH}/config/_metaRunners/MetaRunner.xml"
"${TEAMCITY_HOME}/bin/runAll.sh" stop
"${TEAMCITY_HOME}/bin/runAll.sh" start
```

If you manage TeamCity with `systemd`, restart the service instead:
```bash
sudo systemctl restart teamcity
```

## 6. Troubleshooting

| Symptom | Resolution |
|---------|------------|
| The runner does not appear after uploading. | Confirm the XML file exists in `${TEAMCITY_DATA_PATH}/config/_metaRunners` and restart TeamCity. The server only loads new files at startup. |
| Permission denied when copying files. | Switch to the account that owns the TeamCity data directory (often `teamcity`) or use `sudo` with `chown` to grant access. |
| TeamCity fails to start after adding the XML. | Validate the XML syntax (must include the `<meta-runner>` root element). Remove the file and restart to recover. |
| Multiple runners share the same name. | Edit the `<name>` element in the XML or keep only one copy in the directory. |

Following these steps installs and manages Meta Runners on Ubuntu so teams can reuse complex build logic across multiple pipelines.
