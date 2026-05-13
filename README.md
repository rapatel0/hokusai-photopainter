# Hokusai PhotoPainter

Tools for building and displaying a Hokusai image collection on the Waveshare RPi Zero PhotoPainter.

## Local Archive

Build the local archive from official open-access museum APIs:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/compile_hokusai_photopainter.py
```

Generated folders are ignored by git:

```text
originals/
photopainter_800x480_bmp/
preview_800x480_jpg/
```

The compiler writes display-sized RGB BMPs by default. The Waveshare Python driver
does the final 6-color panel quantization in `epd7in3e.getbuffer()`, matching the
vendor display path. To regenerate existing BMPs after changing conversion
settings:

```bash
python scripts/compile_hokusai_photopainter.py --force
```

Metadata manifests are kept in `metadata/`.

## Raspberry Pi

The Pi stores display-ready images at:

```bash
~/Pictures/hokusai-photopainter
```

Display a specific image:

```bash
~/photopainter-venv/bin/python ~/photopainter-display-image.py /path/to/image.bmp
```

Advance through the Hokusai collection one image at a time:

```bash
~/photopainter-venv/bin/python ~/photopainter-show-hokusai.py
```

The rotation script clears the panel before each image by default to reduce
carry-over artifacts between daily prints. Use `--no-clear-first` only when you
want a faster refresh and can tolerate possible ghosting.

The stateful picker stores its next index in:

```bash
~/Pictures/hokusai-photopainter/.photopainter-state.json
```

Daily cron example:

```cron
0 5 * * * /usr/bin/flock -n /tmp/photopainter-hokusai.lock /home/ravi/photopainter-venv/bin/python /home/ravi/photopainter-show-hokusai.py >> /home/ravi/photopainter-rotate.log 2>&1
```
