# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Lớp:** K4-L3A  
**Nhóm:** Nhóm Bacvuongtoiday  
**Thành viên:**
1. Đỗ Thanh Lâm (Thành viên 1 — Phụ trách `FixedSizeChunker`)
2. Trần Ngọc Khuyến (Thành viên 2 — Phụ trách `SentenceChunker`)
3. Nguyễn Văn An (Thành viên 3 — Phụ trách `HeadingChunker`)
4. Đoàn Bá Khải (Thành viên 4 — Phụ trách `RecursiveChunker` & Report / Demo Lead)

**Ngày:** 2026-09-19  

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy chế đào tạo và dịch vụ hành chính sinh viên — Học viện Công nghệ Bưu chính Viễn thông (PTIT)

**Tại sao nhóm chọn chủ đề này?**
> Thực hiện quy định bắt buộc của lớp K4-L3A về chủ đề "dịch vụ / quy định đại học", nhóm lựa chọn dữ liệu công khai từ Cổng thông tin Giáo vụ PTIT (`giaovu.ptit.edu.vn`). Nguồn này đảm bảo tuân thủ nghiêm ngặt file `robots.txt`, dữ liệu có cấu trúc văn bản pháp quy/hành chính rõ ràng (thông báo có mở đầu, điều khoản, lịch trình, điều kiện ưu tiên), rất phù hợp để so sánh ranh giới phân mảnh của các chiến lược Chunking. Ngoài ra, việc sử dụng quy chế nội bộ trường giúp nhóm dễ dàng kiểm chứng tính chính xác của các câu trả lời do RAG sinh ra.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------| 
| 1 | Đăng ký học lại cải thiện điểm | `giaovu.ptit.edu.vn/.../to-chuc-cac-lop-hoc-lai...` | 2026-09-19 / 2026 | 2,145 | audience: "student", category: "academic" |
| 2 | Thi chuẩn đầu ra Tiếng Anh đợt 2 | `giaovu.ptit.edu.vn/.../to-chuc-ky-thi-chuan-dau-ra...` | 2026-09-19 / 2026 | 5,015 | audience: "student", category: "exam" |
| 3 | Xét cấp học bổng kỳ 1 | `giaovu.ptit.edu.vn/.../ket-luan-cua-hoi-dong-xet...` | 2026-09-19 / not-stated | 4,454 | audience: "student", category: "scholarship" |
| 4 | Chuyển đổi điểm thi ACCA | `giaovu.ptit.edu.vn/.../tiep-nhan-ho-so-xet-cong-nhan...` | 2026-09-19 / not-stated | 4,008 | audience: "student", category: "academic" |
| 5 | Tư vấn chuyên ngành khóa 2023 | `giaovu.ptit.edu.vn/.../tu-van-chuyen-nganh-dao-tao-khoa-2023...` | 2026-09-19 / 2023 | 1,816 | audience: "faculty", category: "advising" |
| 6 | Tư vấn chuyên ngành khóa 2024 | `giaovu.ptit.edu.vn/.../tu-van-chuyen-nganh-dao-tao-khoa-2024...` | 2026-09-19 / 2024 | 1,352 | audience: "student", category: "advising" |
| 7 | Lớp đầu khóa tân sinh viên 2021 | `ptit.edu.vn/.../thong-bao-to-chuc-lop-dau-khoa...` | 2026-09-19 / 2021 | 4,266 | audience: "student", category: "orientation" |
| 8 | Kết quả miễn thi Tiếng Anh | `giaovu.ptit.edu.vn/.../ket-qua-xet-mien-hoc...` | 2026-09-19 / 2026 | 1,601 | audience: "student", category: "exam" |

