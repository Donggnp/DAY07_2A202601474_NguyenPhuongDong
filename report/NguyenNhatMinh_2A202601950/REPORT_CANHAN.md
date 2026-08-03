# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Nhật Minh - 2A202601950
**Nhóm:** [Tên nhóm]
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Độ tương tự cosine cao (gần bằng 1.0) nghĩa là hai vector embedding chỉ về cùng một hướng trong không gian đa chiều. Điều này biểu thị rằng hai đoạn văn bản tương ứng có sự tương đồng rất lớn về mặt ngữ nghĩa hoặc ngữ cảnh, ngay cả khi chúng sử dụng từ vựng khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Chính sách này áp dụng cho việc hoàn tiền sản phẩm bị lỗi."
- Câu B: "Khách mua hàng sẽ được nhận lại tiền nếu mặt hàng xuất hiện khuyết điểm từ nhà sản xuất."
- Tại sao tương đồng: Cả hai câu đều diễn đạt cùng một ý nghĩa cốt lõi là hoàn tiền cho sản phẩm bị lỗi hỏng, mặc dù sử dụng các từ đồng nghĩa khác nhau ("hoàn tiền" - "nhận lại tiền", "sản phẩm bị lỗi" - "mặt hàng xuất hiện khuyết điểm").

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Chính sách này áp dụng cho việc hoàn tiền sản phẩm bị lỗi."
- Câu B: "Người bán phải tự chịu mọi chi phí vận chuyển khi gửi hàng đi quốc tế."
- Tại sao khác: Hai câu này đề cập đến hai chủ đề hoàn toàn khác nhau trong thương mại điện tử (chính sách hoàn tiền sản phẩm lỗi của người mua đối lập với chi phí logistics quốc tế của người bán).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Khoảng cách Euclid bị ảnh hưởng lớn bởi độ dài của văn bản (văn bản dài hơn sẽ có độ dài vector lớn hơn, kéo điểm đầu mút ra xa nhau dù cùng nghĩa). Trong khi đó, độ tương tự cosine chỉ đo góc giữa hai vector, giúp đánh giá chính xác sự tương đồng về mặt ngữ nghĩa mà không bị phụ thuộc vào độ dài ngắn của đoạn văn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Phép tính sử dụng công thức: $\text{Số chunks} = \lceil(Length - Overlap) / (Chunk\_size - Overlap)\rceil$
>
> - Thế số vào công thức: $\lceil(10000 - 50) / (500 - 50)\rceil = \lceil9950 / 450\rceil = \lceil22.11\rceil = 23$
> - **Đáp án:** 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Khi overlap tăng lên 100, số lượng chunk sẽ **tăng lên** thành 25 chunks (phép tính: $\lceil(10000 - 100) / (500 - 100)\rceil = \lceil9900 / 400\rceil = \lceil24.75\rceil = 25$). Chúng ta muốn độ chồng chéo nhiều hơn để bảo toàn tính liên tục của ngữ cảnh tại các ranh giới cắt, tránh tình trạng một câu hoặc một ý quan trọng bị cắt đôi làm mất đi ý nghĩa khi hệ thống thực hiện truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi tách câu bằng `re.split(r"(?<=[.!?])\s+", text)`: lookbehind `(?<=[.!?])` giữ nguyên dấu `.`/`!`/`?` ở cuối câu đứng trước (không bị regex "nuốt" mất), còn `\s+` khớp mọi khoảng trắng lẫn `\n` nên tự động xử lý luôn trường hợp `".\n"` được yêu cầu trong docstring mà không cần thêm nhánh riêng. Sau khi split, tôi `strip()` từng câu và lọc bỏ chuỗi rỗng (edge case: nhiều khoảng trắng liên tiếp hoặc câu cuối không có dấu kết) trước khi gộp theo lô `max_sentences_per_chunk`. Edge case text rỗng được chặn ngay từ đầu bằng `if not text: return []`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán đệ quy thử lần lượt các separator theo đúng thứ tự ưu tiên (`\n\n → \n → ". " → " " → ""`). Có 2 base case: (1) `len(current_text) <= chunk_size` thì trả nguyên văn bản như 1 chunk; (2) hết separator hoặc separator là `""` thì cắt cố định theo `chunk_size` (giống `FixedSizeChunker`). Nếu separator hiện tại không xuất hiện trong text, tôi gọi lại `_split` với phần separator còn lại (`rest`) trên **cùng** text — đây là bước tiến gần điều kiện dừng vì danh sách separator luôn ngắn dần. Nếu có, tôi `split()` theo separator rồi gộp tham lam các phần liền kề cho tới sát `chunk_size`; phần nào tự nó vẫn dài hơn `chunk_size` thì đệ quy tiếp với `rest` (không lặp lại đúng input+separator cũ, tránh vòng lặp vô hạn).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Lưu trong bộ nhớ: mỗi `Document` được chuẩn hoá qua helper `_make_record` thành một dict `{id, content, metadata, embedding}` — `id` ghép `doc.id` với `self._next_index` để không trùng khi nạp nhiều batch, `metadata` được copy (`dict(doc.metadata)`) chứ không dùng thẳng object gốc, và luôn có `doc_id` (dùng `setdefault` để `delete_document` sau này hoạt động được kể cả khi caller quên truyền `doc_id`). `search()` gọi chung helper `_search_records`: embed câu hỏi **một lần**, tính `_dot(query_vector, record["embedding"])` cho từng record, sort giảm dần theo score rồi cắt `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Lọc **trước**, xếp hạng **sau**: tôi duyệt `self._store` giữ lại record nào có `all(record["metadata"].get(k) == v for k, v in metadata_filter.items())`, rồi mới đưa tập con đó vào `_search_records` — nếu làm ngược (lấy top-k rồi mới lọc) có thể mất hết kết quả đúng dù store còn tài liệu hợp lệ. Khi `metadata_filter` là `None`/rỗng, tôi cho `candidates = self._store` để `search_with_filter()` và `search()` luôn trả kết quả giống hệt nhau (dùng chung 1 helper nên không thể lệch nhau). `delete_document(doc_id)` giữ lại các record có `metadata["doc_id"] != doc_id`, so độ dài danh sách trước/sau để biết có thực sự xoá được gì không rồi mới trả `True`/`False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> `__init__` chỉ lưu `store` và `llm_fn`. `answer()` gọi `store.search(question, top_k=top_k)`, ghép các chunk retrieve được thành context có đánh số `[1] (nguồn: doc_id) ...`, `[2] ...` — việc đánh số kèm `doc_id` giúp truy vết câu trả lời về đúng chunk/tài liệu khi debug retrieval sai. Prompt gồm 4 phần theo đúng thứ tự: Instruction (chỉ dùng context, nói rõ khi thiếu thông tin) → Context (đã đánh số) → Question → nhãn `Answer:`, rồi gọi `llm_fn(prompt)`. Nếu `store.search()` trả về rỗng, tôi trả thẳng một thông báo "không tìm thấy ngữ cảnh liên quan" thay vì vẫn gọi LLM với context trống.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform linux -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 42 items

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

