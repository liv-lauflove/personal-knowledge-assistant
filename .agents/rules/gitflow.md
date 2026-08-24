# GitFlow & Conventions

Dokumen ini menjelaskan alur kerja Git (GitFlow) dan konvensi penamaan yang harus dipatuhi saat berkontribusi pada proyek **Lentera Baca**.

## 1. Struktur Branch & GitFlow

Proyek ini menggunakan model pencabangan (branching model) yang terstruktur:

- **`master`** (Production)
  - Branch ini merepresentasikan state aplikasi yang siap dirilis ke *production*.
  - **DILARANG** melakukan commit langsung ke branch ini.
  - Perubahan hanya masuk melalui PR (*Pull Request*) dari branch `dev` atau melalui *hotfix*.
  
- **`dev`** (Integration)
  - Branch pengembangan utama.
  - Fitur baru, perbaikan *bug*, dan semua pengembangan digabungkan (*merged*) di sini untuk diuji (STG/UAT).
  
- **Branch Pendukung (Prefixes)**
  Setiap pekerjaan baru harus berada di cabangnya masing-masing yang dibuat dari `dev`. Gunakan prefiks berikut:
  - `feat/*` : Untuk fitur baru. (contoh: `feat/audio-playback`)
  - `fix/*` : Untuk perbaikan bug. (contoh: `fix/login-crash`)
  - `chore/*` : Pemeliharaan rutin, *update dependencies*, dsb. (contoh: `chore/update-nextjs`)
  - `infra/*` : Perubahan infrastruktur, Docker, CI/CD. (contoh: `infra/add-docker-compose`)
  - `docs/*` : Penambahan atau perubahan dokumentasi. (contoh: `docs/update-readme`)
  - `refactor/*` : Perubahan kode yang tidak menambah fitur atau memperbaiki bug. (contoh: `refactor/button-component`)

## 2. Format Conventional Commits

Kita menggunakan standar [Conventional Commits](https://www.conventionalcommits.org/). Setiap pesan commit harus mengikuti format berikut:

```
<type>(<scope>): <short description>

[optional body]

[optional footer(s)]
```

**Tipe (Type) yang diizinkan:**
- `feat`: Menambahkan fitur baru.
- `fix`: Memperbaiki *bug*.
- `docs`: Hanya mengubah dokumentasi.
- `style`: Perubahan yang tidak mempengaruhi makna kode (*white-space*, *formatting*, dsb).
- `refactor`: Mengubah struktur kode tanpa menambah fitur / *bug fix*.
- `perf`: Optimasi performa.
- `test`: Menambah/memperbaiki tes.
- `build`: Perubahan sistem *build* atau dependensi (contoh: npm, webpack).
- `ci`: Perubahan pada file konfigurasi CI (contoh: GitHub Actions).
- `chore`: Pekerjaan rutin lainnya.

**Contoh:**
- `feat(auth): add local storage sync for user session`
- `fix(ui): resolve overlapping text on small screens`
- `docs(gitflow): update PR guidelines`

**Aturan Tambahan: Commit Atomik (Per-Context)**
- **Wajib melakukan commit per konteks atau per file jika perubahannya tidak berkaitan erat.**
- Jangan menyatukan semua perubahan dalam satu commit besar ("semua-semuanya dijadikan satu").
- Jika kamu memperbaiki bug UI dan di saat yang sama mengubah skema database, pisahkan menjadi minimal 2 commit yang berbeda.
- Gunakan `git add <file>` spesifik, hindari `git add .` jika ada file dari konteks yang berbeda.

## 3. Format & Prosedur Pull Request (PR)

Semua perubahan kode di luar lingkup pribadi harus melalui *Pull Request* (PR).

1. **Target Branch**: Pastikan PR diarahkan ke branch `dev` (kecuali untuk rilis, yang dari `dev` ke `master`).
2. **Reviewers**: Tugaskan minimal 1 *reviewer*.
3. **Deskripsi PR**: 
   - Jelaskan dengan jelas apa yang diubah dan mengapa.
   - Gunakan kata kunci GitHub untuk menghubungkan PR dengan *Issues*.
     - Gunakan **`Closes #N`** atau **`Fixes #N`** jika PR ini **menyelesaikan secara penuh** isu nomor N (otomatis menutup isu saat di-merge).
     - Gunakan **`Refs #N`** jika PR ini **terkait** dengan isu nomor N tetapi tidak menyelesaikannya sepenuhnya (tidak menutup isu otomatis).
4. **Format Checklist Verifikasi**:
   - Selalu sertakan checklist verifikasi di dalam *body* PR menggunakan sintaks Markdown checkbox `[ ]` (bukan emoji ).
   - Contoh format *body* PR:
     ```markdown
     ## Summary
     Deskripsi perubahan...

     ## Verification
     - [ ] `npm run lint`  0 errors
     - [ ] `npm run build`  Build sukses
     - [ ] `graphify update .`  Knowledge graph updated

     Closes #N
     ```

## 4. Git Lifecycle (Siklus Kerja Pengembang)

Langkah demi langkah ketika Anda mulai mengerjakan tugas:

1. **Checkout & Update branch dev**
   ```bash
   git checkout dev
   git pull origin dev
   ```
2. **Buat branch fitur baru**
   ```bash
   git checkout -b feat/nama-fitur
   ```
3. **Koding & Testing Lokal**
   - Lakukan perubahan.
   - Uji kode secara lokal (`npm run dev`).
   - Lakukan pengecekan akhir (`npm run lint`, `npm run build`).
4. **Commit Perubahan**
   - Lakukan `git add` pada file yang diubah.
   - Buat commit sesuai standar *Conventional Commits*.
   ```bash
   git commit -m "feat(ui): add supportive feedback dialog"
   ```
5. **Push ke Repository**
   ```bash
   git push origin feat/nama-fitur
   ```
6. **Buka Pull Request**
   - Buka GitHub (atau platform terkait).
   - Buat PR dari `feat/nama-fitur` menuju `dev`.
   - Isi deskripsi PR dengan jelas.
