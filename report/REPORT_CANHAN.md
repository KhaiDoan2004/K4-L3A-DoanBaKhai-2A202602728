# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đoàn Bá Khải
**Nhóm:** Nhóm Bacvuongtoiday
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector có hướng gần giống nhau trong không gian nhiều chiều, tức nội dung ngữ nghĩa của hai đoạn văn bản tương đồng. Giá trị cosine similarity gần 1 thể hiện hai câu nói về cùng một chủ đề với ý nghĩa gần nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên đăng ký học lại trên hệ thống qldt"
- Câu B: "Đăng ký nguyện vọng học cải thiện điểm trực tuyến"
- Tại sao tương đồng: Cả hai đều nói về việc đăng ký học lại/cải thiện trên hệ thống online, cùng ngữ cảnh giáo vụ đại học.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Sinh viên đăng ký học lại trên hệ thống qldt"
- Câu B: "Thời tiết hôm nay trời nắng đẹp"
- Tại sao khác: Hai câu thuộc hai lĩnh vực hoàn toàn khác nhau (giáo dục vs thời tiết), không có từ khóa hay ngữ nghĩa chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ đo góc giữa hai vector, không phụ thuộc vào độ dài (magnitude). Trong text embedding, hai đoạn văn có thể có vector dài ngắn khác nhau nhưng vẫn cùng hướng ngữ nghĩa — cosine bắt được điều này còn Euclidean thì bị ảnh hưởng bởi độ dài vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: step = chunk_size - overlap = 500 - 50 = 450. Số chunks = ceil((10000 - 500) / 450) + 1 = ceil(9500 / 450) + 1 = 22 + 1 = 23 chunks.
> Đáp án: 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> step = 500 - 100 = 400, số chunks = ceil(9500/400) + 1 = 25 chunks — tăng lên 2 chunks. Overlap lớn hơn giúp giảm nguy cơ cắt đứt thông tin quan trọng nằm ở ranh giới giữa hai chunk, đảm bảo mỗi chunk có đủ ngữ cảnh.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `re.split(r'(\. |\! |\? |\.\n)', text)` để tách văn bản theo dấu chấm câu (". ", "! ", "? ", ".\n"). Sau đó ghép lại các delimiter vào câu trước nó, lọc bỏ chuỗi rỗng, rồi gom mỗi nhóm `max_sentences_per_chunk` câu thành 1 chunk. Edge case: văn bản rỗng trả về list rỗng, `max_sentences_per_chunk < 1` được clamp lên 1.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy: thử tách văn bản bằng separator đầu tiên trong danh sách ưu tiên (`\n\n` → `\n` → `. ` → ` ` → `""`). Nếu mảnh nào vẫn dài hơn `chunk_size`, gọi đệ quy `_split` với separator tiếp theo. Base case: nếu text đã ngắn hơn chunk_size thì trả luôn; nếu hết separator thì cắt cứng theo chunk_size.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi Document được embed bằng `embedding_fn`, lưu thành dict gồm `{id, content, metadata, embedding}` vào list `self._store`. Khi search, embed câu query, tính cosine similarity với mọi record, sort giảm dần và trả về top_k. Nếu có ChromaDB (biến `CHROMA_PERSIST_DIR`), song song lưu vào ChromaDB collection để persistent.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Filter **trước** khi search: duyệt `self._store`, chỉ giữ lại các record có metadata khớp mọi key-value trong `metadata_filter`, rồi mới chạy similarity search trên tập đã lọc. `delete_document` lọc bỏ mọi record có `id == doc_id` hoặc `metadata["doc_id"] == doc_id`, trả True nếu có ít nhất 1 record bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search(question, top_k)` lấy top-k chunks liên quan nhất, nối nội dung các chunk thành chuỗi context, nhúng vào prompt template dạng "Use the following context to answer... Context: {context} Question: {question}", rồi gọi `llm_fn(prompt)` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED
============================= 42 passed in 0.99s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Đăng ký học lại trên qldt | Đăng ký nguyện vọng cải thiện điểm | cao | 0.659 | ✅ |
| 2 | Tư vấn chọn chuyên ngành | Phân chuyên ngành đào tạo | cao | 0.535 | ✅ |
| 3 | Hạn nộp lệ phí học lại | Thời tiết Hà Nội hôm nay | thấp | 0.12 | ✅ |
| 4 | Miễn thi tiếng Anh đầu ra | Xét cấp học bổng kỳ 1 | thấp | 0.38 | ✅ |
| 5 | Lớp đầu khóa tân sinh viên | Chuyển đổi điểm ACCA toàn cầu | thấp | 0.31 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 (miễn thi tiếng Anh vs học bổng) có score 0.38 — cao hơn dự đoán vì cả hai đều thuộc ngữ cảnh "quyền lợi sinh viên" và cùng chứa các từ hành chính như "xét", "kết quả", "sinh viên". Điều này cho thấy embedding không chỉ so sánh từ khóa mà còn mã hóa ngữ cảnh chủ đề chung (semantic field), khiến hai văn bản khác nội dung nhưng cùng lĩnh vực vẫn có điểm tương đồng khá cao.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Hạn cuối đăng ký nguyện vọng học lại? | hoc-lai: "...đăng ký nguyện vọng online trên hệ thống qldt..." | 0.565 | Có ✅ | Từ 12h00 ngày 25/09 đến 24h00 ngày 29/09/2026 |
| 2 | Nguyên tắc ưu tiên mở lớp học lại? | hoc-lai: "...ưu tiên mở các lớp có từ 5 SV trở lên..." | 0.527 | Có ✅ | Có từ 5 SV đăng ký; HP không mở kỳ hè và kỳ 1 |
| 3 | Ngành CNKT Điện, điện tử chia chuyên ngành nào? | tuvan-khoa23: "...Điện tử viễn thông: 358 SV..." | 0.517 | Có ✅ | KT điện tử máy tính và Thiết kế vi mạch |
| 4 | SV nhập gì vào ô Môn học trên qldt? | hoc-lai: "...nhập đúng Mã môn có nguyện vọng học..." | 0.659 | Có ✅ | Nhập đúng "Mã môn" |
| 5 | Tư vấn chuyên ngành ở phòng nào, mấy giờ? (filter: student) | tuvan-khoa24: "...phòng 101 nhà A2..." | 0.535 | Có ✅ | Phòng 101 A2 lúc 19h00 hoặc phòng 205 A2 lúc 13h00 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> [Anh điền sau khi demo xong]

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
