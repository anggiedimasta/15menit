# Changelog

All notable changes to **15menit** are recorded here. Entries under **[Unreleased]** are auto-filled from [conventional commits](https://www.conventionalcommits.org/) on push (see `scripts/release-sync.mjs`).

**Product context:** roadmap in [`backlog.md`](./backlog.md); requirements in [`prd.md`](./prd.md).

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the app uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) in `package.json` (patch bump on each pre-push release commit).

## [Unreleased]

<!-- changelog:sync-begin -->

<!-- changelog:sync-end -->

## [0.1.7] - 2026-06-19

<!-- changelog:sync-begin -->
### Fixed

- **api** — clip mock isochrone away from water ([10fe04e](https://github.com/anggiedimasta/15menit/commit/10fe04e))


<!-- changelog:sync-end -->

## [0.1.6] - 2026-06-19

<!-- changelog:sync-begin -->
### Changed

- **deploy** — add Valhalla service for Railway routing ([611bb83](https://github.com/anggiedimasta/15menit/commit/611bb83))


<!-- changelog:sync-end -->

## [0.1.5] - 2026-06-19

<!-- changelog:sync-begin -->
### Fixed

- **deploy** — serve static assets on Railway web ([4a0698d](https://github.com/anggiedimasta/15menit/commit/4a0698d))


<!-- changelog:sync-end -->

## [0.1.4] - 2026-06-19

<!-- changelog:sync-begin -->
### Fixed

- **deploy** — shell-expand PORT in API start command ([6aa23d5](https://github.com/anggiedimasta/15menit/commit/6aa23d5))


<!-- changelog:sync-end -->

## [0.1.3] - 2026-06-19

<!-- changelog:sync-begin -->
### Fixed

- **deploy** — point Railway API build to apps/api ([bf2f7a1](https://github.com/anggiedimasta/15menit/commit/bf2f7a1))


<!-- changelog:sync-end -->

## [0.1.2] - 2026-06-19

<!-- changelog:sync-begin -->
### Added

- **web** — glass panel contrast and search UX ([8f87cb3](https://github.com/anggiedimasta/15menit/commit/8f87cb3))

### Changed

- **web** — stabilize e2e playwright timeouts ([bc3b9f5](https://github.com/anggiedimasta/15menit/commit/bc3b9f5))
- **backlog** — sync integration and routing status ([19d1ba3](https://github.com/anggiedimasta/15menit/commit/19d1ba3))
- **docker** — add docker-up script and docs ([4b8fb29](https://github.com/anggiedimasta/15menit/commit/4b8fb29))

### Fixed

- **web** — share url sync and devtools SSR ([5bf5d73](https://github.com/anggiedimasta/15menit/commit/5bf5d73))
- **api** — transit gtfs path and routing config ([314bfd7](https://github.com/anggiedimasta/15menit/commit/314bfd7))
- **api** — postgis alembic and test isolation ([8383a5f](https://github.com/anggiedimasta/15menit/commit/8383a5f))


<!-- changelog:sync-end -->

## [0.1.1] - 2026-06-19

<!-- changelog:sync-begin -->
### Changed

- **deploy** — add Railway config for api and web ([f30c56e](https://github.com/anggiedimasta/15menit/commit/f30c56e))


<!-- changelog:sync-end -->

## [0.1.0] - 2026-06-20

<!-- changelog:sync-begin -->
### Added

- **docs** — initial PRD, backlog, changelog, artifact format

<!-- changelog:sync-end -->
