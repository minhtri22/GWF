# Public GitHub Pages Security Boundary

GitHub Pages is a public, static surface. It is never a credential boundary.

## Hard rule

The Pages bundle must not contain, accept, persist, or derive:

- API keys;
- GitHub tokens;
- OAuth access/refresh tokens;
- passwords;
- client secrets;
- private keys;
- Authorization bearer credentials.

This rule applies to source assets, generated static assets, build metadata, JavaScript, HTML forms, JSON configuration and browser storage.

## Current UAT mode

The current Pages site is `STATIC_UAT`.

It uses local browser state only for non-sensitive demo/UAT data. It is explicitly non-authoritative and must not mutate GWF backend state.

`localStorage` may contain only public UAT simulation state. It must never contain credentials or privileged session material.

## If Pages later connects to a real GWF backend

The browser must not receive provider API keys.

The allowed architecture is:

public Pages/browser
→ authenticated GWF backend/session boundary
→ governed plugin host / credential resolver
→ GitHub, model provider, or other external service

Provider credentials remain server-side or in an external secret manager.

For public browser authentication, use a backend-issued user/session mechanism appropriate to the deployment. Do not embed a reusable service credential in JavaScript or HTML.

## Build enforcement

`tools/check_public_site_secrets.py` scans both source and generated public assets.

The build fails on:

- known concrete secret formats;
- bearer credentials;
- private keys;
- password/credential input fields;
- credential-bearing localStorage keys;
- hard-coded credential object properties.

`tools/build_uat_site.py` executes the scanner before copying public assets and again after generating the final bundle.

`.github/workflows/public-pages-security.yml` independently enforces:

1. source scan;
2. public bundle build;
3. generated bundle scan;
4. negative security tests.

## Content Security Policy

The static UAT page constrains network access with a CSP whose `connect-src` is limited to `'self'`.

This is defense in depth, not a substitute for the no-credential rule.

## GitHub Actions secrets

GitHub Actions may use repository/environment secrets for server-side CI tasks when necessary, but those values must never be copied into `web/`, `dist/uat`, `build-meta.json`, or the `gh-pages` branch.

A successful deployment therefore means both:

- CI had enough authority to deploy;
- the deployed artifact itself contains no credential.
