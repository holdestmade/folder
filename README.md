# Folder (UI configurable)

A custom component that overrides Home Assistant's built-in, YAML-only `folder`
integration so folders can be added and edited from the UI.

## Installation

Copy `custom_components/folder` into your Home Assistant `config/custom_components`
directory and restart Home Assistant. Because the domain is `folder`, this
component takes precedence over the built-in integration (Home Assistant logs a
warning that a built-in integration is being overridden — that is expected).

## Configuration

The folder you want to monitor must be allowed by Home Assistant:

```yaml
homeassistant:
  allowlist_external_dirs:
    - /media/downloads
```

Then go to **Settings → Devices & services → Add integration → Folder** and enter:

| Field | Description | Default |
| --- | --- | --- |
| Folder path | Full path of the folder to monitor | — |
| File filter | Glob pattern selecting files, e.g. `*.mp4` | `*` |
| Update interval | Seconds between folder scans | `60` |

Add the integration once per folder. Use **Configure** on an entry to change the
filter or the update interval, and **Reconfigure** to change the folder path.

## Entity

Each entry creates one sensor whose state is the total size in MB of the matched
files, with these attributes:

`path`, `filter`, `number_of_files`, `bytes`, `file_list`

`file_list` is excluded from the recorder database. It is still available in
templates and automations, but it is not written to history, so a folder with
many files cannot push the entity's attributes past the recorder's 16 KiB limit
(which would otherwise stop *all* of the entity's attributes being recorded).

## Migrating from YAML

Existing YAML configuration is imported automatically on startup and a repair
issue is raised. Once the entry appears under Devices & services, remove the
`folder` sensor platform from `configuration.yaml` and restart.
