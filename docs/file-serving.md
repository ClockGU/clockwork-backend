# File serving via nginx (X-Accel-Redirect)

## How it works

1. A client requests a download, e.g. `GET /documents/{document_id}/{document_type}`.
2. FastAPI authenticates and authorizes the request as usual.
3. If `SERVE_FILES_VIA_NGINX=true`, `file_response` (`api/utils.py`) returns an empty
   response with the download headers (`Content-Type`, `Content-Disposition`,
   `Cache-Control: private, no-store`, `X-Content-Type-Options: nosniff`) and
   `X-Accel-Redirect: /protected/<subdir>/<file_name>`.
4. nginx sees the header, looks up `/protected/...` in an `internal` location and streams
   the file from disk. Clients cannot request `/protected/...` directly.

`<subdir>` is `student_documents` or `prev_employments`, both under `settings.UPLOAD_DIR`
(`/app/uploads` in the container).

Endpoints using `file_response`: `GET /documents/{document_id}/{document_type}` and
`GET /clerk/prev_employments/{prev_employment_id}/download` (the latter since #167).

## Local development

Leave `SERVE_FILES_VIA_NGINX` unset (default `false`). FastAPI serves the files itself; no
nginx is needed.

## Server config (dokku)

nginx runs on the host, the app in a container. The uploads directory is already a dokku
storage mount, so host nginx can read the files from the host side of that mount.

Placeholders:
- `<app>`: the dokku app name.
- `<UPLOADS_HOST_PATH>`: host path of the mount whose container path is `/app/uploads`.
  Look it up with `dokku storage:report <app>` (or `dokku storage:list <app>`).

Create `/home/dokku/<app>/nginx.conf.d/protected.conf`:

```nginx
location /protected/ {
    internal;
    alias <UPLOADS_HOST_PATH>/;
}
```

Both the location and the alias end with `/`. dokku's default nginx template includes
`nginx.conf.d/*.conf` inside the app's `server` block (verify against your dokku version).

## Checklist

- [ ] The uploads directory is not publicly served: no other nginx `location`/`root`/`alias`
      points at `<UPLOADS_HOST_PATH>`.
- [ ] No directory listing: no `autoindex on` for `/protected/` (nginx default is off).
- [ ] The nginx worker user (usually `www-data`; check `user` in `/etc/nginx/nginx.conf`)
      can read files under `<UPLOADS_HOST_PATH>` and traverse its parent directories.
      Files are written by the container user `app` (uid/gid 32767).
      Test: `sudo -u www-data cat <UPLOADS_HOST_PATH>/student_documents/<some file>`.
- [ ] Rebuild and reload nginx: `dokku nginx:build-config <app>` (verify it reloads nginx on
      your dokku version; otherwise `sudo nginx -t && sudo systemctl reload nginx`).
- [ ] Enable the flag: `dokku config:set <app> SERVE_FILES_VIA_NGINX=true` (restarts the app).
- [ ] Smoke test: download a document as an authorized user; the file content arrives and the
      response headers include `Content-Disposition: attachment`.
- [ ] Direct access is blocked: `curl -i https://<domain>/protected/student_documents/<file>`
      returns `404`.

## Rollback

`dokku config:set <app> SERVE_FILES_VIA_NGINX=false`. FastAPI serves the files again; the
nginx location can stay in place.
