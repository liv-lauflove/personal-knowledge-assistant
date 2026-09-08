# PRD — Personal Knowledge Assistant

**Status:** Draft v1 (berdasarkan revisi arsitektur fokus RAG)
**Pemilik produk:** Personal project (single developer, self-use)
**Tujuan dokumen:** Menjadi acuan/cetak biru sebelum coding dimulai. Semua keputusan fitur, prioritas, dan requirement dirujuk ke sini — bukan diputuskan ulang secara ad-hoc saat implementasi.

---

## 1. Ringkasan Produk

Personal Knowledge Assistant adalah aplikasi RAG (Retrieval-Augmented Generation) personal yang memungkinkan pengguna mengupload dokumen (PDF, DOCX, catatan, dll), lalu bertanya kepada AI dengan jawaban yang **berbasis isi dokumen tersebut**, disertai **citation** yang bisa diverifikasi langsung ke sumbernya. Berbeda dari ChatGPT biasa, sistem ini punya "memori" jangka panjang berupa knowledge base pribadi yang terus bertambah.

Selain sebagai alat pakai sehari-hari, proyek ini juga merupakan media belajar mendalam soal RAG pipeline (chunking, embedding, retrieval, evaluasi) dan pengembangan aplikasi full-stack modern (Next.js + FastAPI).

---

## 2. Latar Belakang & Masalah

**Masalah yang ingin diselesaikan:**

1. Pengguna mengumpulkan banyak dokumen (buku, paper, catatan kuliah, hasil riset) dari berbagai sumber, tapi kesulitan mencari dan mensintesis informasi lintas dokumen secara cepat.
2. Tools chat AI umum (ChatGPT, dll) tidak punya akses persisten ke dokumen pribadi — dokumen harus diupload ulang tiap sesi, dan tidak ada sistem penyimpanan/pengorganisasian jangka panjang.
3. Jawaban dari LLM sering sulit diverifikasi sumbernya (hallucination risk) — dibutuhkan sistem yang menunjukkan **secara eksplisit** dari halaman/dokumen mana suatu klaim berasal.
4. (Tujuan sekunder) Tidak ada cara terstruktur untuk belajar RAG secara end-to-end selain membangunnya sendiri dari nol, dibanding hanya memakai framework siap pakai yang menyembunyikan detail penting.

---

## 3. Tujuan (Goals)

| ID | Tujuan |
|----|--------|
| G1 | User dapat upload dokumen dan bertanya ke AI, dengan jawaban akurat berbasis isi dokumen dan disertai citation yang dapat diverifikasi. |
| G2 | Kualitas retrieval dapat diukur dan dievaluasi secara sistematis, bukan black box. |
| G3 | UI nyaman dan cepat dipakai sehari-hari (Next.js, responsive, streaming response). |
| G4 | Keamanan dasar terjaga sejak awal: isolasi data antar user, secrets tidak bocor, akses file terkontrol. |
| G5 | Developer (pemilik proyek) memahami penuh alur RAG dari nol — chunking, embedding, retrieval, prompt design, evaluasi. |

### Non-Goals (Di luar cakupan MVP)

- Multi-workspace dan folder bertingkat (masuk Phase 3).
- Flashcard/Quiz/Mind Map/Summary generator (masuk Phase 4).
- Kolaborasi real-time multi-user dalam satu workspace.
- Aplikasi mobile native.
- Dukungan penuh LLM lokal sebagai default (hanya opsional untuk eksperimen via Ollama).
- Skala enterprise (ribuan user bersamaan) — desain ditujukan untuk skala personal/kecil.

---

## 4. Target Pengguna

**Primary persona:** Pemilik proyek sendiri — pelajar/researcher yang mengelola puluhan hingga ratusan dokumen (buku, paper, catatan kuliah, dokumentasi teknis).

**Karakteristik:**
- Nyaman dengan teknologi, bisa memberi feedback teknis langsung.
- Butuh transparansi jawaban AI (citation, bukan jawaban "percaya saja").
- Volume dokumen menengah, bukan skala data enterprise.
- Menggunakan sistem secara rutin (harian/mingguan) untuk belajar dan riset.

