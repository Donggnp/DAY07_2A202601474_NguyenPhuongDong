# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Thị Kiều Trang
**Nhóm:** [Tên nhóm]
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Khi hai đoạn văn bản có độ tương tự cosine cao, điều đó có nghĩa là hai vector embedding của chúng chỉ về cùng một hướng trong không gian nhiều chiều — tức là chúng mang ý nghĩa ngữ nghĩa (semantic meaning) gần giống nhau. Giá trị cosine similarity gần 1.0 cho thấy hai văn bản nói về cùng chủ đề hoặc có nội dung tương đồng, dù có thể dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Hôm nay thời tiết rất nóng"
- Câu B: "Nhiệt độ hôm nay cao quá"
- Tại sao tương đồng: Cả hai câu đều nói về cùng một hiện tượng (thời tiết nóng) chỉ dùng cách diễn đạt khác nhau. Embedding model sẽ hiểu rằng "nóng" và "nhiệt độ cao" có ý nghĩa tương đương.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tôi thích ăn phở gà"
- Câu B: "Thuật toán sắp xếp nhanh (quicksort) có độ phức tạp O(n log n)"
- Tại sao khác: Hai câu hoàn toàn khác chủ đề — một câu nói về ẩm thực, câu kia nói về khoa học máy tính. Các vector embedding sẽ chỉ về các hướng hoàn toàn khác nhau trong không gian.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ quan tâm đến **hướng** (direction) của vector, không phụ thuộc vào **độ dài** (magnitude). Trong text embeddings, hai văn bản có thể có cùng ý nghĩa nhưng vector embedding dài ngắn khác nhau (do độ dài văn bản khác nhau). Euclidean distance bị ảnh hưởng bởi độ dài vector nên có thể cho kết quả sai lệch: hai vector cùng hướng nhưng khác độ dài sẽ bị coi là "xa nhau". Cosine similarity giải quyết vấn đề này bằng cách chuẩn hoá, chỉ so sánh góc giữa hai vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: `số lượng chunk = ceil((độ_dài_tài_liệu - overlap) / (chunk_size - overlap))`
>
> `= ceil((10000 - 50) / (500 - 50))`
>
> `= ceil(9950 / 450)`
>
> `= ceil(22.11)`
>
> **Đáp án: 23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap = 100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks` — tăng từ 23 lên 25 chunks. Overlap lớn hơn nghĩa là mỗi bước nhảy (step) nhỏ hơn, tạo ra nhiều chunks hơn. Tăng overlap có lợi vì nó đảm bảo thông tin ở ranh giới giữa hai chunk không bị "cắt đôi" — nếu một ý nằm ở cuối chunk A thì phần đầu chunk B vẫn chứa lại ý đó, giúp quá trình truy xuất (retrieval) bắt được ngữ cảnh đầy đủ hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex `re.split(r'(?<=[\.\!\?])(?:\s|\n)', text)` để tách văn bản theo ranh giới câu — cụ thể là tách sau các dấu `.`, `!`, `?` khi theo sau là khoảng trắng hoặc ký tự xuống dòng. Regex dùng lookbehind `(?<=...)` để giữ lại dấu câu trong câu gốc thay vì loại bỏ nó. Sau khi tách, các câu rỗng được loại bỏ (`strip`), rồi nhóm lại theo `max_sentences_per_chunk` bằng cách duyệt qua danh sách câu với bước nhảy bằng `max_sentences_per_chunk`. Xử lý edge case: chuỗi rỗng trả về `[]`, văn bản không có dấu câu sẽ trả về toàn bộ văn bản dưới dạng 1 chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo chiến lược "thử separator theo thứ tự ưu tiên". Phương thức `_split` nhận văn bản và danh sách separator còn lại. **Base case**: nếu văn bản <= `chunk_size` thì trả về nguyên; nếu hết separator (hoặc separator rỗng `""`) thì cắt cứng theo `chunk_size`. **Recursive case**: thử tách bằng separator đầu tiên — nếu tách không được (chỉ 1 phần) thì chuyển sang separator tiếp theo. Nếu tách được, các phần nhỏ được gộp lại (merge) miễn là tổng <= `chunk_size`; phần nào quá lớn sẽ được đệ quy tách tiếp bằng separator tiếp theo. Cách tiếp cận này ưu tiên tách ở boundary tự nhiên nhất (paragraph > line > sentence > word > character).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` duyệt qua từng Document, gọi `embedding_fn` để tạo vector embedding cho `content`, rồi lưu vào `self._store` dưới dạng dict gồm `id`, `content`, `embedding`, `metadata`. Nếu ChromaDB khả dụng, dùng `collection.add()` với batch ids/documents/embeddings/metadatas. `search` tạo embedding cho query, rồi tính dot product giữa query embedding và mọi stored embedding (vì MockEmbedder đã normalize nên dot product ≈ cosine similarity). Kết quả được sắp xếp giảm dần theo score và trả về top_k kết quả, mỗi kết quả chứa `content`, `metadata`, và `score`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện **lọc trước, tìm kiếm sau** (pre-filtering): đầu tiên duyệt qua `self._store` và chỉ giữ lại các record mà metadata khớp với tất cả cặp key-value trong `metadata_filter`, sau đó gọi `_search_records` trên tập đã lọc. Nếu `metadata_filter` là `None`, chuyển hướng thẳng tới `search()`. `delete_document` lọc `self._store` bằng list comprehension, loại bỏ mọi record có `metadata['doc_id'] == doc_id` hoặc `record['id'] == doc_id`, trả về `True` nếu kích thước giảm, `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Theo mô hình RAG 3 bước: (1) Gọi `self.store.search(question, top_k)` để truy xuất các chunk liên quan nhất. (2) Xây dựng prompt có cấu trúc rõ ràng: phần hướng dẫn ("Use the following context..."), phần context (các chunk được đánh số `[1]`, `[2]`...), và phần question. Ngữ cảnh được inject trực tiếp vào prompt dưới dạng numbered list, giúp LLM dễ tham chiếu nguồn. (3) Gọi `self.llm_fn(prompt)` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.16s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (Mock) | Điểm thực tế (Multilingual) | Đúng? |
|------|-----------|-----------|---------|---------------------|-----------------------------|-------|
| 1 | "Con mèo nằm trên ghế sofa" | "Chú mèo đang ngủ trên đi-văng" | CAO | -0.0037 | 0.8524 | Đúng (với model thật) |
| 2 | "Python là ngôn ngữ lập trình phổ biến" | "Java được dùng rộng rãi trong phát triển phần mềm" | CAO | -0.1451 | 0.7142 | Đúng (với model thật) |
| 3 | "Hôm nay trời mưa to" | "Thuật toán quicksort có độ phức tạp O(n log n)" | THẤP | 0.1349 | 0.0521 | Đúng |
| 4 | "Chính sách đổi trả hàng trong 30 ngày" | "Khách hàng được hoàn tiền trong vòng 1 tháng" | CAO | -0.0753 | 0.8105 | Đúng (với model thật) |
| 5 | "Giao hàng miễn phí cho đơn trên 500k" | "Free shipping for orders over 500,000 VND" | CAO | -0.1353 | 0.7638 | Đúng (với model thật) |

> **Ghi chú phân tích:** Với `MockEmbedder` (dựa trên MD5 hash chuỗi), các giá trị tương tự cosine dao động ngẫu nhiên quanh 0 (từ -0.14 đến 0.13), không thể hiện được quan hệ ngữ nghĩa. Nhưng khi dùng mô hình nhúng đa ngôn ngữ thực tế (`paraphrase-multilingual-MiniLM-L12-v2`), kết quả phản ánh chính xác ngữ nghĩa: các cặp câu tương đồng đạt điểm > 0.70 (kể cả cặp đa ngôn ngữ Việt - Anh ở cặp 5 đạt 0.7638), trong khi cặp câu không liên quan ở cặp 3 chỉ đạt 0.0521.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điều bất ngờ nhất là ở **Cặp 5 (Việt - Anh)**, mặc dù hai câu dùng hai ngôn ngữ khác nhau ("Giao hàng miễn phí..." và "Free shipping..."), mô hình nhúng multilingual vẫn đạt độ tương đồng rất cao (0.7638). Điều này chứng minh rằng text embeddings trong không gian đa ngôn ngữ biểu diễn **ý nghĩa khái niệm (semantic concept)** độc lập với ngôn ngữ biểu đạt bề mặt. Đồng thời, kết quả của Mock Embedder nhắc nhở rằng mock chỉ dùng cho unit test kỹ thuật, không thể dùng để đánh giá chất lượng truy xuất thực tế.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | *(câu hỏi từ nhóm)* | | | | |
| 2 | *(câu hỏi từ nhóm)* | | | | |
| 3 | *(câu hỏi từ nhóm)* | | | | |
| 4 | *(câu hỏi từ nhóm)* | | | | |
| 5 | *(câu hỏi từ nhóm)* | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(Sẽ điền sau buổi thuyết trình)*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **50 / 60** |
