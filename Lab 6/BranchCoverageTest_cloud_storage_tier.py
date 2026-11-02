import pytest
from cloud_storage_tier import process_storage_tenants, monitor_replication_latency

def t(tier="hot", buckets=None, active=True, vault=False):
    return {"account_active": active, "tier": tier,
            "has_backup_vault": vault, "buckets": buckets or []}

def b(size=100, corrupted=False, egress=0):
    return {"size_gb": size, "corrupted": corrupted, "egress_gb": egress}

def test_single_active_hot_tenant():
    r = process_storage_tenants([t(buckets=[b(100, egress=50)])], 10.0)
    assert r == {"total_billed": 2.5, "status": "BILLED"}

def test_invalid_input():
    with pytest.raises(ValueError):
        process_storage_tenants("bad", 10.0)

def test_inactive_tenant_skipped():
    r = process_storage_tenants([t(active=False, buckets=[b()])], 10.0)
    assert r["status"] == "ZERO_USAGE"

def test_cool_tier():
    r = process_storage_tenants([t("cool", [b(100)])], 0)
    assert r["total_billed"] == 1.5

def test_archive_tier():
    r = process_storage_tenants([t("archive", [b(100)])], 0)
    assert r["total_billed"] == 0.5

def test_unknown_tier_flagged():
    r = process_storage_tenants([t("weird", [b()])], 0)
    assert r["status"] == "ZERO_USAGE"

def test_large_bucket_egress_and_vault():
    r = process_storage_tenants([t("hot", [b(600, egress=150)], vault=True)], 10.0)
    assert r["total_billed"] == pytest.approx(27.5)

def test_zero_size_bucket():
    r = process_storage_tenants([t(buckets=[b(0)])], 0)
    assert r["status"] == "ZERO_USAGE"

def test_corrupted_hot_bucket():
    r = process_storage_tenants([t("hot", [b(100, corrupted=True), b(100)])], 0)
    assert r["total_billed"] == 2.5

def test_audit_flagged():
    r = process_storage_tenants([t(buckets=[b(0)] * 5)], 0)
    assert r["status"] == "AUDIT_FLAGGED"

def test_sync_lag_alert():
    assert monitor_replication_latency([[100, 250, 300]]) == "SYNC_LAG_ALERT"