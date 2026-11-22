"""Collect the completed S2 campaign's reviewed GitHub publication allowlist.

Original experiment files are never rewritten. Large raw records stay local.
Run from any directory; the selection is bound to the completed November22 run.
"""
import csv
import hashlib
import json
from pathlib import Path
import subprocess

LOCAL = Path(__file__).resolve().parent
REPO = Path(subprocess.check_output(['git', '-C', str(LOCAL), 'rev-parse', '--show-toplevel'], text=True).strip())
RUN = '20261114-235334-endpoint-multiseed-mechanisms'
LOG = LOCAL / 'logs' / RUN
OUT = LOCAL / 'results' / RUN
EXPORT = LOCAL / 'exports' / '20261122-key-results'


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def collect():
    assert load(LOG / 'completion_audit.json')['status'] == 'completed'
    assert load(LOG / 'pipeline' / 'exit.json')['returncode'] == 0
    EXPORT.mkdir(parents=True, exist_ok=True)
    selected = set()

    def add(path):
        assert path.is_file(), path
        assert path.stat().st_size < 8 * 2**20, ('unexpectedly large publication file', str(path))
        selected.add(path)

    def matches(root, pattern):
        for path in root.glob(pattern):
            if path.is_file():
                add(path)

    # Runners and mathematical definitions retain their original paths and bytes.
    add(REPO / 'README.md')
    add(REPO / '.gitignore')
    matches(LOCAL, '*.py')
    for name in ['README.md', 'GITHUB_EXPERIMENTS.md', 'FORMAL_RUNNER.md', 'PILOT_ALPHA_RUNNER.md']:
        add(LOCAL / name)
    for pattern in ['20261113-*.md', '20261114-*.md', '20261118-*.md']:
        matches(LOCAL, pattern)
    for name in ['README.md', 'experiment_manifest.json', 'generate_manifest.py', 'protocol_checks.py']:
        add(LOCAL.parent / name)
    matches(LOG / 'code', '*.py')
    matches(LOG / 'code', '*.json')
    matches(LOG, '*.py')
    for name in ['preregistration.json', 'campaign_code_frozen_before_test.json', 'endpoint_source_frozen.json',
                 'mechanism_design_frozen.json', 'endpoint_verification.json', 'mechanism_verification.json',
                 'statistics_verification.json', 'completion_audit.json', 'pipeline_status.json',
                 'report_summary.json', 'environment-freeze.txt', 'seed17-endpoint.png', 'seed17-endpoint.pdf',
                 'attempt_locations.json', 'STARTED.md']:
        add(LOG / name)
    # Actual stage commands, exit codes and moderate-size stdout/stderr are useful evidence.
    for directory in sorted(LOG.iterdir()):
        if directory.is_dir() and (directory / 'launch.json').exists():
            for name in ['launch.json', 'exit.json', 'stdout.log', 'stderr.log']:
                if (directory / name).is_file():
                    add(directory / name)
    matches(LOG / 'core_snapshot', '*')
    recovery = LOG / 'recovery-20261118-rate-recovery'
    matches(recovery, '*.py')
    for name in ['recovery.json', 'environment_and_sources.json', 'quarantine_before.json',
                 'partial_shards_comparison.json', 'probe_vram.json', 'probe_stages_graphs.json',
                 'raw_cpu_comparison.json', 'training_cpu_gpu_rounding.json']:
        add(recovery / name)
    for pattern in ['gpu3-health/*.json', 'gpu3-health/channel/*.json', 'stage-health/*/probe_vram.json']:
        matches(recovery, pattern)
    for name in ['20261117-interruption/recovery.json', '20261118-nonfinite/captured_nonfinite.json',
                 '20261118-nonfinite/channel_probe.json']:
        add(LOG / ('recovery-' + name))
    matches(OUT, '*.json')
    matches(OUT, '*.sha256')
    # Point and shard aggregate statistics are preserved; per-frame npz remain local.
    matches(OUT / 'test', '**/*.json')
    matches(OUT / 'pilot', '**/*.json')

    registry_entries = []
    points = []
    thresholds = []
    train_rows = []
    for path in sorted(OUT.glob('*_registry.json')):
        registry = load(path)
        for cid, methods in registry['configs'].items():
            for spec in methods:
                if 'checkpoint' not in spec:
                    continue
                checkpoint = Path(spec['checkpoint'])
                assert checkpoint.is_relative_to(LOCAL), checkpoint
                assert digest(checkpoint) == spec['checkpoint_sha256']
                add(checkpoint)
                add(checkpoint.with_suffix('.pt.sha256'))
                registry_entries.append({**spec, 'config_id': cid,
                                         'checkpoint_repository_path': str(checkpoint.relative_to(REPO))})
    assert len(registry_entries) == 24
    assert len({v['checkpoint_repository_path'] for v in registry_entries}) == 24
    for spec in registry_entries:
        root = REPO / Path(spec['checkpoint_repository_path']).parent.parent
        for name in ['summary.json', 'contract.json', 'checkpoint_selection.json', 'independent_audit.json',
                     'validation/top2_frozen.json']:
            if (root / name).exists():
                add(root / name)
        summary = load(root / 'summary.json')
        assert summary['status'] == 'formal_50k_completed'
        assert summary['steps'] == 50000 and summary['observations'] == 3200000
        train_rows.append({'config_id': spec['config_id'], 'kind': spec['kind'], 'seed': spec['seed'],
                           'steps': summary['steps'], 'selected_step': spec['step'],
                           'mean_step_seconds': summary['mean_step_seconds'],
                           'peak_allocated_bytes': summary['peak_allocated_bytes'],
                           'peak_reserved_bytes': summary['peak_reserved_bytes'],
                           'initial_validation_bce': summary['initial_validation_mean_bce'],
                           'final_periodic_validation_bce': summary['latest_validation_mean_bce'],
                           'selected_validation_bce': summary['checkpoint_selection']['selected']['mean_information_bce'],
                           'gradient_clip_fraction': summary['gradient_clip_fraction'],
                           'checkpoint_repository_path': spec['checkpoint_repository_path'],
                           'checkpoint_sha256': spec['checkpoint_sha256']})
    for path in sorted((OUT / 'test').glob('*/summary.json')):
        summary = load(path)
        audit = load(path.parent / 'audit_summary.json')
        assert summary['status'] == audit['status'] == 'passed'
        assert audit['points'] == 9 and audit['channel_observations'] == 1800000
        for cid, stats in summary['configs'].items():
            config = load(path.parent / cid / 'summary.json')
            for method in stats['methods']:
                thresholds.append({'cohort': path.parent.name, 'config_id': cid, 'method': method['method'],
                                   'crossing_db': method['crossing_db'], 'gain_vs_nms_db': method.get('gain_vs_NMS_db'),
                                   'gain_ci95_lo': (method.get('gain_ci95_db') or [None, None])[0],
                                   'gain_ci95_hi': (method.get('gain_ci95_db') or [None, None])[1]})
            for point in config['points']:
                for method in point['methods']:
                    points.append({'cohort': path.parent.name, 'config_id': cid,
                                   'snr_db': point['identity']['snr_db'], 'method': method['name'],
                                   'frames': method['frames'], 'payload_frame_errors': method['payload_frame_errors'],
                                   'payload_bler': method['payload_bler'], 'payload_bit_errors': method['payload_bit_errors'],
                                   'rejected': method['rejected'], 'service_frame_errors': method['service_frame_errors'],
                                   'information_bce': method['information_bce']})
    assert len(list((OUT / 'test').glob('*/audit_summary.json'))) == 13
    # Calibration, CPU formal proof, chain checks and validation summaries used to choose models.
    calibration = LOCAL / 'results/20261113-163414-pilot-alpha'
    for name in ['training_inputs_frozen.json', 'training_inputs_frozen.sha256', 'completion_audit.json',
                 'audit_summary.json', 'alpha_paired_comparison.json', 'calibration/summary.json',
                 'nms-verification/summary.json']:
        add(calibration / name)
    add(LOCAL / 'results/20261113-214206-formal50k-verify-03/summary.json')
    for root in LOCAL.glob('results/20261113-152035-s2qc-4090-*'):
        for pattern in ['*.json', '*.txt', '*.log']:
            matches(root, pattern)
    gradient = LOCAL / 'results/20261113-160241-bg1-gradient'
    matches(gradient, '*.json')
    for p in gradient.glob('**/summary.json'):
        add(p)
    for root in LOCAL.glob('logs/20261113-160241-bg1-gradient'):
        matches(root, '*.py')
    for spec in registry_entries:
        root = REPO / Path(spec['checkpoint_repository_path']).parent.parent
        selected_dir = 'step-' + str(spec['step']).zfill(5)
        for name in [f'validation/20k/{selected_dir}/summary.json', f'validation/100k/{selected_dir}/summary.json',
                     'validation/20k/NMS/summary.json', 'validation/100k/NMS/summary.json']:
            add(root / name)
    write_csv(EXPORT / 'training.csv', sorted(train_rows, key=lambda x: (x['kind'], x['config_id'], x['seed'])))
    write_csv(EXPORT / 'thresholds.csv', thresholds)
    write_csv(EXPORT / 'test_points.csv', points)
    write_json(EXPORT / 'selected_models.json', registry_entries)
    write_json(EXPORT / 'scope.json', {
        'source_experiment_commit': '606439166812f97fb42e30ae3dcfec58ec2b35f9',
        'completed_at': load(LOG / 'completion_audit.json')['finished_at'],
        'training_runs_in_campaign': 22, 'prior_seed17_training_runs': 2,
        'trained_selected_models': 24, 'paired_test_cohorts': 13,
        'test_frames_per_config_snr': 200000, 'channel_observations_shared_across_cohorts': 1800000,
        'original_local_root': str(REPO), 'precision': 'FP32, TF32/AMP off',
        'published': 'source, protocol, calibration/proof, reports/plots, aggregate point/shard statistics, '
                     'audit records, selected checkpoints, stage command/exit/stdout/stderr',
        'retained_locally': 'per-frame test/validation npz, complete train_history.jsonl, non-selected '
                            'checkpoints, large fault arrays, full original hash inventories, downloaded papers',
        'verification_limit': 'Published summaries and checkpoints can be hashed and compared. Full independent '
                              'per-frame audit requires the retained raw archive; completion_audit is historical evidence.',
        'portability': 'Original immutable JSON/PT retain absolute host paths and source hash keys. '
                       'Use checkpoint_repository_path for checkout-relative lookup; do not silently rewrite original artifacts.'})
    matches(EXPORT, '*.csv')
    matches(EXPORT, '*.json')
    add(EXPORT / 'README.md')
    add(EXPORT / 'verify_export.py')
    manifest = EXPORT / 'files.sha256.json'
    # This manifest deliberately excludes itself to avoid a recursive hash.
    selected.discard(manifest)
    write_json(manifest, {str(p.relative_to(REPO)): digest(p) for p in sorted(selected)})
    add(manifest)
    cache = REPO / '.cache/s2qc-publish-files.json'
    cache.parent.mkdir(parents=True, exist_ok=True)
    write_json(cache, [str(p.relative_to(REPO)) for p in sorted(selected)])
    print(json.dumps({'files': len(selected), 'bytes': sum(p.stat().st_size for p in selected),
                      'selected_models': 24, 'paired_cohorts': 13, 'staging_list': str(cache)}, ensure_ascii=False))


if __name__ == '__main__':
    collect()
