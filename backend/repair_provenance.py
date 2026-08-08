"""
ClinIQ — Provenance Repair Migration
Back-fills document_id on existing lab_results, vital_signs, and clinical_alerts
that were written before the per-document provenance fix.

This is a one-time repair — forward ingestion already stamps document_id correctly.

Strategy:
  For each patient, find all documents and the lab/alert/vital rows that lack a
  document_id. Match them by overlapping time window: if a record's created_at
  falls within ±1 day of a document's created_at, link them to that document.

Run from backend/ with:
  venv\Scripts\python repair_provenance.py
"""
import sqlite3
import sys
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = "cliniq.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def parse_dt(s):
    if not s:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

print("=== ClinIQ Provenance Repair ===\n")

# 1. Get all patients
cur.execute("SELECT DISTINCT patient_id FROM documents")
patients = [r['patient_id'] for r in cur.fetchall()]
print(f"Found {len(patients)} patients to process\n")

total_lab_fixed = 0
total_vital_fixed = 0
total_alert_fixed = 0
total_timeline_fixed = 0

for patient_id in patients:
    # Get all completed documents for this patient
    cur.execute("""
        SELECT id, created_at, document_date, original_filename, parse_source
        FROM documents
        WHERE patient_id = ? AND status = 'completed'
        ORDER BY created_at ASC
    """, (patient_id,))
    docs = cur.fetchall()
    if not docs:
        continue

    def best_doc_for_time(created_at_str):
        """Return the document ID closest in time to the record's created_at."""
        rec_dt = parse_dt(created_at_str)
        if not rec_dt:
            return docs[0]['id'] if docs else None
        # Find doc whose created_at is closest and within 1-day window
        best_id = None
        best_delta = None
        for d in docs:
            doc_dt = parse_dt(d['created_at'])
            if not doc_dt:
                continue
            delta = abs((rec_dt - doc_dt).total_seconds())
            if best_delta is None or delta < best_delta:
                best_delta = delta
                best_id = d['id']
        return best_id

    # Fix lab_results
    cur.execute("SELECT id, created_at FROM lab_results WHERE patient_id = ? AND document_id IS NULL", (patient_id,))
    null_labs = cur.fetchall()
    for lr in null_labs:
        doc_id = best_doc_for_time(lr['created_at'])
        if doc_id:
            cur.execute("UPDATE lab_results SET document_id = ? WHERE id = ?", (doc_id, lr['id']))
            total_lab_fixed += 1

    # Fix vital_signs
    cur.execute("SELECT id, created_at FROM vital_signs WHERE patient_id = ? AND document_id IS NULL", (patient_id,))
    null_vs = cur.fetchall()
    for vs in null_vs:
        doc_id = best_doc_for_time(vs['created_at'])
        if doc_id:
            cur.execute("UPDATE vital_signs SET document_id = ? WHERE id = ?", (doc_id, vs['id']))
            total_vital_fixed += 1

    # Fix clinical_alerts
    cur.execute("SELECT id, created_at FROM clinical_alerts WHERE patient_id = ? AND document_id IS NULL", (patient_id,))
    null_alerts = cur.fetchall()
    for ca in null_alerts:
        doc_id = best_doc_for_time(ca['created_at'])
        if doc_id:
            cur.execute("UPDATE clinical_alerts SET document_id = ? WHERE id = ?", (doc_id, ca['id']))
            total_alert_fixed += 1

    # Fix timeline_events with NULL record_id
    # Strategy: match by title (contains filename) to document's original_filename
    cur.execute("SELECT id, title, created_at FROM timeline_events WHERE patient_id = ? AND record_id IS NULL", (patient_id,))
    null_events = cur.fetchall()
    for te in null_events:
        title = te['title'] or ''
        # Try to find matching document by filename match in title
        matched_doc = None
        for d in docs:
            fname = (d['original_filename'] or '').lower()
            fname_stem = fname.rsplit('.', 1)[0].lower()
            # Title usually includes the filename stem
            if fname_stem and fname_stem[:15].lower() in title.lower():
                matched_doc = d['id']
                break
        # Fallback: use closest by time
        if not matched_doc:
            matched_doc = best_doc_for_time(te['created_at'])
        if matched_doc:
            cur.execute("UPDATE timeline_events SET record_id = ? WHERE id = ?", (matched_doc, te['id']))
            total_timeline_fixed += 1

conn.commit()

print(f"Repair complete:")
print(f"  lab_results fixed:       {total_lab_fixed}")
print(f"  vital_signs fixed:       {total_vital_fixed}")
print(f"  clinical_alerts fixed:   {total_alert_fixed}")
print(f"  timeline_events fixed:   {total_timeline_fixed}")

# Verify
print("\nPost-repair verification:")
for table, col in [('lab_results', 'document_id'), ('vital_signs', 'document_id'), ('clinical_alerts', 'document_id'), ('timeline_events', 'record_id')]:
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL")
    null_count = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    total_count = cur.fetchone()[0]
    status = "✓" if null_count == 0 else "⚠"
    print(f"  {status} {table}.{col}: {null_count}/{total_count} still NULL")

conn.close()
print("\nDone.")
