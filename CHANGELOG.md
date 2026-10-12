# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.2] - 2026-10-13

### Added

- Scan `.markdown` files as well as `.md` files.
- Resolve Setext heading anchors and honor opening/closing fence lengths.
- Add install instructions, release badges, pinned CI actions, and tagged wheel/sdist releases with SHA-256 checksums.
- Add regression coverage that ties the CLI version to package metadata.

### Fixed

- Avoid false link and heading findings inside code blocks whose closing fence is shorter than the opening fence.

## [0.1.1] - 2026-10-11

### Added

- CI now also runs the test suite on Windows (windows-latest), not only Ubuntu.
- `--exclude GLOB` (repeatable) to skip Markdown files, for example vendored docs.


## [0.1.0] - 2026-10-11

### Added

- Offline check of relative Markdown links and heading anchors.
- Skips external URLs, fenced code blocks and inline code.
- Path-escape detection and percent-decoding of paths.

[Unreleased]: https://github.com/GhosTnever-lkm/md-link-check/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/GhosTnever-lkm/md-link-check/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/GhosTnever-lkm/md-link-check/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/GhosTnever-lkm/md-link-check/releases/tag/v0.1.0
