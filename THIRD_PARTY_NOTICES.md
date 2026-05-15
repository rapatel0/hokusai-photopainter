# Third-Party Notices

This repository contains code and metadata for building a local Hokusai image
archive for a Waveshare PhotoPainter frame. It does not intentionally include
downloaded source images, generated preview images, generated display BMPs, or
Waveshare's reference converter bundle.

## Museum Images And Metadata

Generated image archives are ignored by git:

- `originals/`
- `photopainter_800x480_bmp/`
- `preview_800x480_jpg/`
- `diagnostics/`

The build scripts download images and metadata from open-access museum sources.
Those generated local files remain governed by the source institutions' open
access terms and metadata in the generated manifest.

Sources currently used by the compiler:

- Art Institute of Chicago Open Access Images and API
  - https://www.artic.edu/open-access-images
  - https://api.artic.edu/docs/
- The Metropolitan Museum of Art Open Access Initiative and Collection API
  - https://www.metmuseum.org/hubs/open-access
  - https://metmuseum.github.io/
- Cleveland Museum of Art Open Access API
  - https://www.clevelandart.org/open-access
  - https://openaccess-api.clevelandart.org/

The tracked manifest files are derived from those public APIs and include source
URLs, object metadata, license status fields, and local generated filenames.

## Waveshare PhotoPainter Reference Converter

The script `scripts/download_waveshare_converter.py` downloads Waveshare's
reference PhotoPainter converter bundle into `vendor/waveshare-photopainter/`
for local audit and comparison. That directory is ignored by git.

Waveshare's converter bundle and Waveshare hardware/software documentation are
not licensed by this repository's MIT license. They remain governed by
Waveshare's own terms.

Relevant Waveshare pages:

- https://www.waveshare.com/photopainter-b.htm
- https://www.waveshare.com/wiki/PhotoPainter
- https://www.waveshare.com/wiki/7.3inch_e-Paper_HAT_(E)_Manual