---

## 5. Scope

### 5.1 Termasuk di MVP (Phase 1)

- Autentikasi ringan (Google OAuth via NextAuth)
- Upload dokumen (PDF, TXT) ke satu koleksi per user
- RAG pipeline penuh: extract → cleaning → chunking → embedding → retrieval → prompt → jawaban + citation
- Evaluasi kualitas retrieval (manual, dengan eval set)
- AI Chat dengan streaming response
- Document Viewer terhubung citation
- Search berbasis keyword (belum digabung ke semantic search)
- Saved Items (gabungan bookmark/pin/notes)
- Dashboard ringkas
- Settings dasar (pilihan embedding model & LLM)
- Keamanan dasar (row-level access control, validasi upload, secrets management)

### 5.2 Ditunda ke Fase Lanjutan

| Fase | Fitur |
|------|-------|
| Phase 2 | DOCX, PPTX, CSV, OCR gambar; Hybrid Search (vector + keyword); Re-ranking |
| Phase 3 | Workspace multi-koleksi; Folder Management; riwayat versi dokumen |
| Phase 4 | Flashcard Generator; Quiz Generator; Mind Map Generator; Summary Generator; pengaturan model AI lanjutan |

---

## 6. Functional Requirements

Setiap requirement ditulis dengan format: **Deskripsi**, **User Story**, **Acceptance Criteria**.

### FR-1 Autentikasi

**Deskripsi:** User login menggunakan akun Google melalui NextAuth. Session diverifikasi ulang di backend FastAPI.

**User Story:** Sebagai user, saya ingin login dengan akun Google saya supaya tidak perlu membuat akun/password baru.

**Acceptance Criteria:**
- [ ] User dapat login via tombol "Sign in with Google".
- [ ] Setelah login, session tersimpan dan bertahan hingga logout eksplisit atau expired.
- [ ] Setiap request ke backend API membawa token yang divalidasi ulang oleh FastAPI (backend tidak mempercayai identitas dari frontend begitu saja).
- [ ] User yang belum login tidak dapat mengakses endpoint apa pun selain halaman login.

### FR-2 Upload & Knowledge Library

**Deskripsi:** User dapat mengupload dokumen (PDF, TXT untuk MVP), melihat daftar dokumen beserta metadata dan status pemrosesan.

**User Story:** Sebagai user, saya ingin mengupload dokumen saya supaya bisa ditanyakan ke AI nantinya.

**Acceptance Criteria:**
- [ ] User dapat upload file PDF atau TXT (maks ukuran tertentu, misal 20MB).
- [ ] Sistem menolak tipe file yang tidak didukung dengan pesan error yang jelas.
- [ ] Validasi tipe file berdasarkan konten file (magic bytes), bukan hanya ekstensi nama file.
- [ ] Setelah upload, status dokumen berubah: `pending → processing → ready` atau `failed` jika terjadi error.
- [ ] Metadata yang ditampilkan: nama file, ukuran, tanggal upload, status, jumlah chunk, tag/kategori (opsional, boleh kosong).
- [ ] User hanya bisa melihat/mengakses dokumen miliknya sendiri.

### FR-3 RAG Pipeline — Pemrosesan Upload

**Deskripsi:** Saat dokumen diupload, sistem menjalankan pipeline: extract text → cleaning → chunking → embedding → simpan ke pgvector.

**User Story:** Sebagai user, saya ingin dokumen saya otomatis diproses supaya siap ditanyakan tanpa langkah manual.

**Acceptance Criteria:**
- [ ] Text diekstrak dari PDF menggunakan PyMuPDF, mempertahankan informasi nomor halaman per potongan teks.
- [ ] Cleaning menghapus whitespace berlebih dan header/footer berulang yang terdeteksi.
- [ ] Chunking mendukung minimal 2 strategi yang dapat dikonfigurasi: fixed-size (default 500 token, overlap 50) dan structure-aware (per paragraf/heading).
- [ ] Setiap chunk disimpan dengan referensi ke `document_id`, `page`, `chunk_index`, dan vector embedding-nya di kolom yang sama (pgvector).
- [ ] Jika embedding API gagal, sistem melakukan retry dengan backoff, dan menandai dokumen `failed` jika tetap gagal setelah batas retry.

