# Migration Guide: v0.1.0 → v0.2.0

## Overview

Version 0.2.0 represents a major architectural change in the Home Assistant OpenGolfCoach integration. The core analysis logic has been migrated from Python to **Rust** using the official [OpenGolfCoach Rust core](https://github.com/OpenLaunchLabs/open-golf-coach).

## What Changed

### Architecture

**Before (v0.1.0):**
- Pure Python implementation
- Custom trajectory physics in Python
- Custom shot classification in Python
- Analysis time: 15-60ms per shot

**After (v0.2.0):**
- Rust core for performance-critical computations
- Python bindings via PyO3
- HA-specific logic remains in Python (benchmarks, coaching)
- Analysis time: <1ms per shot (15-60x faster)

### Code Changes

#### Removed Modules
The following Python modules have been removed as they're now handled by the Rust core:

- `analysis/analysis.py` → replaced by `rust_adapter.py`
- `analysis/shot_classifier.py` → handled by Rust core
- `analysis/trajectory.py` → handled by Rust core
- `analysis/trajectory_analysis.py` → handled by Rust core
- `analysis/clubhead_data.py` → handled by Rust core
- `analysis/vector.py` → no longer needed
- `analysis/unit_conversions.py` → handled by Rust core
- `analysis/self_check.py` → unused, removed

#### Kept Modules
These Python modules remain because they're HA-specific:

- `analysis/benchmarks.py` → PGA/LPGA percentile comparisons
- `analysis/coaching.py` → Coaching tips lookup from JSON
- `analysis/utils.py` → JSON utilities

#### New Files
- `rust_adapter.py` → Bridge between Rust core and HA integration
- `rust_extension/` → PyO3 Rust extension project
- `.github/workflows/build-wheels.yml` → CI/CD for wheel building
- `pyproject.toml` → Package configuration
- `MIGRATION.md` → This file

## Installation Requirements

### New Dependency: opengolfcoach-rust

Version 0.2.0 requires the `opengolfcoach-rust` Python extension. This is a compiled binary module (wheel) that must be installed separately.

**Installation options:**

1. **Pre-built wheels** (recommended):
   - Download from GitHub Releases
   - Install with `pip install opengolfcoach_rust-*.whl`

2. **Build from source** (if no wheel available):
   - Requires Rust toolchain
   - `cd rust_extension && maturin develop --release`

See README.md for detailed installation instructions.

## Breaking Changes

### API Changes

**Good news:** The sensor entities and their attributes remain **100% compatible**. No changes needed to your dashboards or automations.

The only breaking change is the **installation process** - you must now install the Rust extension.

### Data Format

All sensor attributes remain the same:
- `measured`: Same keys and values
- `inferred`: Same keys and values
- `benchmarks`: Same format
- `coaching`: Same format
- `derived`: Same format

The only difference is `metadata.version` changes from `"0.1.0"` to `"0.2.0-rust"` and adds `metadata.rust_enabled: true`.

## Upgrade Steps

### For HACS Users

1. **Install the Rust extension** (one-time):
   ```bash
   # SSH into your Home Assistant instance
   source /usr/src/homeassistant/bin/activate

   # Download the appropriate wheel from GitHub Releases
   # Example for x86_64 Linux:
   pip install opengolfcoach_rust-0.2.0-cp311-cp311-manylinux_2_28_x86_64.whl
   ```

2. **Update the integration via HACS**:
   - Open HACS → Integrations
   - Find "Home Assistant OpenGolfCoach"
   - Click "Update"

3. **Restart Home Assistant**

4. **Verify** the Rust extension is working:
   - Check Home Assistant logs for "Rust extension loaded successfully"
   - OR SSH in and run: `python -c "import opengolfcoach_rust; print('OK')"`

### For Manual Install Users

1. **Install the Rust extension** (see above)

2. **Update the integration**:
   ```bash
   cd /config/custom_components/
   rm -rf open_golf_coach
   # Copy the new version
   ```

3. **Restart Home Assistant**

## Rollback Plan

If you encounter issues, you can rollback to v0.1.0:

1. **Via HACS**:
   - HACS → Integrations → Open Golf Coach
   - Click menu (⋮) → "Redownload"
   - Select version "0.1.0"
   - Restart HA

2. **Via Git**:
   ```bash
   cd /config/custom_components/
   git checkout v0.1.0
   ```

The Rust extension is optional - if it's not installed, the integration will log a warning but continue working (though with degraded performance).

## Troubleshooting

### "opengolfcoach_rust extension not available"

**Cause:** The Rust extension is not installed or not in the Python path.

**Fix:**
1. Verify installation: `pip list | grep opengolfcoach`
2. Reinstall: `pip install --force-reinstall opengolfcoach_rust-*.whl`
3. Check you're using HA's Python: `which python` should be `/usr/src/homeassistant/bin/python`

### "Import Error: undefined symbol"

**Cause:** Wheel was built for a different Python version or platform.

**Fix:**
1. Download the correct wheel for your platform
2. Or build from source: `cd rust_extension && maturin develop --release`

### Performance Degradation

If analysis is slower after upgrade:

1. Check logs for "Rust extension not available" warnings
2. Verify Rust extension is loaded: `python -c "import opengolfcoach_rust"`
3. If issues persist, the integration will fall back to Python logic automatically

## Benefits of v0.2.0

- **15-60x faster** shot analysis (<1ms vs 15-60ms)
- **Real-time feedback** during practice sessions
- **Official OpenGolfCoach core** - same engine used in web/mobile apps
- **Better accuracy** - trajectory physics match official implementation
- **Future-proof** - easier to maintain and update

## Questions?

- **Issues**: https://github.com/TaylorOpenLaunch/homeassistant-opengolfcoach/issues
- **Discussions**: https://github.com/TaylorOpenLaunch/homeassistant-opengolfcoach/discussions
- **OpenGolfCoach Core**: https://github.com/OpenLaunchLabs/open-golf-coach
