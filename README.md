# Timbang — AI Maker–Checker untuk Purchasing

Sistem AI maker–checker untuk mendeteksi fraud pengadaan di perusahaan menengah Indonesia (50–500 karyawan) tanpa ERP.

## Problem
Fraud pengadaan menggerus ~5% pendapatan per tahun (ACFE 2026). Perusahaan menengah tanpa ERP tidak punya kontrol maker–checker yang layak.

## Solusi
Dua agen AI:
- **Maker Agent** — analisis penawaran vendor, cross-validate harga pasar, rekomendasi vendor.
- **Checker Agent** — three-way matching (PO/GRN/Invoice/Faktur Pajak), validasi SOP, laporan risiko.

## Status
- Maker Agent di Langflow — berjalan.
- Checker Agent — dalam pengembangan.
- Backend FastAPI — dalam pengembangan.

## Struktur Repo
- `backend/` — FastAPI backend (flat monorepo).
- `docs/` — arsitektur, security, panduan agent.
- `langflow/` — export flow Langflow.
- `tools/` — utilitas & sanitasi.

## Lisensi
Hackathon submission — IBM SkillsBuild University Education National Hackathon 2026.
