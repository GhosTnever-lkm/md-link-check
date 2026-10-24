# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.5] - 2026-10-25

### Fixed

- Ignore headings and links inside HTML comments when scanning rendered Markdown, without treating comment markers in fenced or inline code as comments.

### Added

- Add regression coverage for multiline comments, comment markers inside code fences, and inline code spans.

## [0.1.4] - 2026-10-21

### Fixed

- Allocate unique heading anchors across both explicit numeric suffixes and generated duplicate-heading suffixes.
- Share collision tracking between ATX and Setext headings so links to disambiguated anchors resolve correctly.

### Added

- Five regression tests for heading ID collisions and links to their resolved anchors.

## [0.1.3] - 2026-10-21

### Fixed

- Ignore URL query strings when resolving relative file links, while still checking the target file and heading fragment.
- Resolve query-only links against the current Markdown document.
- Preserve percent-encoded `?` and `#` characters in filenames by separating URL syntax before decoding.

### Added

- Seven regression tests for query strings, query-only links, encoded filenames, and missing file/anchor diagnostics.

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

[Unreleased]: https://github.com/GhosTnever-lkm/md-link-check/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/GhosTnever-lkm/md-link-check/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/GhosTnever-lkm/md-link-check/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/GhosTnever-lkm/md-link-check/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/GhosTnever-lkm/md-link-check/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/GhosTnever-lkm/md-link-check/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/GhosTnever-lkm/md-link-check/releases/tag/v0.1.0
