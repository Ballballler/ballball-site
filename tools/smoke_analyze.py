"""端到端过一遍新接口： POST /api/admin/works/{id}/analyze

用 dependency_overrides 顶掉鉴权，免得在测试里碰口令。
跑完把分析结果确认写进库这条路真走过一遍。
"""
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\ballball-site")
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Work  # noqa: E402
from app.routers import deps  # noqa: E402

app.dependency_overrides[deps.get_admin] = lambda: True

client = TestClient(app)

with SessionLocal() as db:
    work_ids = [
        w.id for w in db.query(Work).order_by(Work.sort_order, Work.id).all() if w.audio_url
    ]

print("状态查询:", client.get("/api/admin/works/analyze/status").json())

for wid in work_ids:
    res = client.post(f"/api/admin/works/{wid}/analyze")
    if res.status_code != 200:
        print(f"#{wid} 失败 {res.status_code}: {res.json()}")
        continue
    data = res.json()
    a = data.get("analysis") or {}
    print(f"\n#{wid} {data['title']}  bpm={data['bpm']} key={data['key_signature']} 时长={data['audio_duration']}s")
    print("  labels:", a.get("labels"))
    print("  verdict:", a.get("verdict"))
    print("  波形点数:", len(a.get("waveform") or []))

# 前台能不能顺带把 analysis 带出来
with SessionLocal() as db:
    first = db.query(Work).order_by(Work.sort_order, Work.id).first()
pub = client.get(f"/api/works/{first.id}").json()
print("\n公开接口是否带 analysis:", "analysis" in pub, "| analyzed_at:", pub.get("analysis", {}).get("analyzed_at"))
