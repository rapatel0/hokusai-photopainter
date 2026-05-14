# Waveshare PhotoPainter Dithering

This repo incorporates the behavior of Waveshare's `ConverTo6c_bmp-7.3`
PhotoPainter converter. The official bundle includes a readable `convert.py`;
the Mac and Windows executables are PyInstaller wrappers around the same logic.

## Pipeline

The converter does four things:

1. Load the source image with Pillow.
2. Choose display orientation:
   - landscape: `800x480`
   - portrait: `480x800`
   - unspecified: landscape when source width is greater than height, otherwise portrait
3. Resize to the target frame.
4. Quantize to a 7-entry indexed palette, using Floyd-Steinberg dithering by default.

The official `scale` mode is scale-to-fill, so it can crop the artwork:

```python
scale_ratio = max(target_width / width, target_height / height)
resized_width = int(width * scale_ratio)
resized_height = int(height * scale_ratio)
resized = input_image.resize((resized_width, resized_height))
canvas = Image.new("RGB", (target_width, target_height), (255, 255, 255))
canvas.paste(resized, centered_offset)
```

The official `cut` mode uses `ImageOps.pad(...)`, which also fills the target
aspect ratio and can crop.

## Palette

Waveshare uses this palette:

| Index | Color |
| --- | --- |
| `0` | black `(0, 0, 0)` |
| `1` | white `(255, 255, 255)` |
| `2` | yellow `(255, 255, 0)` |
| `3` | red `(255, 0, 0)` |
| `4` | unused black `(0, 0, 0)` |
| `5` | blue `(0, 0, 255)` |
| `6` | green `(0, 255, 0)` |

In Pillow:

```python
pal_image = Image.new("P", (1, 1))
pal_image.putpalette(
    (0, 0, 0, 255, 255, 255, 255, 255, 0, 255, 0, 0, 0, 0, 0, 0, 0, 255, 0, 255, 0)
    + (0, 0, 0) * 249
)
```

## Dithering

The converter calls:

```python
quantized = resized_image.quantize(
    dither=Image.Dither.FLOYDSTEINBERG,
    palette=pal_image,
).convert("RGB")
```

So the visible dot pattern is Pillow's Floyd-Steinberg error diffusion, not a
Waveshare-specific proprietary algorithm.

Pillow's Floyd-Steinberg diffusion distributes quantization error to neighboring
unprocessed pixels with the standard weights:

```text
        X   7/16
  3/16 5/16 1/16
```

The converter can disable dithering with `--dither 0`, but the default is
Floyd-Steinberg (`--dither 3`).

## Driver Packing

The low-level `epd7in3e.getbuffer()` uses the same palette, then packs two
4-bit palette indexes into each byte:

```python
buf[idx] = (buf_6color[i] << 4) + buf_6color[i + 1]
```

That packed buffer is what the panel receives.

## Repo Behavior

This repo's default `--conversion waveshare` intentionally differs from the
official converter in one place: it fits the whole artwork into `800x480`
without cropping, then applies the same palette and Floyd-Steinberg quantizer.

Use `--conversion waveshare-crop` to reproduce the official scale-to-fill crop
exactly.
