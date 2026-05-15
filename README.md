# Hokusai PhotoPainter

Build and deploy a rotating Hokusai print archive for the Waveshare RPi Zero
PhotoPainter e-paper frame.

The project downloads open-access museum images, converts them for the 7.3-inch
six-color Waveshare display, and deploys the display-ready BMPs plus rotation
scripts to a Raspberry Pi.

## Dependencies

Local machine:

- [mise](https://mise.jdx.dev/) for Python and task management
- Python `3.13.13`, installed by mise
- Python packages from `requirements.txt`: `Pillow`, `requests`, `tqdm`
- `ssh` and `rsync` for deployment to the frame

Raspberry Pi / PhotoPainter:

- Waveshare PhotoPainter hardware with the 7.3-inch E Ink Spectra 6 display
- Raspberry Pi OS with Python 3
- Waveshare `waveshare_epd` Python driver installed in
  `/home/ravi/photopainter-venv`
- SSH access from the local machine

## Quick Start

Trust the local mise config, install Python, and create the virtualenv:

```bash
mise trust
mise install
mise run setup
```

Download Waveshare's reference converter bundle for local audit/comparison:

```bash
mise run converter
```

Build the archive from open-access museum APIs:

```bash
mise run build
```

After changing conversion settings, regenerate display images from the existing
manifest without re-querying museum APIs:

```bash
mise run reconvert
```

Refresh metadata and rebuild everything:

```bash
mise run rebuild
```

List available project tasks:

```bash
mise tasks ls --local
```

## Image Conversion

The default conversion fits the full artwork into an `800x480` landscape canvas
without cropping, then applies Waveshare's six-color PhotoPainter palette with
Floyd-Steinberg dithering.

Generated folders are intentionally ignored by git:

```text
originals/
photopainter_800x480_bmp/
preview_800x480_jpg/
diagnostics/
vendor/waveshare-photopainter/
```

Alternative conversion experiments:

```bash
.venv/bin/python scripts/compile_hokusai_photopainter.py --force --conversion adaptive
.venv/bin/python scripts/compile_hokusai_photopainter.py --force --conversion plain
.venv/bin/python scripts/compile_hokusai_photopainter.py --force --conversion waveshare-crop
```

Reverse-engineering notes for the Waveshare converter are in
[`docs/waveshare_dithering.md`](docs/waveshare_dithering.md).

## Deploy To The Frame

Set up an SSH alias for the frame:

```sshconfig
Host pi-window photopainter
  HostName 192.168.50.169
  User ravi
```

Deploy scripts and display-ready BMPs:

```bash
mise run deploy
```

The deploy task uses `pi-window` by default. Override it when needed:

```bash
HOST=photopainter mise run deploy
```

The deploy script syncs to:

```bash
~/Pictures/hokusai-photopainter
```

It preserves `.photopainter-state.json`, so rotation state is not lost while
BMPs are pruned and refreshed.

## Display And Rotation

Display a specific image on the Pi:

```bash
~/photopainter-venv/bin/python ~/photopainter-display-image.py /path/to/image.bmp
```

Redisplay the image named by the current state file without advancing rotation:

```bash
mise run display-current
```

Advance through the collection one image at a time:

```bash
~/photopainter-venv/bin/python ~/photopainter-show-hokusai.py
```

The rotation script performs one display refresh by default. Use `--clear-first`
only as a recovery option for visible ghosting; it performs a full clear refresh
before the image refresh, which roughly doubles the update cycle.

State is stored on the Pi at:

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
