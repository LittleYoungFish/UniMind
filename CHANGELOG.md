# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-04-15

### Added

- Added online visualization of the project and "interactive" mode for the script.
- Added phases for documentation, code execution and testing.
- Added multimodal input support (text file, image, etc.) as demand.

### Changed

- Changed the "time" field in the output to "started_at" and "finished_at" for clarity.

### Fixed

- Fixed a bug where the "get_code_structure" tool produced incorrect OpenAI API schema.

## [0.0.3] - 2025-04-05

### Added

- Added demand analysis agent, developing supervision agent and quality assurance agent.
- Added static analysis tool and code structure extractor tool.
- Added development summary view.
- Added error reporting view.

### Changed

- Changed the default retry interval and backoff strategy.

## [0.0.2] - 2025-04-02

### Added

- Added docker support for running the script in a container.

### Changed

- Changed output directory cleanup logic, now it will not remove the directory itself.

### Fixed

- Fixed a bug where the script would crash if no OPENAI_API_KEY was set.

## [0.0.1] - 2025-03-31

### Added

- Initial release of the project.
