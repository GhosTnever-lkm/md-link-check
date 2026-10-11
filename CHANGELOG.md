# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `--exclude GLOB` (repeatable) to skip Markdown files, for example vendored docs.

## [0.1.1] - 2026-10-11

### Added

- CI now also runs the test suite on Windows (windows-latest), not only Ubuntu.


## [0.1.0] - 2026-10-11

### Added

- Offline check of relative Markdown links and heading anchors.
- Skips external URLs, fenced code blocks and inline code.
- Path-escape detection and percent-decoding of paths.

[Unreleased]: https://github.com/GhosTnever-lkm/md-link-check/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/GhosTnever-lkm/md-link-check/releases/tag/v0.1.0
