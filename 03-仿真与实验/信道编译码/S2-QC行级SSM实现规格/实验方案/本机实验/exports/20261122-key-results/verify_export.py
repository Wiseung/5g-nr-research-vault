"""Verify published artifacts and archived evidence without torch or CUDA."""
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL = HERE.parents[1]


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    manifest = load(HERE / 'files.sha256.json')
    # Locate repository by its published relative path, without relying on .git.
    anchor = '03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/本机实验'
    repo = next(p for p in HERE.parents if (p / anchor).resolve() == LOCAL)
    for name, expected in manifest.items():
        path = repo / name
        assert path.is_relative_to(repo) and path.is_file(), name
        assert sha(path) == expected, ('publication hash mismatch', name)
    scope = load(HERE / 'scope.json')
    original_root = Path(scope['original_local_root'])
    models = load(HERE / 'selected_models.json')
    assert len(models) == 24
    seen = set()
    run = '20261114-235334-endpoint-multiseed-mechanisms'
    log = LOCAL / 'logs' / run
    out = LOCAL / 'results' / run
    for model in models:
        key = (model['kind'], model['config_id'], model['seed'])
        assert key not in seen
        seen.add(key)
        path = repo / model['checkpoint_repository_path']
        assert path in [repo / p for p in manifest]
        assert sha(path) == model['checkpoint_sha256']
        assert path.with_suffix('.pt.sha256').read_text().split()[0] == sha(path)
        summary = load(path.parent.parent / 'summary.json')
        assert summary['status'] == 'formal_50k_completed'
        assert summary['steps'] == 50000 and summary['observations'] == 3200000
        assert summary['checkpoint_selection']['selected']['step'] == model['step']
        assert summary['checkpoint_selection']['selected']['model_parameter_sha256'] == model['parameter_sha256']
        assert summary['all_training_loss_gradients_parameters_finite']
        assert summary['checkpoint_reload_max_error'] == 0
        assert summary['post_checks']['symmetry_max_abs_error'] < 2e-4
        assert summary['post_checks']['noiseless_payload_errors'] == 0
        assert summary['post_checks']['noiseless_rejected'] == 0
    cohorts = sorted((out / 'test').glob('*/audit_summary.json'))
    assert len(cohorts) == 13
    for path in cohorts:
        audit = load(path)
        assert audit['status'] == 'passed'
        assert audit['points'] == 9 and audit['channel_observations'] == 1800000
        if path.parent.name != 'seed17':
            assert audit['paired_baseline_shards_reproduced'] == 288
        assert load(path.parent / 'summary.json')['status'] == 'passed'
    for manifest_path, nested in [(log / 'core_snapshot/sha256.json', None),
                                   (log / 'campaign_code_frozen_before_test.json', 'sha256'),
                                   (log / 'endpoint_source_frozen.json', None)]:
        hashes = load(manifest_path)
        if nested:
            hashes = hashes[nested]
        for name, expected in hashes.items():
            old_path = Path(name)
            if old_path.is_absolute():
                relative = old_path.relative_to(original_root)
            else:
                relative = LOCAL.relative_to(repo) / old_path
            assert sha(repo / relative) == expected, ('frozen code mismatch', str(relative))
    completion = load(log / 'completion_audit.json')
    assert completion['status'] == 'completed' and completion['training_runs'] == 22
    assert completion['test_cohorts'] == 13
    assert load(log / 'pipeline/exit.json')['returncode'] == 0
    with (HERE / 'training.csv').open(newline='') as stream:
        assert len(list(csv.DictReader(stream))) == 24
    print(json.dumps({'status': 'passed', 'published_files_checked': len(manifest),
                      'selected_models': len(models), 'paired_test_cohorts': len(cohorts),
                      'verification_scope': 'published hashes, frozen sources, aggregate completion evidence; '
                                            'not a fresh per-frame audit or new-machine GPU proof'}, ensure_ascii=False))


if __name__ == '__main__':
    verify()