============================== 42 passed in 0.10s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Chạy `compute_similarity()` với **`LocalEmbedder`** (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, `EMBEDDING_PROVIDER=local`) — embedder ngữ nghĩa thật, không phải mock. (Lần chạy trước với `_mock_embed` cho kết quả gần như ngẫu nhiên do mock chỉ hash nội dung, không hiểu nghĩa — số liệu đó đã được thay bằng kết quả thật dưới đây.)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
| --- | --- | --- | --- | --- | --- |
| 1 | "Khách hàng có thể đổi trả sản phẩm nếu hàng bị lỗi do nhà sản xuất." | "Nếu sản phẩm hư hỏng do lỗi từ nhà sản xuất, người mua được quyền đổi trả." | cao (paraphrase cùng nghĩa) | 0.8519 | **Đúng** |
| 2 | "GearVN hỗ trợ thanh toán bằng ví điện tử MOMO và ZaloPay." | "Khách hàng có thể quét mã QR để thanh toán qua MOMO hoặc ZaloPay khi mua hàng tại GearVN." | cao (cùng chủ đề thanh toán) | 0.7746 | **Đúng** |
| 3 | "Thời gian bảo hành laptop tại GearVN là 7 ngày đổi mới nếu lỗi nhà sản xuất." | "GearVN cam kết bảo mật thông tin cá nhân khách hàng và không chia sẻ cho bên thứ ba." | thấp (khác chủ đề: bảo hành vs. bảo mật) | 0.4117 | **Đúng** (thấp hơn hẳn 2 cặp cùng chủ đề ở trên, dù không gần 0) |
| 4 | "Phí giao hàng nhanh 2h-4h tại khu vực HCM/HN là 40.000đ cho đơn dưới 5 triệu." | "Người dùng có quyền yêu cầu chỉnh sửa dữ liệu cá nhân đã cung cấp cho GearVN." | thấp (vận chuyển vs. quyền dữ liệu cá nhân) | 0.0124 | **Đúng** — gần như trực giao, đây là cặp thấp nhất trong cả 5 cặp |
| 5 | "Sản phẩm bị lỗi kỹ thuật trong thời gian bảo hành sẽ được xử lý trong 7-30 ngày." | "Đơn hàng giao trễ so với dự kiến do điều phối hàng từ kho xa." | thấp–trung bình (đều nói "thời gian xử lý" nhưng khác chủ đề bảo hành/vận chuyển) | 0.2963 | **Đúng** |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Với embedder ngữ nghĩa thật, cả 5/5 dự đoán của tôi đều đúng thứ tự tương đối — trái ngược hoàn toàn với lần chạy `MockEmbedder` trước đó (dự đoán sai 3/5 cặp, kể cả đảo ngược thứ hạng cao nhất/thấp nhất). Điều bất ngờ nhất là **độ chênh lệch giữa các mức**: hai cặp "cùng chủ đề nhưng khác từ ngữ" (cặp 1, 2) đạt 0.77–0.85 — rất cao dù không chung một từ nào ngoài tên riêng; cặp 3 (hai chủ đề chính sách khác nhau nhưng vẫn cùng miền "chính sách mua sắm") vẫn còn 0.41, không gần 0 như tôi tưởng; còn cặp 4 (chủ đề khác biệt rõ nhất về mặt hành vi — phí ship vs. quyền dữ liệu) mới thực sự gần 0 (0.0124). Điều này cho thấy embedding ngữ nghĩa thật không chỉ phân biệt "giống/khác" nhị phân mà biểu diễn một **phổ liên tục về mức độ liên quan chủ đề** — hai văn bản cùng miền nội dung (chính sách e-commerce) luôn có similarity nền tảng nhất định dù nói về hai chính sách khác nhau, chỉ khi chủ đề tách bạch hoàn toàn (sản phẩm/vận chuyển vs. quyền riêng tư dữ liệu) thì score mới rơi về gần 0. Đây là thứ `MockEmbedder` không thể mô phỏng được vì nó không "biết" gì về ngữ nghĩa cả.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> **Corpus dùng để chạy:** `data/k4_crawled/` (6 tài liệu chính sách thật crawl từ GearVN + CellphoneS: đổi trả, thanh toán, bảo mật, vận chuyển, bảo hành). **Chiến lược cá nhân (được giao):** `RecursiveChunker(chunk_size=300)` — xem lý do chọn tham số này trong `REPORT_NHOM.md` mục 2. Nạp được **124 chunk**. **Embedder:** **`LocalEmbedder`** (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, `EMBEDDING_PROVIDER=local`) — embedder ngữ nghĩa thật, thay cho `MockEmbedder` ở lần chạy trước. Dưới đây là **đúng 5 câu hỏi chính thức** nhóm đã chốt trong `REPORT_NHOM.md` — mục 3 (trích nguyên văn). Mỗi câu tôi thêm một `gold_snippet` (chuỗi trích trực tiếp từ tài liệu gốc, đã verify tồn tại bằng `grep`) để chấm **đúng ở mức chunk**, không chỉ khớp `doc_id`.