> Ghi chú: tài liệu 3 (`hoc-bong.md`) và 4 (`acca.md`) không ghi số hiệu văn bản trong bản gốc nên `document_version` để `"not-stated"` thay vì bịa số — đúng yêu cầu K4-L3A "không bịa số hiệu". Số ký tự lấy đúng bằng `len()` trên phần thân sau khi bỏ YAML frontmatter.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] File `sources.csv` trong thư mục data khớp 1-1 với các file `.md` thu thập được.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `"hoc-lai"`, `"tuvan-khoa24"` | Định danh duy nhất của tài liệu gốc; dùng để theo dõi trích dẫn và hỗ trợ hàm `delete_document` |
| `audience` | string | `"student"`, `"faculty"`, `"all"` | Cho phép lọc cứng (pre-filtering) đối tượng thụ hưởng văn bản, tránh nhầm lẫn giữa lịch sinh viên và giảng viên |
| `department` | string | `"giaovu"` | Giúp khoanh vùng truy vấn theo từng đơn vị hành chính quản lý |
| `category` | string | `"academic"`, `"exam"`, `"advising"` | Phân loại chủ đề để lọc truy vấn theo nhu cầu cụ thể |
| `document_version`| string | `"2024"`, `"2026"` | Giúp phân biệt các văn bản cùng tên nhưng ban hành ở các năm học khác nhau |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=500)` (nay đã có cả `HeadingChunker`, xem `src/chunking.py`) trên toàn bộ 8 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Toàn bộ corpus (8 file) | FixedSizeChunker (`fixed_size`) | 57 chunks | 475.6 ký tự | Kém — thường cắt đứt ngang câu văn và con số |
| Toàn bộ corpus (8 file) | SentenceChunker (`by_sentences`) | 50 chunks | 487.5 ký tự | Khá — giữ trọn vẹn câu nhưng kích thước chunk không đều |
| Toàn bộ corpus (8 file) | RecursiveChunker (`recursive`) | 61 chunks | 402.5 ký tự | Tốt — ưu tiên cắt theo đoạn văn tự nhiên `\n\n` |
| Toàn bộ corpus (8 file) | HeadingChunker (`heading`) | 87 chunks | 285.1 ký tự | Xuất sắc — bảo toàn cấu trúc đề mục, chunk ngắn hơn vì mỗi mục nhỏ tách riêng |

*(Số liệu chạy trực tiếp bằng `ChunkingStrategyComparator` sau khi bổ sung `HeadingChunker`; không phải ước lượng.)*

### Chiến lược của từng thành viên

**Thành viên 1 — Đỗ Thanh Lâm**
- **Loại chiến lược:** `FixedSizeChunker` (chunk_size=500, overlap=50)
- **Mô tả & lý do chọn:** Cắt cố định theo độ dài 500 ký tự với 50 ký tự gối đầu (overlap). Đây là chiến lược baseline đơn giản nhất để làm mốc đối chứng, ưu điểm là chi phí tính toán thấp, kích thước chunk đồng nhất.

**Thành viên 2 — Trần Ngọc Khuyến**
- **Loại chiến lược:** `SentenceChunker` (max_sentences_per_chunk=3)
- **Mô tả & lý do chọn:** Tách văn bản theo ranh giới câu bằng Regex, mỗi chunk gom đúng 3 câu hoàn chỉnh. Chiến lược này phù hợp với các thông báo ngắn vì không bao giờ bị cắt đứt ý giữa câu.

**Thành viên 3 — Nguyễn Văn An**
- **Loại chiến lược:** `HeadingChunker` (Custom Section Chunker, chunk_size=500) — cài đặt trong `src/chunking.py`, đã tích hợp vào `ChunkingStrategyComparator`.
- **Mô tả & lý do chọn:** Văn bản hành chính PTIT không dùng markdown (`#`, `##`) hay `Điều X`/`Mục X` — kiểm tra trực tiếp trên corpus cho thấy 0 dòng nào khớp các mẫu đó. Heading thật trong dữ liệu chỉ xuất hiện dưới 2 dạng: dòng **VIẾT HOA** ngắn (VD: "ĐỐI TƯỢNG VÀ HÌNH THỨC THI") hoặc dòng **kết thúc bằng dấu `:`** (VD: "Nguyên tắc mở lớp:", "Lưu ý:") — nên `HeadingChunker` nhận diện heading theo 2 dạng này (cộng thêm dòng đánh số kiểu "2.5."). Nếu một mục vượt quá `chunk_size` sẽ gọi `RecursiveChunker` chia nhỏ tiếp, và tiêu đề được lặp lại ở đầu mỗi mảnh con để không mất ngữ cảnh.

