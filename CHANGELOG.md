# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-01-10

### Added
- **musllinux Wheel Builds**: Added support for Home Assistant OS (Alpine Linux)
  - Build musllinux wheels for x86_64 and aarch64 using zig cross-compilation
  - Auto-detect Home Assistant OS and download correct wheel type
  - Support for Raspberry Pi with aarch64 musllinux wheels
- **Automated Installation Script** (`scripts/install_rust_extension.sh`):
  - One-command installation for Rust extension
  - Auto-detects platform (Linux manylinux/musllinux, macOS, Windows)
  - Auto-detects Python version and Home Assistant environment
  - Downloads appropriate wheel from GitHub Releases
  - Verifies installation with import test

### Fixed
- **Script Regex Bug**: Fixed Python version detection causing grep errors
  - Moved print statements after variable capture to avoid stdout pollution
  - Added stderr suppression during version detection
  - Better error messages for Python version mismatches
- **Home Assistant OS Compatibility**: Resolved incompatibility with Alpine Linux
  - Previous manylinux wheels (glibc) didn't work on HA OS (musl libc)
  - Now builds and distributes musllinux wheels specifically for HA OS
  - Script automatically selects correct wheel based on platform detection

### Changed
- Updated CI/CD workflow to use ziglang for cross-compilation
- Enhanced README with musllinux wheel information and platform-specific notes
- Improved MIGRATION.md with automated installation script references

## [0.2.0] - 2026-01-10

### Added

- **Rust Core Integration**: Integrated official OpenGolfCoach Rust core via PyO3 bindings
- **PyO3 Extension Module**: Created `rust_extension/` directory with Maturin-based Python extension
  - `Cargo.toml`: Rust dependencies and project configuration
  - `src/lib.rs`: PyO3 bindings to OpenGolfCoach core
  - `pyproject.toml`: Maturin build system configuration
  - `README.md`: Extension-specific documentation
- **Rust Adapter Module**: Created `rust_adapter.py` to bridge Rust core with HA integration
- **Python Wrapper**: Created `rust_extension/python/opengolfcoach_wrapper/` for high-level Python API
- **GitHub Actions CI/CD**: Added `.github/workflows/build-wheels.yml` for automated wheel building
  - Builds for Linux (x86_64, aarch64)
  - Builds for macOS (x86_64, arm64)
  - Builds for Windows (x86_64)
  - Automatic PyPI publishing on tag
  - GitHub Releases integration
- **Package Configuration**: Added root-level `pyproject.toml` for pip installation support
- **Migration Guide**: Added `MIGRATION.md` with upgrade instructions
- **Changelog**: Added this `CHANGELOG.md` file
- **Documentation**: Comprehensive README updates with:
  - Architecture overview (Rust core + Python glue layers)
  - Installation instructions for Rust extension
  - Development and build instructions
  - Performance benchmarks (15-60x speedup)
  - Project structure diagram
  - Troubleshooting guide

### Changed

- **Performance**: Shot analysis now completes in <1ms (vs 15-60ms in v0.1.0)
  - Trajectory simulation: 10-50x faster
  - Shot classification: 10-50x faster
  - Full analysis: 15-60x faster
- **sensor.py**: Updated import to use `rust_adapter.analyze_shot()` instead of `analysis.analyze_shot()`
- **Import Path**: Changed `from .benchmarks` to `from .analysis.benchmarks` in sensor.py
- **Version**: Bumped to 0.2.0 in `manifest.json`
- **.gitignore**: Added Rust-specific entries (target/, Cargo.lock, *.rs.bk, *.so, wheels/)
- **Analysis Version**: Metadata now reports `"0.2.0-rust"` and includes `rust_enabled` flag

### Removed

Removed Python modules that are now handled by Rust core:

- `analysis/analysis.py` → Replaced by `rust_adapter.py`
- `analysis/shot_classifier.py` → Rust core handles classification
- `analysis/trajectory.py` → Rust core handles trajectory simulation
- `analysis/trajectory_analysis.py` → Rust core handles trajectory analysis
- `analysis/clubhead_data.py` → Rust core estimates club data
- `analysis/vector.py` → No longer needed
- `analysis/unit_conversions.py` → Rust core handles conversions
- `analysis/self_check.py` → Unused, removed

### Kept

Python modules preserved because they're HA-specific:

- `analysis/benchmarks.py` → PGA/LPGA percentile comparisons (uses local JSON data)
- `analysis/coaching.py` → Coaching tips lookup (uses local tips.json)
- `analysis/utils.py` → JSON loading utilities

### Technical Details

#### Rust Integration Architecture

```
NOVA Device → nova_by_openlaunch → coordinator → sensor.py
                                                    ↓
                                            rust_adapter.py
                                                    ↓
                                            opengolfcoach_rust (PyO3 extension)
                                                    ↓
                                            OpenGolfCoach Rust core
```

#### Data Flow

1. **Input**: Raw shot data from NOVA (ball speed, launch angles, spin)
2. **Rust Processing**:
   - Trajectory simulation with physics models
   - Shot shape classification
   - Club speed/smash factor estimation
3. **Python Post-processing**:
   - Benchmark comparisons (uses local benchmarks.json)
   - Coaching recommendations (uses local tips.json)
4. **Output**: Comprehensive analysis dict for HA sensors

#### Build System

- **Rust**: Cargo with PyO3 dependencies
- **Python Bindings**: Maturin for building wheels
- **CI/CD**: GitHub Actions for multi-platform builds
- **Distribution**: GitHub Releases + optional PyPI

### Breaking Changes

**Installation Only**: The Rust extension (`opengolfcoach-rust`) must be installed separately. See `MIGRATION.md` for upgrade instructions.

**API**: No breaking changes - all sensor entities and attributes remain compatible.

### Upgrade Instructions

See `MIGRATION.md` for detailed upgrade steps.

### Known Issues

- Rust extension must be compiled/installed separately (not automatic via HACS)
- First-time installation requires manual wheel installation
- Some platforms may need to build from source if pre-built wheels unavailable

### Future Plans

- [ ] Publish `opengolfcoach-rust` to PyPI for easier installation
- [ ] Add automated wheel building for more platforms
- [ ] Explore making Rust extension optional with Python fallback
- [ ] Add integration tests for Rust ↔ Python boundary
- [ ] Add Rust extension version to integration diagnostics

## [0.1.0] - 2025-12-XX

### Added

- Initial release with pure Python implementation
- Shot analysis using custom Python physics models
- Shot classification with decision trees
- Benchmark comparisons against PGA/LPGA cohorts
- Coaching recommendations system
- Integration with NOVA by Open Launch
- HACS support
- Configuration flow

### Features

- `sensor.open_golf_coach_last_shot` - Primary rich sensor
- 6 compatibility sensors for GolfCoachCards
- Real-time shot analysis from NOVA data stream
- Handedness normalization (RH/LH)
- Percentile band calculations
- JSON-based data files for benchmarks and tips

---

## Legend

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features that will be removed in future
- **Removed**: Features removed in this release
- **Fixed**: Bug fixes
- **Security**: Security-related changes