### FR-4 RAG Pipeline — Chat & Retrieval

**Deskripsi:** User bertanya melalui chat, sistem melakukan retrieval chunk relevan dan menghasilkan jawaban dengan citation.

**User Story:** Sebagai user, saya ingin bertanya ke AI dan mendapat jawaban yang benar-benar berdasarkan dokumen saya, lengkap dengan sumbernya.

**Acceptance Criteria:**
- [ ] Pertanyaan user di-embed, lalu dilakukan similarity search (cosine similarity) terhadap chunk milik user tersebut saja.
- [ ] Top-k dapat dikonfigurasi (default k=5).
- [ ] Ada similarity threshold minimum; jika seluruh hasil di bawah threshold, sistem menjawab "tidak menemukan informasi terkait" alih-alih mengarang jawaban.
- [ ] Prompt yang dikirim ke LLM secara eksplisit menginstruksikan penyertaan citation per klaim (bukan hanya menempelkan seluruh chunk mentah).
- [ ] Jawaban AI ditampilkan dengan streaming (token muncul bertahap, bukan menunggu jawaban lengkap).
- [ ] Setiap jawaban menyertakan daftar sumber (nama dokumen + halaman) yang dipakai.
- [ ] Riwayat chat tersimpan dan bisa di-rename, dihapus, dan dicari.

### FR-5 Evaluasi Kualitas Retrieval

**Deskripsi:** Tersedia mekanisme untuk mengevaluasi kualitas retrieval secara manual/semi-otomatis.

**User Story:** Sebagai developer, saya ingin mengukur apakah retrieval saya benar-benar mengambil chunk yang relevan, supaya saya tahu kapan harus mengubah strategi chunking/parameter.

**Acceptance Criteria:**
- [ ] Tersedia eval set berisi 10–20 pasangan pertanyaan-jawaban dari minimal 1 dokumen uji.
- [ ] Tersedia script/endpoint yang menjalankan retrieval untuk semua pertanyaan di eval set dan menampilkan chunk yang diambil.
- [ ] Developer dapat membandingkan hasil retrieval antar strategi chunking dan antar nilai top-k secara berdampingan.

### FR-6 Document Viewer & Citation

**Deskripsi:** Jawaban AI menampilkan sumber; klik sumber membuka dokumen pada halaman terkait.

**Acceptance Criteria:**
- [ ] Setiap citation di jawaban chat dapat diklik.
- [ ] Klik citation membuka PDF viewer dan langsung scroll/navigasi ke halaman yang relevan.

### FR-7 Search (Keyword)

**Deskripsi:** Pencarian non-AI berdasarkan nama file, tag, kategori, dan isi dokumen (full-text search).

**Acceptance Criteria:**
- [ ] User dapat mencari dokumen berdasarkan nama file.
- [ ] User dapat mencari berdasarkan tag/kategori.
- [ ] User dapat mencari berdasarkan isi teks dokumen (full-text search Postgres).
- [ ] Hasil pencarian hanya menampilkan dokumen milik user tersebut.

### FR-8 Saved Items

**Deskripsi:** Sistem penyimpanan terpadu untuk chat, jawaban, dokumen, dan catatan (note) yang disimpan user.

**Acceptance Criteria:**
- [ ] User dapat menyimpan (save) sebuah chat, pesan/jawaban tertentu, atau dokumen.
- [ ] User dapat membuat "note" dari sebuah chat/jawaban (Save as Note) dengan konten yang bisa diedit.
- [ ] Semua saved items dapat difilter berdasarkan tipe (chat/message/document/note).

### FR-9 Dashboard

**Deskripsi:** Ringkasan aktivitas dan statistik knowledge base user.

**Acceptance Criteria:**
- [ ] Menampilkan jumlah total dokumen, chat, dan chunk milik user.
- [ ] Menampilkan aktivitas terbaru (upload, chat) sebagai widget di halaman yang sama (bukan halaman terpisah).

### FR-10 Settings

**Deskripsi:** Pengaturan dasar aplikasi.

