# Visenlo website

A static promotional and download website for the local Visenlo face-swap studio. Plain HTML, CSS, and JavaScript; no build step or backend.

## Preview locally

From this folder:

```bash
python3 -m http.server 8088 --bind 127.0.0.1
```

Open **http://127.0.0.1:8088**. The local app is a separate process, normally at http://127.0.0.1:7860.

## What is included

- Responsive landing page, working mobile navigation, platform-specific setup tabs, keyboard navigation, clipboard feedback, and expandable FAQs.
- A model setup guide that distinguishes required weights, optional finishing models, and experimental adapters.
- A source ZIP download at `downloads/Visenlo.zip`. It contains the application source; it is **not** a standalone executable and excludes model weights, virtual environments, outputs, and personal test images.
- Local fonts and original SVG illustrations. No external font service, image CDN, analytics, or image uploads.
- Branded favicon, social sharing image, search verification, sitemap, and a custom `404.html`.

## Starting the downloaded application

Extract the ZIP and open a terminal in its `Visenlo/` folder. On Linux/macOS, run `./run.sh` (use `chmod +x run.sh` once if your extractor removes execute permissions). On Windows, double-click `run.bat` or run `.\run.bat` in PowerShell. The scripts handle the Python bootstrap internally and open the local studio. In Model setup, review the model terms, tick the acknowledgement and choose Install required models. Required assets install with progress; the swap button becomes available when ready. Python still needs to be installed as described on the website.

## Updating the application download

After changing the sibling application, rebuild its source archive and copy the resulting archive to `downloads/Visenlo.zip` before publishing this website. From this website folder:

```bash
python3 ../ReactorX/scripts/make_dist.py
mkdir -p downloads
cp ../ReactorX/dist/Visenlo-v1.zip downloads/Visenlo.zip
```
 Inspect the archive listing to ensure it contains no `.venv`, `.venvs`, `.git`, model weights, outputs, or test images. Keep download instructions and model guide aligned with the included source.

## Publishing

Serve this folder as a static site. On Vercel, use this folder as the project root with **Other** as the framework and no build command. No API keys or environment variables are needed. The canonical domain is `https://reactor-web-seven.vercel.app/`; update canonical/Open Graph URLs, `robots.txt`, and `sitemap.xml` together if it changes.

The source project is [Mevinb/Visenlo](https://github.com/Mevinb/Visenlo). Deploy this folder to publish website changes. Model weights have separate upstream licenses and are installed by the application user.

## Fonts and assets

Space Grotesk, DM Sans, and DM Mono are self-hosted; their SIL Open Font License files are in `assets/`. `face-study.svg` is a workflow illustration, not an example of a generated face swap.

## SEO verification

Run `python3 scripts/check_seo.py` for local crawl, metadata, structured-data, sitemap, asset and download checks. After publishing, run it with `--live` to verify the deployed responses. See [SEO maintenance and deployment notes](docs/SEO.md), including the corrected production hostname and release checks.
