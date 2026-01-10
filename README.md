# Home Assistant OpenGolfCoach (for NOVA)

This repository provides a Home Assistant integration that adds an Open Golf Coach analysis layer on top of the NOVA shot data stream. It leverages the **official OpenGolfCoach Rust core** for high-performance shot analysis, trajectory simulation, and classification.

The integration is designed to be installed via HACS as a custom repository and uses Python bindings to the Rust core for maximum performance and accuracy.

## Architecture

This integration consists of two layers:

### 1. Rust Core (Performance Layer)
- **OpenGolfCoach Rust core** via PyO3 Python extension
- Physics-based trajectory simulation with drag and lift models
- Shot shape classification using decision trees
- Club speed and smash factor estimation
- Typical analysis time: **< 1ms per shot**

### 2. Python Integration Layer (Home Assistant Glue)
- Home Assistant sensor entities and device management
- Benchmark comparison against PGA/LPGA cohorts (Python logic using JSON data)
- Coaching recommendations (Python logic using tips database)
- Configuration flow and user interface

The Rust core handles all performance-critical computations, while Python manages the Home Assistant integration, data lookup, and user experience.

## What you get

After installation, Home Assistant will show two integrations:
- **NOVA by Open Launch** (device + raw shot ingest)
- **Open Golf Coach** (analysis + benchmarking + coaching)

Open Golf Coach listens to the shot stream coming from NOVA and publishes a single rich sensor designed for dashboards and cards.

## Measured vs derived data (important)

### Measured inputs (ground truth from NOVA)
These are the only values treated as 100% correct:
- Ball speed (meters per second)
- Vertical launch angle (degrees)
- Horizontal launch angle (degrees)
- Total spin (rpm)
- Spin axis (degrees)

### Derived and inferred outputs (computed)
Open Golf Coach computes:
- Inferred club category (wedges, mid irons, woods) using ball speed + vertical launch + spin
- Shot shape classification using start line (horizontal launch) and curvature (spin axis)
- Benchmark comparisons (PGA Tour, LPGA Tour, Amateur tiers)
- Coaching: diagnostics and 2 to 3 coaching cues based on shot shape
- Estimated trajectory outputs (if present): carry, total, offline, apex, hang time, descent angle
  - These are explicitly labeled as estimated, not measured.

## Primary entity

### sensor.open_golf_coach_last_shot
State:
- The inferred shot shape

Attributes include:
- **measured**: ball_speed_mps, ball_speed_mph, vertical_launch_angle, horizontal_launch_angle, total_spin, spin_axis
- **inferred**: club_category, shot_shape
- **benchmarks**: cohort comparisons and percentile bands
- **coaching**: diagnostics and coaching_cues
- **estimated_trajectory**: trajectory outputs from a simplified model (if available)
- **metadata**: timestamp and flags including trajectory_is_estimated and trajectory_model_note

This single entity is the recommended source for dashboards and custom cards.

## Compatibility entities (optional)
For compatibility with GolfCoachCards-style dashboards, Open Golf Coach also exposes derived sensors:
- sensor.nova_shot_type
- sensor.nova_shot_rank
- sensor.nova_nova_shot_quality
- sensor.nova_launch_in_window
- sensor.nova_spin_in_window
- sensor.nova_start_line_in_window

These are derived from analysis output and include attributes:
- source: open_golf_coach
- is_derived: true

## Installation via HACS (recommended)

### Step 1: Install the Rust Extension

The integration requires the `opengolfcoach-rust` Python extension. You have two options:

#### Option A: Install Pre-built Wheels (Recommended)