**Acceptance Criteria:**
- [ ] User dapat memilih embedding model dan LLM yang dipakai (dari daftar yang didukung).
- [ ] User dapat mengganti tema (light/dark) dan bahasa antarmuka.

---

## 7. Non-Functional Requirements

### 7.1 Performa
- Waktu hingga token pertama muncul pada chat (time-to-first-token) target < 2 detik dalam kondisi jaringan normal.
- Pemrosesan upload dokumen (extract → embed) untuk dokumen ≤ 20 halaman target selesai < 30 detik.

### 7.2 Skalabilitas
- Desain harus tetap responsif hingga skala personal: ratusan dokumen, puluhan ribu chunk per user. Tidak dioptimalkan untuk skala multi-tenant besar di MVP, tapi skema data (kolom `user_id`/`workspace_id` di semua tabel relevan) harus tetap mendukung migrasi ke skala lebih besar nanti tanpa migrasi besar-besaran.

### 7.3 Reliabilitas
- Kegagalan panggilan ke LLM/embedding API harus di-retry dengan backoff, dan kegagalan permanen harus tercatat dengan status yang jelas ke user (bukan silent failure).
- Tidak ada single point of failure yang membuat data user hilang tanpa jejak (upload gagal harus jelas statusnya, bukan hilang begitu saja).

### 7.4 Keamanan
- Row-level access control: setiap query dokumen/chat/chunk WAJIB difilter berdasarkan `user_id` pemilik.
- Validasi & sanitasi file upload berdasarkan konten file, bukan hanya ekstensi.
- Semua API key/secret disimpan di environment variable atau secret manager, tidak pernah masuk ke repository.
- Rate limiting pada endpoint yang memanggil LLM/embedding API untuk mencegah biaya membengkak akibat abuse atau bug.
- HTTPS wajib di semua environment non-lokal.
- Semua input divalidasi di boundary (Pydantic di FastAPI, Zod di frontend).
- Akses file di object storage menggunakan signed URL bermasa berlaku terbatas, bukan URL publik permanen.
- Session dari NextAuth diverifikasi ulang di backend, backend tidak boleh mempercayai klaim identitas dari frontend tanpa verifikasi.

### 7.5 Usability
- UI harus responsive (desktop & mobile browser).
- Streaming response wajib ada di chat supaya terasa "hidup", bukan menunggu lama tanpa feedback.
- Pesan error harus manusiawi (bukan stack trace mentah) di sisi frontend.

### 7.6 Maintainability
- Struktur kode mengikuti modul per domain (lihat AGENTS.md).
- RAG dibangun manual per komponen (text splitter, embedding pipeline, retriever, prompt template) alih-alih memakai framework besar (LangChain dsb) di awal, supaya setiap langkah dipahami penuh dan mudah di-debug.

### 7.7 Kontrol Biaya
- Tersedia pencatatan penggunaan token/API call per user sebagai dasar rate limiting dan monitoring biaya, meskipun UI biaya detail belum wajib di MVP.

---

## 8. Arsitektur Sistem (Ringkasan)

```
Frontend (Next.js + React + Tailwind + shadcn/ui + NextAuth)
        │  REST / SSE (streaming)
        ▼
Backend API (FastAPI)
        │
   ┌────┴─────┐
   ▼          ▼
PostgreSQL   Object Storage
+ pgvector   (PDF/DOCX/Image)
(data + vector)
   │
   ▼
Embedding Model ──▶ LLM API
```

Vector database terpisah sengaja tidak digunakan — pgvector di dalam PostgreSQL yang sama sudah cukup untuk skala ini dan menyederhanakan operasional (satu database untuk dipahami dan dikelola).

---

## 9. Data Model (Ringkasan)

