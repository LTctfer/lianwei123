#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Headless runner for the enhanced pollution tracing system.
Runs a minimal single-variant scenario and writes a compact summary
so we can inspect results even if stdout is not captured.
"""

import os
import json
import time
from datetime import datetime

# Use non-interactive backend for matplotlib to avoid GUI requirements
try:
    import matplotlib
    matplotlib.use('Agg')
except Exception:
    pass

from enhanced_pollution_tracing import (
    EnhancedPollutionTracingSystem,
    EnhancedScenarioConfig,
)


def main():
    os.makedirs('enhanced_results', exist_ok=True)
    summary_path = os.path.join('enhanced_results', 'headless_summary.json')
    log_path = os.path.join('enhanced_results', 'headless_run.log')

    start = time.time()
    log = []

    try:
        log.append('Init config')
        config = EnhancedScenarioConfig()
        system = EnhancedPollutionTracingSystem(config)

        log.append('Create scenario')
        true_source, meteo_data, sensor_data = system.create_scenario('headless_standard')

        log.append('Run inversion (standard only)')
        results = system.run_enhanced_inversion(sensor_data, meteo_data, algorithm_variants=['standard'])

        # Build compact summary
        std = results.get('standard')
        total_time = time.time() - start
        summary = {
            'timestamp': datetime.now().isoformat(),
            'scenario': 'headless_standard',
            'run_seconds': round(total_time, 2),
            'algorithms': list(results.keys()),
            'standard': {
                'position': [float(std.source_x), float(std.source_y), float(std.source_z)] if std else None,
                'emission_rate': float(std.emission_rate) if std else None,
                'objective_value': float(std.objective_value) if std else None,
                'position_error': float(std.position_error) if std else None,
                'emission_error': float(std.emission_error) if std else None,
                'computation_time': float(std.computation_time) if std else None,
            },
            'log': log,
        }

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log))

    except Exception as e:
        total_time = time.time() - start
        error_summary = {
            'timestamp': datetime.now().isoformat(),
            'scenario': 'headless_standard',
            'run_seconds': round(total_time, 2),
            'error': str(e),
            'log': log,
        }
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(error_summary, f, ensure_ascii=False, indent=2)
        raise


if __name__ == '__main__':
    main()