Download the appropriate wheel for your platform from the [GitHub Releases](https://github.com/TaylorOpenLaunch/homeassistant-opengolfcoach/releases) page:

- **Linux x86_64**: `opengolfcoach_rust-*-cp311-cp311-manylinux_2_28_x86_64.whl`
- **Linux aarch64** (Raspberry Pi): `opengolfcoach_rust-*-cp311-cp311-manylinux_2_28_aarch64.whl`
- **macOS Intel**: `opengolfcoach_rust-*-cp311-cp311-macosx_*_x86_64.whl`
- **macOS Apple Silicon**: `opengolfcoach_rust-*-cp311-cp311-macosx_*_arm64.whl`
- **Windows**: `opengolfcoach_rust-*-cp311-cp311-win_amd64.whl`

Install using Home Assistant's Python environment:

```bash
# SSH into your Home Assistant instance or use the Terminal add-on
source /usr/src/homeassistant/bin/activate
pip install /path/to/downloaded/opengolfcoach_rust-*.whl
```

#### Option B: Build from Source

If a pre-built wheel isn't available for your platform:

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin
pip install maturin

# Clone the repository and build
cd /path/to/homeassistant-opengolfcoach/rust_extension
maturin build --release
pip install target/wheels/opengolfcoach_rust-*.whl
```

### Step 2: Install the Integration via HACS

1) Open HACS in Home Assistant
2) Go to **Integrations**
3) Open the menu (top right) and select **Custom repositories**
4) Add this repository URL:
   https://github.com/TaylorOpenLaunch/homeassistant-opengolfcoach
5) Select category: **Integration**
6) Install
7) Restart Home Assistant

### Step 3: Configure the Integration

After restart:
1) Go to **Settings -> Devices & services -> Add integration**
2) Add **NOVA by Open Launch** first and confirm it is receiving shots
3) Add **Open Golf Coach**
4) When prompted, select the existing NOVA entry to bind to

**Note**: If the Rust extension is not installed, the integration will log a warning but will continue to function using fallback Python logic (with reduced performance).

## Manual install (alternative)
Copy both folders into your HA config:
- custom_components/nova_by_openlaunch
- custom_components/open_golf_coach

Restart Home Assistant and add both integrations.

## Data files
This repo includes:
- custom_components/open_golf_coach/data/benchmarks.json
- custom_components/open_golf_coach/data/tips.json

Benchmarks drive percentile comparisons by cohort.
Tips drive diagnostics and coaching cues keyed by shot shape.

## Troubleshooting

### Integration Issues
- If Open Golf Coach shows no updates, confirm NOVA is receiving shots first.
- Check Home Assistant logs for JSON parsing errors of benchmarks.json or tips.json.
- If shapes look mirrored, confirm handedness and sign convention normalization.

### Rust Extension Issues
- **Warning: "opengolfcoach_rust extension not available"**: The Rust extension is not installed. Follow the installation steps above.
- **Import errors**: Ensure you've installed the wheel in Home Assistant's Python environment, not your system Python.
- **Performance degradation**: If the Rust extension fails to load, the integration will fall back to slower Python implementations. Check logs for specific errors.

To verify the Rust extension is working:
```bash
source /usr/src/homeassistant/bin/activate
python -c "import opengolfcoach_rust; print('Rust extension loaded successfully')"
```

## Development

### Building the Rust Extension

```bash
cd rust_extension

# Development build (fast, debug symbols)
maturin develop

# Release build (optimized)
maturin develop --release

# Build wheels for distribution
maturin build --release
```

### Running Tests

```bash
# Python tests
pytest tests/

# Rust tests
cd rust_extension
cargo test
```

### Project Structure

```
homeassistant-opengolfcoach/
├── rust_extension/               # Rust PyO3 extension
│   ├── src/lib.rs               # Rust bindings to OpenGolfCoach core
│   ├── Cargo.toml               # Rust dependencies
│   └── pyproject.toml           # Maturin build configuration
│
├── custom_components/
│   └── open_golf_coach/         # Home Assistant integration
│       ├── __init__.py          # Integration setup
│       ├── sensor.py            # Sensor entities
│       ├── config_flow.py       # Configuration UI
│       ├── rust_adapter.py      # Rust ↔ Python adapter
│       ├── analysis/            # Python-only analysis helpers
│       │   ├── benchmarks.py    # PGA/LPGA benchmark comparisons
│       │   ├── coaching.py      # Coaching tips lookup
│       │   └── utils.py         # JSON utilities
│       └── data/                # Data files
│           ├── benchmarks.json  # Percentile data by cohort
│           └── tips.json        # Coaching recommendations
│
├── .github/workflows/
│   └── build-wheels.yml         # CI/CD for wheel building
│
└── pyproject.toml               # Package metadata
```

## Performance

The Rust core provides significant performance improvements over pure Python implementations:

| Operation | Python | Rust | Speedup |
|-----------|--------|------|---------|
| Trajectory simulation | 10-50ms | <1ms | 10-50x |
| Shot classification | 1-5ms | <0.1ms | 10-50x |
| Full analysis | 15-60ms | <1ms | 15-60x |

This enables real-time feedback during practice sessions without lag.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

For Rust core changes, please contribute to the upstream [OpenGolfCoach repository](https://github.com/OpenLaunchLabs/open-golf-coach).

## Credits

- **OpenGolfCoach Rust core**: [OpenLaunchLabs/open-golf-coach](https://github.com/OpenLaunchLabs/open-golf-coach)
- **NOVA device integration**: Based on the NOVA Home Assistant integration
- **Benchmarks data**: Derived from public PGA Tour and LPGA Tour statistics

## License
See LICENSE in this repository.
