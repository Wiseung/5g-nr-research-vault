"""Disclose device migration after the unchanged frozen report generator."""
from pathlib import Path
import hashlib,json,runpy,sys
HERE=Path(__file__).resolve().parent;LOG=HERE.parent
sys.path.insert(0,str(LOG/'code'))
import endpoint as e
def disclose():
    meta=e.load(LOG/'report_summary.json');report=Path(meta['report'])
    original=report.read_text()
    text=original.replace('RTX4090 GPU0，FP32，',
        'RTX4090：历史GPU0；2026-11-18设备数据损坏后迁移GPU3，FP32，',1)
    note='设备故障、隔离分片与迁移验收详见 [GPU0异常定位与GPU3恢复报告](20261118-GPU0显存异常定位与GPU3恢复报告.md)。\n'
    if note not in text:text+='\n'+note
    report.write_text(text)
    meta.update(device_migration_disclosed=True,platform_recovery=str(e.OUT/'platform_recovery-20261118.json'),
        reporting_adapter=str(Path(__file__)),reporting_adapter_sha256=e.sha256(Path(__file__)),report_sha256=e.sha256(report))
    e.save_json(LOG/'report_summary.json',meta)
if __name__=='__main__':
    runpy.run_path(str(LOG/'code/report.py'),run_name='__main__');disclose()
