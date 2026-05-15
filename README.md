# Hokusai PhotoPainter

Tools for building and displaying a Hokusai image collection on the Waveshare RPi Zero PhotoPainter.

## Local Archive

Bootstrap a local machine:

```bash
mise trust
mise install
mise run setup
mise run converter
```

Available project tasks:

```bash
mise tasks ls --local
```

Build the local archive from official open-access museum APIs:

```bash
mise run build
```

Regenerate already-downloaded images after changing conversion settings:

```bash
mise run reconvert
```

Use `mise run rebuild` when you also want to refresh the museum API metadata
and download any newly discovered source images.

Generated folders are intentionally ignored by git:

```text
originals/
photopainter_800x480_bmp/
preview_800x480_jpg/
diagnostics/
vendor/waveshare-photopainter/
```

The compiler uses Waveshare's six-color PhotoPainter palette and
Floyd-Steinberg dithering by default, while fitting the full artwork into the
800x480 display without cropping. The `--conversion waveshare-crop` mode matches
Waveshare's official scale-to-fill crop behavior exactly.

The reverse-engineered converter notes are in
[`docs/waveshare_dithering.md`](docs/waveshare_dithering.md).

The upstream converter bundle can be downloaded for comparison or audit:

```bash
mise run converter
```

Alternative local conversion experiments remain available:

```bash
python scripts/compile_hokusai_photopainter.py --force --conversion adaptive
python scripts/compile_hokusai_photopainter.py --force --conversion plain
python scripts/compile_hokusai_photopainter.py --force --conversion waveshare-crop
```

Metadata manifests are kept in `metadata/`.

## Raspberry Pi

Set up an SSH alias for the frame. The mise tasks use `pi-window` by default;
override it with `HOST=...` when needed:

```sshconfig
Host pi-window photopainter
  HostName 192.168.50.169
  User ravi
```

The Pi stores display-ready images at:

```bash
~/Pictures/hokusai-photopainter
```

Deploy scripts and display-ready BMPs:

```bash
mise run deploy
HOST=pi-window mise run deploy
```

The deploy script keeps `.photopainter-state.json` on the Pi while syncing and
pruning BMPs, so rotation state is not lost.

Display a specific image:

```bash
~/photopainter-venv/bin/python ~/photopainter-display-image.py /path/to/image.bmp
```

Redisplay the image named by the current state file without advancing rotation:

```bash
mise run display-current
HOST=pi-window mise run display-current
```

Advance through the Hokusai collection one image at a time:

```bash
~/photopainter-venv/bin/python ~/photopainter-show-hokusai.py
```

The rotation script performs one display refresh by default. Use `--clear-first`
only as a recovery option for visible ghosting; it performs a full clear refresh
before the image refresh, which roughly doubles the update cycle.

The stateful picker stores its next index in:

```bash
~/Pictures/hokusai-photopainter/.photopainter-state.json
```

Twice-daily cron example:

```cron
0 5,12 * * * /usr/bin/flock -n /tmp/photopainter-hokusai.lock /home/ravi/photopainter-venv/bin/python /home/ravi/photopainter-show-hokusai.py >> /home/ravi/photopainter-rotate.log 2>&1
```

## License

Project code is licensed under the MIT License. Generated images are not
included in this repository; see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
for museum source and Waveshare reference-converter notes.