> **So sánh nhanh 3 giá trị `chunk_size` với embedder thật (5 câu hỏi chính thức, chấm mức chunk):** `chunk_size=200` → **2/10**; `chunk_size=300` → **4/10**; `chunk_size=500` → **4/10**. Bảng chi tiết dưới đây dùng `chunk_size=300` (giá trị nhóm đã chọn).

| # | Câu hỏi (Query) — nguyên văn từ `REPORT_NHOM.md` mục 3 | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (theo `gold_snippet`) | Câu trả lời của Agent (tóm tắt) |
|---|---|---|---|---|---|
| 1 | Sản phẩm được mua tại GearVN sẽ được đổi mới trong vòng bao nhiêu ngày nếu phát sinh lỗi từ nhà sản xuất đối với các sản phẩm gaming gear? | `gearvn-warranty-policy` — "Đối với các sản phẩm lỗi phát sinh do nhà sản xuất hoặc GearVN, khách hàng sẽ được đổi mới trong vòng 30 ngày..." | 0.850 | **Có, đúng ở top-1** — chunk chứa nguyên câu gold_snippet "đổi mới trong vòng 30 ngày" | Agent trả lời đúng: dựa trên chunk chứa chính xác "30 ngày" |
| 2 | Thời gian tối đa để gửi chuyển trả sản phẩm lỗi cho GearVN là bao lâu? | `gearvn-shipping-policy` — "Với đa phần đơn hàng, GearVN cần vài giờ làm việc để kiểm tra thông tin..." | 0.791 | Không — đúng doc (`gearvn-return-policy`) rớt khỏi top-3 hoàn toàn (top-3 toàn `gearvn-shipping-policy`/`gearvn-warranty-policy`, đều nói về "thời gian xử lý" nhưng sai tài liệu) | Agent dùng nhầm context vận chuyển/bảo hành, không có "14 ngày" trong câu trả lời |
| 3 | Khi thanh toán bằng ZaloPay trên website GearVN, tôi cần làm gì sau khi chọn hình thức thanh toán này? | `gearvn-payment-guide` — "phần còn lại (sau khi khách hàng đã đặt cọc trước) bằng tiền mặt hoặc quẹt thẻ..." | 0.714 | Đúng doc (cả top-1, top-2, top-3 đều `gearvn-payment-guide`) nhưng **sai section** — không chunk nào chứa "Mở ứng dụng ZaloPay của bạn quét mã QR..." | Agent có context đúng tài liệu thanh toán nhưng không đúng đoạn hướng dẫn ZaloPay cụ thể |
| 4 | Phí vận chuyển của CellphoneS cho đơn hàng 250.000đ đối với người mua bình thường (không phải thành viên Smem/SVip) là bao nhiêu? (Lọc metadata: `customer_role="buyer"`) | `cellphones-shipping-policy` — "+ Đơn hàng dưới 300.000đ: Phí giao hàng 15.000đ + Đơn hàng từ 300.000đ trở lên: Miễn phí..." | 0.770 | **Có, đúng ở top-1** — chunk chứa nguyên câu gold_snippet "Đơn hàng dưới 300.000đ: Phí giao hàng 15.000đ" | Agent trả lời đúng: dựa trên chunk chứa chính xác mức phí 15.000đ |
| 5 | Nếu tôi hủy đơn hàng CellphoneS và đã thanh toán qua thẻ ATM, tôi sẽ nhận lại tiền trong bao lâu? | `cellphones-shipping-policy` — "(Với các thất thoát, hư hỏng sản phẩm trong quá trình vận chuyển sẽ không được hưởng chế độ đổi trả...)" | 0.719 | Đúng doc (cả top-1/2/3 đều `cellphones-shipping-policy`) nhưng **sai section** — không chunk nào chứa "Đối với giao dịch thẻ ATM: Trong vòng 7 - 10 ngày" | Agent có đúng tài liệu chính sách giao hàng CellphoneS nhưng không trúng đoạn quy định hoàn tiền theo hình thức thanh toán |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** Chấm đúng mức chunk (`gold_snippet` thật sự xuất hiện trong top-3): **2 / 5** (câu 1 và câu 4, cả hai đều ở **top-1** nên full 2/2 điểm mỗi câu). Chấm chỉ theo `doc_id` (đúng tài liệu, không quan tâm section): **4 / 5** (câu 1, 3, 4, 5) — câu 3 và câu 5 là ví dụ rõ "đúng tài liệu nhưng sai section" nên không được tính ở cách chấm chunk. Tổng điểm theo rubric `docs/SCORING.md` (2 điểm/câu): **4 / 10** ở mức chấm đúng chunk — tăng gấp 4 lần so với lần chạy `MockEmbedder` trước (1/10).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> So với lần chạy `MockEmbedder` (1/10, hầu hết sai cả tài liệu lẫn section), chạy lại với `LocalEmbedder` cho **4/10** — cải thiện rõ rệt và các score giờ nằm trong khoảng có ý nghĩa (0.71–0.85) thay vì rải rác ngẫu nhiên (0.2–0.3) như mock. Điều này xác nhận đúng cảnh báo của README: **kết luận về chunking chỉ đáng tin khi chạy với embedder ngữ nghĩa thật**. Tuy vậy câu 3 và câu 5 vẫn cho thấy giới hạn của bản thân `RecursiveChunker`: dù embedder đã tìm đúng tài liệu (căn cứ vào chủ đề chung), nó vẫn không phân biệt được giữa các section khác nhau trong CÙNG một tài liệu dài (`gearvn-payment-guide`, `cellphones-shipping-policy`) vì `RecursiveChunker` không có khái niệm "heading/mục" để neo ngữ cảnh — nhiều section về chủ đề gần giống nhau (vd. các bước thanh toán khác nhau) có similarity xấp xỉ nhau nên xếp hạng giữa chúng vẫn có thể lệch. Bài học cụ thể: (1) `chunk_size=300` và `500` cho điểm bằng nhau (4/10) trong khi `200` kém hơn hẳn (2/10) — với embedder thật, chunk quá nhỏ (200) có thể cắt đứt câu chứa số liệu quan trọng khỏi phần câu nêu chủ đề, làm giảm độ tương đồng với câu hỏi; (2) một chunker theo heading (tách và giữ tiêu đề mục cho từng section) nhiều khả năng sẽ khắc phục được lỗi "đúng doc sai section" ở câu 3, 5 — đây là hướng cải tiến tôi sẽ đề xuất thảo luận với nhóm.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 (chạy lại đúng 5 câu hỏi chính thức với `EMBEDDING_PROVIDER=local`, kết quả retrieval thật 4/10 — có ý nghĩa ngữ nghĩa, phân tích chỉ ra rõ giới hạn "đúng doc sai section" của `RecursiveChunker`) |
| **Tổng phần cá nhân** | **58 / 60** |
