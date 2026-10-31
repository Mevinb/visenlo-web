# Visenlo search visibility and release checks

The website targets people looking for a local AI face-swap application and practical model setup. Search position depends on relevance, competition, reputation, and Google's systems. Neither this implementation nor a Lighthouse score guarantees indexing, rich results, or first place. Google's [SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide) explicitly makes that distinction.

## Production issue to resolve first

On 2026-10-31 the repository’s public GitHub API identified **`https://reactor-web-seven.vercel.app/` as its homepage**, and that hostname returned HTTP 200 with the original Visenlo website and the correct application repository links. The deployed page incorrectly declared `https://visenlo-web.vercel.app/` as its canonical. Its deployed robots file and sitemap repeated that incorrect hostname, which returned **HTTP 404 / `DEPLOYMENT_NOT_FOUND`**. This was a real canonical-domain mismatch, not evidence that the actual Visenlo website was completely offline.

The local canonicals, Open Graph URLs, JSON-LD IDs, robots declaration, sitemap and validation script now consistently use the confirmed production origin, `https://reactor-web-seven.vercel.app/`. The new model guide, fixed download and other improvements were subsequently published through the existing GitHub-to-Vercel integration in commit `7a34a01`. The homepage, guide, assets and current source ZIP now return HTTP 200. Repository evidence: [GitHub repository metadata](https://api.github.com/repos/Mevinb/visenlo-web), [successful deployment status](https://api.github.com/repos/Mevinb/visenlo-web/deployments/6552488331/statuses). The commit’s public [Vercel status](https://api.github.com/repos/Mevinb/visenlo-web/commits/3c95e2d7c31bb15a4a6a72d0e863a8aa764067c9/status) also exposes the exact dashboard deployment URL under [project `reactor-web`](https://vercel.com/mevinbenty507-9965s-projects/reactor-web), in scope `mevinbenty507-9965s-projects`. This identifies the existing project to open; publishing used the authenticated GitHub account and the existing Vercel integration, without changing account permissions.

Redeploy the website through that existing Vercel project. For the standalone `Mevinb/visenlo-web` repository, keep Root Directory at the repository root (`.`). If deploying from the combined parent workspace, select its `visenlo-web/` folder. `vercel.json` selects the Other/static preset, skips the build, and serves this directory. The config also redirects `/index.html` to `/` with HTTP 308 and sends the source ZIP as an attachment with an `X-Robots-Tag: noindex` header. CSS, JavaScript, and `/assets/` use a one-hour browser cache with revalidation, without an `immutable` promise for files whose names do not include content hashes. It deliberately does not rewrite every unknown route to the homepage: missing routes should stay HTTP 404. The existing Google verification file and token are preserved. `.vercelignore` excludes local maintenance docs/scripts, README, and repository metadata from CLI uploads. This is configured locally, not a verified production manifest; for Git-triggered deployments, inspect the built/served file list rather than assuming the CLI default ignore behavior applies. See Vercel’s [file exclusion guide](https://vercel.com/docs/deployments/vercel-ignore) and [CLI-specific default exclusions](https://vercel.com/docs/builds/build-features).

If the actual production domain changes, update **both pages' canonicals, Open Graph URLs and JSON-LD IDs, robots.txt, sitemap.xml, and the `ORIGIN` constant in scripts/check_seo.py together**. Do not leave canonical URLs pointing to an abandoned hostname. Preview deployments should retain the intended production canonical; never submit previews as production pages.

## What this implementation covers

| Page | Purpose | Search intent it addresses |
| --- | --- | --- |
| `/` | Explain and download the actual local application | Visenlo, local/offline AI face swap, Windows/Linux face-swap app, multiple references and batches |
| `/model-guide.html` | Complete model setup, run a first swap, and resolve actual errors | Visenlo model setup, buffalo_l/InSwapper, slow CPU processing, missing models, face detection and Pixel Boost |

These are useful topics, not measured search-volume claims. The guide contains product-specific commands, file paths, tradeoffs and troubleshooting. Adding many near-identical pages for keyword variants would reduce usefulness rather than establish expertise. Google's guidance prioritizes [original, helpful, people-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content).

Both pages have distinct descriptive titles, descriptions, self-referencing HTTPS canonicals, coherent social metadata, and JSON-LD delivered in the initial HTML. A connected `WebSite`, `WebPage`, and `SoftwareApplication` graph describes the product; the guide adds `TechArticle` and a visible two-level breadcrumb. No invented review, rating, license, award, or site-search action is included. This is structured description, not a promise of app rich results. Google requires [truthful markup representative of visible content](https://developers.google.com/search/docs/appearance/structured-data/sd-policies); its [software application documentation](https://developers.google.com/search/docs/appearance/structured-data/software-app) describes the supported feature separately.

The XML sitemap lists only the two canonical content URLs. The error page, verification token and ZIP are excluded. `lastmod` records the date of a substantive page update; do not change it merely because the footer year or deployment changed. Google [ignores sitemap priority/changefreq and expects accurate modification dates](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

CSS, JavaScript, images and fonts remain crawlable. Visible text and ordinary links work without JavaScript. Local fonts, explicit image dimensions, responsive layouts and deferred scripting support page experience without third-party analytics. Browser and Lighthouse checks are laboratory evidence; they do not establish real-user Core Web Vitals. Google's [page-experience guidance](https://developers.google.com/search/docs/appearance/page-experience) recommends the broader user experience rather than a perfect score alone.

## Repeatable validation

No package installation is needed:

```bash
python3 scripts/check_seo.py
```

The script checks the crawlable local HTML, unique metadata, canonicals, headings, original verification token, connected JSON-LD, images and CSS assets, local links and anchors, robots/sitemap consistency, real ZIP, and intended Vercel redirect/download configuration. It exits nonzero on a failed requirement.

After the production deployment:

```bash
python3 scripts/check_seo.py --live
```

The live check also verifies public HTTP status, current page/robots/sitemap bytes, absence of index-blocking page headers, the canonical redirect, downloadable current ZIP and its headers, and a real HTTP 404 for unknown paths. A local Python HTTP server cannot apply `vercel.json`; confirm those host-specific behaviors on Vercel after deployment.

## Search Console and ongoing work

1. Confirm the deployed homepage and guide return HTTP 200 before requesting indexing. Run the live check.
2. Verify the actual domain in Google Search Console using the owner's existing verification setup. A token in the source does not itself prove the account has completed verification.
3. Submit `https://reactor-web-seven.vercel.app/sitemap.xml`. Use URL Inspection for the homepage and guide, then request recrawling if appropriate. A sitemap is a discovery hint, not a guarantee.
4. Use Google's Rich Results Test to review the deployed structured data. Do not create ratings or reviews just to satisfy a suggested field.
5. Review Search Console indexing, selected canonicals, search queries, clicks and impressions over subsequent weeks. Compare equivalent periods; ranking changes are not instantaneous.
6. Add real, permission-cleared demonstrations, measured quality comparisons and fixes for genuine user questions when available. Keep platform support and setup instructions aligned with the downloadable application. Earn relevant links through useful releases and documentation; do not buy links or mass-produce keyword pages.

Cache settings follow [Vercel’s cache-control documentation](https://vercel.com/docs/caching/cache-control-headers). Official deployment references: [Vercel static configuration](https://vercel.com/docs/project-configuration/vercel-json), [static build settings](https://vercel.com/docs/builds/configure-a-build). Canonical strategy follows Google's [duplicate URL guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls).

## Verified production release — 2026-10-31

Commit `7a34a01` deployed successfully to the existing production alias. The post-deployment `python3 scripts/check_seo.py --live` run passed **319/319 checks**, including the corrected canonical, live sitemap/robots, current page bytes, current ZIP bytes and headers, 308 homepage redirect, bounded asset cache rules, and a real branded HTTP 404.

Production Chromium checks covered 320, 390, 768 and 1440px layouts, platform tabs and exact clipboard commands, mobile navigation, FAQ, setup guide, and an actual browser ZIP download matching the current local archive. The extracted archive was launched using `./run.sh` with an existing environment and model weights; a real CPU swap produced a lossless gallery PNG matching its saved output, with zero pixel change in the unselected test region. A clean cross-platform dependency/model installation was not reproduced.

The production mobile Lighthouse 13.6 run measured **100 performance, 100 accessibility, 100 best practices, and 100 SEO**, with LCP 1.1s and CLS 0 in that laboratory run. Local desktop also scored 100 in all four categories. These are lab observations, not real-user Core Web Vitals, Google indexing confirmation or a search-ranking guarantee. Search Console sitemap submission and URL inspection still require the owner's Google account and were not performed.
