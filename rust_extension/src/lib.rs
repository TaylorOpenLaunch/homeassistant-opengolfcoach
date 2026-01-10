use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

/// Calculate derived golf shot values from measured data.
///
/// This function is the main entry point for the OpenGolfCoach analysis engine.
/// It accepts a JSON string containing measured shot data and returns a JSON
/// string with calculated trajectory, spin, and classification data.
///
/// # Arguments
///
/// * `json_input` - JSON string containing shot measurements. Required fields:
///   - ball_speed_meters_per_second: f64
///   - vertical_launch_angle_degrees: f64
///   Optional fields include horizontal_launch_angle_degrees, total_spin_rpm,
///   spin_axis_degrees, backspin_rpm, sidespin_rpm, and others.
///
/// # Returns
///
/// JSON string containing derived values including:
/// - carry_distance_meters
/// - total_distance_meters
/// - offline_distance_meters
/// - backspin_rpm / sidespin_rpm
/// - shot_name, shot_rank, shot_color_rgb
/// - club_speed_meters_per_second
/// - smash_factor
/// - and more (see API.md for complete schema)
///
/// # Errors
///
/// Returns PyValueError if:
/// - Input JSON is malformed
/// - Required fields are missing
/// - Calculation fails due to invalid physics parameters
///
/// # Example
///
/// ```python
/// import opengolfcoach_rust
/// import json
///
/// shot_data = {
///     "ball_speed_meters_per_second": 70.0,
///     "vertical_launch_angle_degrees": 12.5,
///     "horizontal_launch_angle_degrees": 0.0,
///     "total_spin_rpm": 2500.0,
///     "spin_axis_degrees": 0.0
/// }
///
/// result_json = opengolfcoach_rust.calculate_derived_values(json.dumps(shot_data))
/// result = json.loads(result_json)
/// print(f"Carry distance: {result['carry_distance_meters']:.1f}m")
/// ```
#[pyfunction]
fn calculate_derived_values(json_input: &str) -> PyResult<String> {
    // Call the underlying Rust core function
    opengolfcoach::calculate_derived_values(json_input)
        .map_err(|e| PyValueError::new_err(format!("Calculation failed: {}", e)))
}

/// OpenGolfCoach Rust Extension Module
///
/// This module provides Python bindings to the OpenGolfCoach Rust core library,
/// which performs high-performance golf shot analysis including:
///
/// - Trajectory simulation with drag and lift models
/// - Shot shape classification (draw, fade, slice, hook, etc.)
/// - Benchmark comparison against PGA/LPGA cohorts
/// - Club speed and smash factor estimation
/// - Coaching recommendations based on shot shape
///
/// The module exposes a single function `calculate_derived_values` that accepts
/// JSON input and returns JSON output for maximum flexibility and compatibility
/// with the Home Assistant integration layer.
#[pymodule]
fn opengolfcoach_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_derived_values, m)?)?;
    Ok(())
}
