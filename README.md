# Home Assistant OpenGolfCoach (for NOVA)

This repository provides a Home Assistant integration that adds an Open Golf Coach analysis layer on top of the NOVA shot data stream. It is designed to be installed via HACS as a custom repository.

This project is a fork of the NOVA Home Assistant integration for the device ingest layer, and it adds a separate Open Golf Coach integration for analysis and coaching.

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

1) Open HACS in Home Assistant
2) Go to **Integrations**
3) Open the menu (top right) and select **Custom repositories**
4) Add this repository URL:
   https://github.com/TaylorOpenLaunch/homeassistant-opengolfcoach
5) Select category: **Integration**
6) Install
7) Restart Home Assistant

After restart:
1) Go to **Settings -> Devices & services -> Add integration**
2) Add **NOVA by Open Launch** first and confirm it is receiving shots
3) Add **Open Golf Coach**
4) When prompted, select the existing NOVA entry to bind to

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
- If Open Golf Coach shows no updates, confirm NOVA is receiving shots first.
- Check Home Assistant logs for JSON parsing errors of benchmarks.json or tips.json.
- If shapes look mirrored, confirm handedness and sign convention normalization.

## License
See LICENSE in this repository.
