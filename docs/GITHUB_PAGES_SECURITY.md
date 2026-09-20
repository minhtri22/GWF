# GitHub Pages Security Boundary

GitHub Pages for GWF is a **public static UAT surface**. It is not an authenticated backend and it is not a credential-bearing client.

## Hard rule

The Pages artifact must never contain or persist:

- API keys;
- GitHub PATs;
- access or refresh tokens;
- client secrets;
- passwords;
- Authorization credentials;
- any other reusable secret.

This applies to committed HTML/JavaScript/JSON, generated build artifacts, browser localStorage, and user-entered UAT YAML.

## Enforcement

1. `tools/build_uat_site.py` scans the final static artifact and fails the build on secret fields or recognized token patterns.
2. `web/app.js` rejects secret-bearing YAML before localStorage persistence.
3. Existing local UAT domain revisions containing secret-like material are removed from localStorage at startup.
4. Build metadata declares `secret_storage_allowed=false` and `credential_transport=NONE`.
5. GitHub Pages remains non-authoritative. Real GitHub/API credentials are resolved server-side or host-side through the GWF plugin/credential resolver boundary.

## Architecture

```
GitHub Pages
  public static UI
  no credentials
  no authoritative mutation
        |
        | display/demo only
        v
GWF backend / host runtime
  authentication
  authority
  plugin connection refs
  external credential resolver
        |
        v
GitHub / external APIs
```

If a future live UI is introduced, it must authenticate to a backend using an appropriate user/session mechanism. Long-lived provider API keys must still never be shipped to the browser.
