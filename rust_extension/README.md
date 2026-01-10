# OpenGolfCoach Rust Extension

This directory contains the Rust-based Python extension module that powers the Home Assistant OpenGolfCoach integration.

## Architecture

The extension uses [PyO3](https://pyo3.rs/) to create Python bindings for the [OpenGolfCoach Rust core](https://github.com/OpenLaunchLabs/open-golf-coach). This provides:

- **High-performance trajectory simulation** with physics-based drag and lift models
- **Shot classification** using decision trees trained on professional data
- **Benchmark analysis** against PGA and LPGA cohorts
- **Zero-copy JSON I/O** for efficient data exchange with Python

## Building

### Prerequisites

- Rust toolchain (1.70+): `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Python 3.9+
- Maturin: `pip install maturin`

### Development Build

```bash
cd rust_extension
maturin develop --release
```

This compiles the Rust code and installs the extension into your active Python environment.

### Production Wheels

Build wheels for distribution:

```bash
# Build for current platform
maturin build --release

# Build for multiple platforms (requires Docker)
maturin build --release --manylinux 2_28
```

Wheels are output to `target/wheels/`.

## Usage

```python
import json
import opengolfcoach_rust

# Prepare shot data
shot = {
    "ball_speed_meters_per_second": 70.0,
    "vertical_launch_angle_degrees": 12.5,
    "horizontal_launch_angle_degrees": -2.5,
    "total_spin_rpm": 2500.0,
    "spin_axis_degrees": 10.0
}

# Calculate derived values
result_json = opengolfcoach_rust.calculate_derived_values(json.dumps(shot))
result = json.loads(result_json)

# Access results
print(f"Carry: {result['carry_distance_meters']:.1f}m")
print(f"Shot shape: {result['shot_name']}")
print(f"Smash factor: {result['smash_factor']:.2f}")
```

## CI/CD Integration

See `.github/workflows/build-wheels.yml` for automated wheel building across:
- Linux (x86_64, aarch64)
- macOS (x86_64, arm64)
- Windows (x86_64)

## Performance

Typical shot analysis completes in **< 1ms** compared to **10-50ms** for pure Python implementations, enabling real-time feedback during practice sessions.

## License

MIT - See LICENSE file in repository root.