| Tabel | Kolom Utama |
|-------|-------------|
| User | id, name, email, password_hash (nullable jika OAuth), provider, created_at |
| Workspace | id, user_id, name, created_at *(MVP: 1 workspace default per user)* |
| Folder | id, workspace_id, name, parent_folder_id, created_at *(opsional, Phase 3)* |
| Document | id, workspace_id, folder_id (nullable), title, file_url, file_size, mime_type, status, uploaded_at, updated_at |
| Tag | id, workspace_id, name |
| DocumentTag | document_id, tag_id *(relasi many-to-many)* |
| DocumentChunk | id, document_id, chunk_index, content, page, embedding (vector), token_count, created_at |
| Chat | id, workspace_id, title, created_at, updated_at |
| Message | id, chat_id, role, content, citations (json), created_at |
| SavedItem | id, user_id, type (chat/message/document/note), ref_id, note_content (nullable), created_at |

Detail lengkap keputusan skema (kenapa tabel Embedding terpisah dihapus, kenapa Tag ditambahkan, dll) ada di dokumen arsitektur `PERSONAL_KNOWLEDGE_ASSISTANT_v2.docx`.

---

## 10. Tech Stack

**Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui, NextAuth (Auth.js) dengan Google Provider, TanStack Query, Zustand, React Hook Form + Zod.

**Backend:** FastAPI, SQLAlchemy, Alembic.

**Database & Storage:** PostgreSQL + pgvector, Supabase Storage (signed URL).

**AI:** LLM OpenAI GPT (atau kompatibel), OpenAI Embeddings (opsional model open-source untuk eksperimen), parsing dengan PyMuPDF/python-docx/Tesseract.

**Deployment:** Frontend di Vercel, Backend di Railway/VPS, Database & Storage di Supabase.

---

## 11. Roadmap

| Fase | Fokus | Exit Criteria |
|------|-------|---------------|
| **Phase 1 (MVP)** | RAG dari nol + UI dasar + keamanan dasar | Chat dengan dokumen berjalan end-to-end dengan citation benar; eval retrieval menunjukkan hasil relevan untuk mayoritas eval set; tidak ada kebocoran data antar user. |
| **Phase 2** | Multi-format, hybrid search, re-ranking | DOCX/PPTX/CSV/OCR terproses dengan benar; hybrid search terbukti meningkatkan relevansi dibanding vector-only pada eval set. |
| **Phase 3** | Workspace, folder, versi dokumen | User dapat memisahkan konteks antar topik tanpa embedding tercampur; riwayat versi dokumen berfungsi. |
| **Phase 4** | Flashcard, quiz, mind map, summary | Fitur generatif menghasilkan output terstruktur (JSON) yang valid dan bisa dirender di UI. |

---

## 12. Success Metrics

- **Retrieval quality:** ≥ 80% pertanyaan di eval set mendapat chunk relevan di top-5 hasil retrieval.
- **Latency:** time-to-first-token < 2 detik pada kondisi normal.
- **Keamanan:** 0 insiden kebocoran data antar user pada pengujian manual row-level access control.
- **Pemakaian pribadi:** digunakan secara rutin (mingguan) oleh pemilik proyek sebagai indikator produk benar-benar berguna, bukan sekadar selesai dibangun.

---

## 13. Risiko & Asumsi

| Risiko | Mitigasi |
|--------|----------|
| Biaya API LLM/embedding membengkak | Rate limiting, tracking token usage, threshold peringatan |
| Strategi chunking awal ternyata kurang optimal | Eval set dipakai untuk iterasi cepat sebelum lanjut fitur lain |
| Kualitas OCR rendah untuk dokumen scan (Phase 2) | Tandai dokumen hasil OCR dengan confidence score, biarkan user tahu keterbatasannya |
| Scope creep kembali terjadi | Semua penambahan fitur baru wajib dicek dulu terhadap Non-Goals di dokumen ini sebelum dikerjakan |

**Asumsi:** Infrastruktur skala personal (bukan multi-tenant besar) cukup untuk seluruh masa hidup proyek ini sebagai learning project.

---

## 14. Pertanyaan Terbuka

- Model embedding final: tetap OpenAI Embeddings, atau eksperimen model open-source (mis. `bge-base`, `nomic-embed`) untuk perbandingan?
- Apakah dukungan LLM lokal via Ollama akan diseriuskan di luar sekadar eksperimen?
- Berapa batas rate limit yang wajar untuk penggunaan personal (perlu disesuaikan setelah melihat pola pemakaian nyata)?
