# Folder (UI configurable)

[![hacs][hacs-badge]][hacs-url]

A custom component that overrides Home Assistant's built-in, YAML-only `folder`
integration so folders can be added and edited from the UI.

Requires Home Assistant 2024.11 or newer.

## Installation

### HACS (custom repository)

This integration is not in the HACS default store, so add it as a custom
repository:

1. In Home Assistant go to **HACS**.
2. Open the three-dot menu at the top right and choose **Custom repositories**.
3. Add `https://github.com/holdestmade/folder` with the type **Integration**.
4. Find **Folder** in the list, click **Download**, then restart Home Assistant.

### Manual

Copy `custom_components/folder` into your Home Assistant `config/custom_components`
directory and restart Home Assistant.

Either way, because the domain is `folder`, this component takes precedence over
the built-in integration — Home Assistant logs a warning that a built-in
integration is being overridden, which is expected.

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
| File filter | Glob patterns selecting files, comma separated, e.g. `*.mkv, *.mp4` | `*` |
| Include subfolders | Also count files in every subfolder | off |
| Update interval | Seconds between folder scans | `60` |

Add the integration once per folder. Use **Configure** on an entry to change the
filter, the subfolder setting or the update interval, and **Reconfigure** to
change the folder path.

### The file filter

The filter is a comma separated list of glob patterns, and a file is counted if
it matches any of them:

| Filter | Counts |
| --- | --- |
| `*` | everything (the default) |
| `*.mkv` | one extension |
| `*.mkv, *.mp4, *.avi` | several extensions |

Listing extensions is the way to keep sidecar files such as `Thumbs.db` or
`desktop.ini` out of the total when you cannot delete them.

Matching ignores case, so `*.mkv` also counts `.MKV` and `.Mkv`. A file
matching more than one pattern is still only counted once.

### Including subfolders

With **Include subfolders** off (the default) only files directly inside the
configured folder are counted. With it on, the whole tree below the folder is
walked and the filter is matched against each file name, so `*.mp4` on
`/media` counts `/media/films/a.mp4` as well as `/media/b.mp4`.

Two things are deliberately skipped in both modes:

- **Symlinked folders are not followed.** They can point outside the configured
  folder, and a symlink loop would be walked until the path length limit stops
  it.
- **Hidden files and folders** (names starting with `.`) are not counted, so a
  `.git` or `.stfolder` directory does not inflate the total.

## Entities

Each entry creates a device named after the folder, with two sensors:

| Entity | State |
| --- | --- |
| `sensor.<folder>` | Total size in MB of the matched files |
| `sensor.<folder>_number_of_files` | Count of matched files |

Both have a `measurement` state class, so both get long-term statistics.

The size sensor also carries these attributes:

`path`, `filter`, `recursive`, `number_of_files`, `bytes`, `file_list`

`file_list` is excluded from the recorder database. It is still available in
templates and automations, but it is not written to history, so a folder with
many files cannot push the entity's attributes past the recorder's 16 KiB limit
(which would otherwise stop *all* of the entity's attributes being recorded).

## Migrating from YAML

Existing YAML configuration is imported automatically on startup and a repair
issue is raised. Once the entry appears under Devices & services, remove the
`folder` sensor platform from `configuration.yaml` and restart.

## Counting behaviour

Only real files are counted. Earlier versions matched the filter with `glob`
and counted whatever it returned, so a bare `*` filter also counted every
subdirectory as a file — the `bytes` attribute has always excluded them. If you
used the default filter, the file count may now be lower than before by the
number of subdirectories in the folder; nothing else changed.

## License

[Apache-2.0](LICENSE). This integration is derived from the `folder` integration
in [Home Assistant Core][ha-core], which is also licensed under Apache-2.0.

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
[ha-core]: https://github.com/home-assistant/core
