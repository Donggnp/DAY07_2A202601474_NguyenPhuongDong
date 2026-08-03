# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Nguyễn Quý Dũng]
**Nhóm:** [Tên nhóm]
**Ngày:** [8/3/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Độ tương tự cosine cao (giá trị tiến gần đến 1.0) thể hiện rằng góc giữa hai vector embedding trong không gian đa chiều rất nhỏ, cho thấy hai văn bản có độ tương đồng lớn về ý nghĩa ngữ nghĩa (semantic meaning) và ngữ cảnh, bất kể sự khác biệt về số lượng từ hay độ dài văn bản.

**Ví dụ có độ tương tự CAO:**

- Câu A: Chính sách đổi trả sản phẩm trong vòng 7 ngày kể từ khi nhận.
- Câu B: Khách hàng có thể gửi trả lại hàng đã mua trong vòng một tuần.
- Tại sao tương đồng: Cả hai câu cùng diễn đạt một ý định và chính sách (hoàn trả hàng) với thời hạn tương đương ("7 ngày" và "một tuần"), dù từ ngữ và cách viết khác nhau.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Thời gian giao hàng dự kiến từ 2 đến 3 ngày làm việc.
- Câu B: Hướng dẫn đăng ký tài khoản người bán mới trên sàn.
- Tại sao khác: Hai câu đề cập đến hai chủ đề hoàn toàn độc lập (vận chuyển/giao hàng vs quản lý tài khoản người bán), không có mối liên quan ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Độ tương tự cosine chỉ đo hướng góc của vector mà không bị ảnh hưởng bởi độ dài (magnitude) của vector. Trong khi khoảng cách Euclid bị biến dạng khi độ dài câu/văn bản thay đổi (văn bản dài hơn tạo ra vector lớn hơn), cosine similarity giúp so sánh chuẩn xác bản chất ngữ nghĩa bất kể văn bản ngắn hay dài.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> *Trình bày phép tính:*
> Bước nhảy (step) = `chunk_size` - `overlap` = 500 - 50 = 450.
> Số lượng chunks = $\lceil \frac{\text{độ dài tài liệu} - \text{overlap}}{\text{step}} \rceil = \lceil \frac{10000 - 50}{450} \rceil = \lceil \frac{9950}{450} \rceil = \lceil 22.11 \rceil = 23$.
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Khi overlap tăng lên 100, step giảm xuống $500 - 100 = 400$, số lượng chunk sẽ tăng lên thành $\lceil \frac{9900}{400} \rceil = 25$ chunks. Việc tăng độ chồng chéo giúp duy trì liên tục ngữ cảnh ở ranh giới giữa các chunk, tránh làm đứt gãy thông tin hoặc làm mất ý nghĩa của câu/đoạn văn khi bị cắt ngắt ngang.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+|\n+', text.strip())` với kỹ thuật Lookbehind để ngắt câu theo dấu kết thúc (`.`, `!`, `?` hoặc ký tự xuống dòng `\n`) mà vẫn giữ nguyên dấu ngắt câu ở cuối mỗi câu. Xử lý edge case văn bản rỗng hoặc câu không đúng định dạng bằng cách làm sạch `strip()`, sau đó gom các câu lại thành nhóm tối đa `max_sentences_per_chunk` câu per chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán thực hiện thử nghiệm các dấu phân cách theo thứ tự ưu tiên giảm dần (`["\n\n", "\n", ". ", " ", ""]`). Ở mỗi cấp, tách văn bản và gom các phần lại sao cho độ dài không vượt quá `chunk_size`. Base case (trường hợp cơ sở) xảy ra khi độ dài đoạn văn bản nhỏ hơn hoặc bằng `chunk_size` (trả về ngay đoạn đó) hoặc khi đã duyệt hết danh sách separator thì tiến hành cắt phẳng theo độ dài ký tự `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Với `add_documents`, mỗi `Document` được tạo vector embedding thông qua `_embedding_fn` và lưu vào danh sách bản ghi `self._store` dưới dạng dictionary gồm các trường (`id`, `content`, `metadata`, `embedding`, `doc_id`). Với `search`, câu hỏi truy vấn được nhúng thành vector, tính tích vô hướng (dot product) / cosine similarity với từng bản ghi trong `self._store`, sau đó sắp xếp theo điểm số từ cao đến thấp và lấy top-k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> `search_with_filter` thực hiện lọc trước (pre-filtering) danh sách các chunk trong `self._store` thỏa mãn toàn bộ các cặp điều kiện key-value trong `metadata_filter`, sau đó mới tính độ tương tự và xếp hạng trên tập đã lọc. `delete_document` tìm kiếm tất cả các chunk khớp với `doc_id` (kiểm tra `id`, `doc_id`, hoặc `metadata['doc_id']`), loại bỏ chúng khỏi `self._store` và trả về `True` nếu xóa thành công ít nhất 1 chunk, ngược lại trả về `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Xây dựng theo mô hình RAG chuẩn: gọi `store.search(question, top_k)` để truy xuất top-k chunk có điểm tương đồng cao nhất, ghép các nội dung này thành chuỗi ngữ cảnh `context_str` với định dạng danh sách (`- <content>`). Sau đó, inject ngữ cảnh và câu hỏi vào một Prompt có cấu trúc rõ ràng (`Context`, `Question`, `Answer:`) rồi gọi `llm_fn(prompt)` để sinh ra câu trả lời cuối cùng.


---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# === Demo pipeline nạp dữ liệu (ingest.build_knowledge_base) ===
Thư mục dữ liệu: data/k4_ecommerce
Backend nhúng: text-embedding-3-small
Đã nạp 3 chunk vào EmbeddingStore

=== Tìm kiếm (EmbeddingStore.search) ===
Câu hỏi: Chunking là gì?
1. score=0.285 source=data\k4_ecommerce\seller-listing.md
   > Khối metadata phía trên là **template mẫu** cho K4 — thay `source_url`/`retrieved_at`/`document_version` bằng nguồn cô...
2. score=0.262 source=data\k4_ecommerce\returns-policy.md
   > Khối metadata phía trên là **template mẫu** cho K4 (bắt buộc: `customer_role` + `source_url` + `retrieved_at` + `docum...
3. score=0.248 source=data\k4_ecommerce\returns-policy.md
   hoặc không đúng mô tả.  Người bán có trách nhiệm phản hồi theo quy trình của sàn. Nhóm phải bổ sung nguồn chính sách côn...

=== KnowledgeBaseAgent ===
[DEMO LLM] Generated answer from prompt preview: Use the following context to answer the question.  Context: - > Khối metadata phía trên là **template mẫu** cho K4 — thay `source_url`/`retrieved_at`/`document_version` bằng nguồn công khai thật trước khi dùng làm benchmark.  # Đăng bán sản phẩm (dữ liệu khởi động)  Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác, bao gồm giá, mô tả và tình trạng hàng. Sản phẩm bị hạn chế hoặc bị ...
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
| --- | --- | --- | --- | --- | --- |
| 1 | Chính sách đổi trả sản phẩm trong 7 ngày | Khách hàng có thể hoàn trả hàng trong vòng 1 tuần | cao | 0.6264 | Đúng |
| 2 | Quy định thanh toán trực tuyến | Hình thức chuyển khoản ngân hàng và ví điện tử | cao | 0.5151 | Đúng |
| 3 | Thời gian giao hàng dự kiến | Hướng dẫn đăng ký tài khoản người bán mới | thấp | 0.3649 | Đúng |
| 4 | Quyền riêng tư và bảo mật thông tin | Chính sách hoàn tiền khi hủy đơn hàng | thấp | 0.3774 | Đúng |
| 5 | Khách hàng muốn đổi trả hàng lỗi | Làm sao để tôi trả lại sản phẩm bị hỏng? | cao | 0.6114 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Kết quả ấn tượng nhất là cặp câu 5 ("Khách hàng muốn đổi trả hàng lỗi" và "Làm sao để tôi trả lại sản phẩm bị hỏng?") dù từ vựng khác nhau hoàn toàn ("đổi trả hàng lỗi" vs "trả lại sản phẩm bị hỏng"), mô hình embedding vẫn nhận diện độ tương đồng cao (0.6114). Điều này chứng minh rằng vector embeddings biểu diễn dựa trên không gian ý nghĩa ngữ nghĩa (semantic meaning) và ngữ cảnh chứ không phụ thuộc vào việc khớp từ khóa chính xác (lexical keyword matching).


---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| - | ----------------- | ------------------------------------------ | ------------ | --------------------------------- | ------------------------------------- |
| 1 |                   |                                            |              |                                   |                                       |
| 2 |                   |                                            |              |                                   |                                       |
| 3 |                   |                                            |              |                                   |                                       |
| 4 |                   |                                            |              |                                   |                                       |
| 5 |                   |                                            |              |                                   |                                       |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | / 5                    |
| Hướng tiếp cận của tôi (My Approach)           | / 10                   |
| Hoàn thiện code (Core Implementation — tests)     | / 30                   |
| Dự đoán độ tương tự (Similarity Predictions) | / 5                    |
| Kết quả truy xuất của tôi (Competition Results) | / 10                   |
| **Tổng phần cá nhân**                      | **/ 60**         |