**Thành viên 4 — Đoàn Bá Khải (Report & Demo Lead)**
- **Loại chiến lược:** `RecursiveChunker` (chunk_size=500, separators=`["\n\n", "\n", ". ", " ", ""]`)
- **Mô tả & lý do chọn:** Thuật toán chia để trị đa cấp, ưu tiên cắt theo khoảng cách đoạn văn `\n\n` trước khi hạ cấp xuống câu và từ. Đảm bảo toàn vẹn cấu trúc văn bản hành chính; phụ trách tổng hợp số liệu của cả 4 thành viên và dẫn phần thuyết trình demo.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|:---|:---|:---:|:---|:---|
| **TV1 - Lâm** | FixedSize | 7.5 / 10 | Đơn giản, số chunk ổn định, dễ cấu hình; điểm cao nhất toàn bài ở Câu 4 (0.741) | Cắt cụt câu văn; là chiến lược DUY NHẤT bị lấy sai tài liệu (`tuvan-khoa23`) lên Top-1 ở Câu 3 |
| **TV2 - Khuyến**| Sentence | 8.0 / 10 | Đảm bảo trọn vẹn ngữ nghĩa từng câu; đúng Top-1 cả 5/5 câu | Độ dài chunk không đồng đều; điểm số nhìn chung thấp nhất trong 4 chiến lược |
| **TV3 - An** | Heading | **9.0 / 10** | Đúng Top-1 cả 5/5 câu; điểm cao nhất ở 4/5 câu (Câu 1, 2, 3, 5), kỷ lục Câu 5 = 0.572 | Phụ thuộc heuristic nhận diện heading (viết hoa / kết thúc bằng `:`); tạo nhiều chunk nhỏ hơn (87 chunks) |
| **TV4 - Khải** | Recursive | 9.0 / 10 | Cân bằng tốt giữa ngữ cảnh và độ dài; đúng Top-1 cả 5/5 câu | Không đạt điểm cao nhất ở câu nào so với Heading/FixedSize |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **`HeadingChunker`** (sát nút là **`RecursiveChunker`**) là chiến lược tốt nhất cho văn bản quy chế đại học, dựa trên số liệu chạy thật bằng `text-embedding-3-small`:
> 1. Văn bản quy chế PTIT được tổ chức theo các khối mục có tiêu đề rõ ràng (*Kế hoạch thực hiện:*, *Nguyên tắc mở lớp:*, *Lưu ý:*). `HeadingChunker` cắt đúng theo các ranh giới này nên giữ chunk ngắn, đúng trọng tâm — nhờ đó thắng điểm cao nhất ở Câu 1 (0.662), Câu 2 (0.636), Câu 3 (0.615) và Câu 5 (0.572, có filter).
> 2. Ở câu hỏi số 3 (hỏi về chuyên ngành Điện tử khóa 2024), chỉ có `FixedSize` bị nhầm và xếp tài liệu khóa 2023 (`tuvan-khoa23`) lên Top-1 (tài liệu đúng vẫn có trong top-3); `Sentence`, `Recursive` và `Heading` đều xác định đúng `tuvan-khoa24` ở Top-1.
> 3. `Recursive` vẫn là lựa chọn an toàn thứ nhì — không thắng điểm cao nhất ở câu nào nhưng luôn đúng Top-1 cả 5/5 câu, tương tự Heading và Sentence.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Tài liệu & Chunk chứa thông tin |
|---|-------|-------------------------------|--------------------------| 
| 1 | Hạn cuối để đăng ký nguyện vọng học lại cải thiện điểm là khi nào? | Từ 12h00 ngày 25/09 đến 24h00 ngày 29/09/2026 | `hoc-lai.md` — Mục "Kế hoạch thực hiện" |
| 2 | Nguyên tắc ưu tiên khi mở các lớp học lại là gì? | Ưu tiên mở các lớp có từ 5 sinh viên trở lên đăng ký; các học phần không mở trong kỳ hè 2025-2026 và không có trong kỳ 1 năm học 2026-2027 | `hoc-lai.md` — Mục "Nguyên tắc mở lớp" |
| 3 | Ngành Công nghệ kỹ thuật Điện, điện tử được chia thành những chuyên ngành nào? | Kỹ thuật điện tử máy tính và Thiết kế vi mạch | `tuvan-khoa24.md` — Mục "Các chuyên ngành đào tạo" |
| 4 | Khi đăng ký học lại nguyện vọng online trên hệ thống qldt, sinh viên phải nhập thông tin gì vào ô Môn học? | Nhập đúng “Mã môn” có nguyện vọng học | `hoc-lai.md` — Mục "Lưu ý" |
| 5 | Buổi tư vấn chọn chuyên ngành diễn ra ở phòng nào và lúc mấy giờ? *(cần filter `audience = student`)* | Phòng 101 nhà A2 lúc 19h00 (ngày 17-18/9) hoặc phòng 205 nhà A2 lúc 13h00 (ngày 21/9) | `tuvan-khoa24.md` — Mục "Hỗ trợ và tư vấn chọn chuyên ngành" |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất | Điểm Score cao nhất | Có chunk liên quan trong top-3? | Ghi chú đánh giá |
|---|---------|---------------------|:---:|:---:|---|
| 1 | Hạn đăng ký học lại | Heading | **0.662** | Có ✅ (Cả 4 chiến lược) | Heading trích xuất trọn vẹn dòng kế hoạch ngày giờ |
| 2 | Nguyên tắc mở lớp | Heading | **0.636** | Có ✅ (Cả 4 chiến lược) | Heading giữ nguyên vẹn cả mục "Nguyên tắc mở lớp" |
| 3 | Chuyên ngành Điện, điện tử | Heading | **0.615** | Có ✅ (Cả 4 chiến lược) | Chỉ FixedSize chọn nhầm tài liệu khóa 2023 lên Top-1 (tài liệu đúng vẫn ở top-3) |
| 4 | Nhập thông tin ô Môn học | FixedSize | **0.741** | Có ✅ (Cả 4 chiến lược) | Điểm số cao nhất toàn bài, AI trả lời chuẩn xác 100% |
| 5 | Địa điểm tư vấn chuyên ngành | Heading | **0.572** | Có ✅ (Cả 4 chiến lược, khi bật filter) | Khi bật filter, Heading đưa phòng 101 và 205 lên Top-1 |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Metadata Pre-filtering đóng vai trò quyết định ở Câu hỏi số 5.**  
> Trong corpus có 2 tài liệu mang nội dung tương đồng về tư vấn chuyên ngành: `tuvan-khoa24` (`audience: student`) và `tuvan-khoa23` (`audience: faculty`).
> - **Khi KHÔNG dùng filter:** Do độ tương đồng từ vựng quá cao, Top-1 bị chiếm bởi tài liệu giảng viên (`tuvan-khoa23`), khiến AI sinh ra câu trả lời sai lệch (nói về lịch tư vấn online qua Trans ID của giảng viên).
> - **Khi BẬT filter `{"audience": "student"}`:** Hệ thống loại bỏ hoàn toàn các chunk của giảng viên trước khi search vector, đảm bảo 100% kết quả Top-3 đều thuộc `tuvan-khoa24` và AI trả lời chính xác phòng 101 và 205 nhà A2.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Cấu trúc dữ liệu quyết định chiến lược Chunking:** Văn bản hành chính dạng điều khoản có cấu trúc phân tầng tự nhiên, do đó các chiến lược tôn trọng ranh giới ngữ nghĩa (`RecursiveChunker`, `HeadingChunker`) luôn đánh bại phương pháp cắt theo độ dài ký tự (`FixedSizeChunker`).
> 2. **Metadata Filter là lớp bảo vệ sự thật (Grounding Layer):** Vector search thuần túy chỉ đo độ giống ngữ nghĩa, không phân biệt được đối tượng áp dụng. Metadata filter là công cụ bắt buộc để ngăn chặn AI trả lời sai đối tượng trong các bài toán thực tế.
> 3. **Hiện tượng đứt gãy thông tin tại ranh giới chunk:** `FixedSizeChunker` dễ bị chia cắt các con số và thời gian (ví dụ ngày 25/09 bị cắt ở chunk này, 24h00 ngày 29/09 bị đẩy sang chunk khác), làm suy giảm nghiêm trọng khả năng suy luận của LLM.

**Bài học rút ra khi so sánh trong nhóm:**
> Việc thử nghiệm đồng thời 4 chiến lược trên cùng một bộ câu hỏi kiểm thử giúp cả nhóm thấy rõ: cùng một mô hình embedding (`text-embedding-3-small`) và cùng một LLM (`gpt-4o-mini`), nhưng việc thay đổi cách cắt lát văn bản có thể làm đảo lộn thứ tự tài liệu trong top-k và quyết định việc AI trả lời đúng hay sai.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa bước làm sạch dữ liệu ngay từ đầu bằng cách bóc tách hoàn toàn phần tiêu đề Metadata YAML ra khỏi thân văn bản trước khi đưa vào hàm chunking, tránh việc các thẻ YAML bị cắt lẫn vào chunk nội dung đầu tiên làm loãng trọng số vector.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|:---:|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
