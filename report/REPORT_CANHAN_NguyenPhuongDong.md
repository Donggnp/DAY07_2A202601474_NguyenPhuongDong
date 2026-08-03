# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Phương Đông
**Nhóm:** [Tên nhóm]
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Hai văn bản có độ tương tự cosine cao khi vector biểu diễn của chúng hướng gần giống nhau,  hai văn bản có nội dung hoặc ý nghĩa gần nhau, dù có thể dùng từ khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: Khách hàng có thể đổi trả sản phẩm trong vòng 7 ngày.
- Câu B: Thời hạn trả lại hàng dành cho người mua là bảy ngày.
- Tại sao tương đồng: Cả hai cùng nói về quyền trả hàng và cùng nêu thời hạn 7 ngày.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Python là một ngôn ngữ lập trình.
- Câu B: Hôm nay trời mưa lớn ở Hà Nội.
- Tại sao khác: Một câu nói về công nghệ, câu còn lại nói về thời tiết và không có chung chủ đề.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine tập trung vào hướng của vector, do đó ít bị chi phối bởi độ lớn vector hoặc độ dài văn bản. Khoảng cách Euclid có thể coi hai vector cùng hướng là xa nhau chỉ vì độ lớn của chúng khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Bước trượt là `500 - 50 = 450`. Theo công thức: `ceil((10.000 - 50) / (500 - 50)) = ceil(9.950 / 450) = ceil(22,11)`.
> **Đáp án: 23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Khi overlap là 100, số chunk là `ceil((10.000 - 100) / (500 - 100)) = ceil(24,75) = 25`, tăng 2 chunk so với trước. Overlap lớn hơn giúp giữ ngữ cảnh bị cắt ở ranh giới hai chunk, nhưng làm tăng dung lượng lưu trữ và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách tại khoảng trắng hoặc xuống dòng sau dấu kết thúc câu, nhờ vậy dấu câu vẫn được giữ lại. Sau khi loại phần tử rỗng và khoảng trắng thừa, tôi gom tối đa `max_sentences_per_chunk` câu; chuỗi rỗng trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán thử dấu phân cách theo thứ tự ưu tiên, ghép các phần nhỏ khi tổng độ dài chưa vượt `chunk_size`, và gọi đệ quy với dấu phân cách tiếp theo cho phần còn quá dài. Base case là đoạn đã không vượt kích thước; nếu hết separator thì cắt cứng theo số ký tự để bảo đảm dừng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Mỗi `Document` được chuẩn hóa thành bản ghi gồm id duy nhất, content, metadata (luôn có `doc_id`) và embedding. Store dùng ChromaDB khi khả dụng, nếu không thì lưu trong danh sách trong bộ nhớ; truy vấn được nhúng một lần, chấm điểm bằng tích vô hướng của các vector đã chuẩn hóa (tương đương cosine), rồi sắp xếp giảm dần.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Tôi lọc metadata trước khi tính/xếp hạng độ tương tự, nên `top_k` chỉ được chọn từ các ứng viên thỏa điều kiện. Khi xóa, tôi tìm tất cả chunk có `metadata['doc_id']` trùng id yêu cầu, xóa toàn bộ và trả về `True` chỉ khi thực sự tìm thấy bản ghi.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Agent lấy `top_k` chunk liên quan, đánh số từng chunk trong phần `Context`, rồi đặt câu hỏi ở phần `Question`. Prompt yêu cầu LLM chỉ dùng ngữ cảnh đã cho và thông báo thiếu thông tin nếu ngữ cảnh không đủ, sau đó agent gọi `llm_fn` đúng một lần.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
collected 42 items
tests/test_solution.py ..........................................       [100%]
42 passed, 1 warning in 0.66s
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                                 | Câu B                                                           | Dự đoán | Điểm thực tế | Đúng? |
| ---- | ---------------------------------------------------------------------- | ---------------------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | Con mèo đang ngủ trên ghế sofa.                                   | Một chú mèo nằm ngủ trên chiếc ghế dài.                 | cao        | -0,090130        | Không  |
| 2    | Khách hàng có thể đổi trả sản phẩm trong vòng 7 ngày.       | Thời hạn trả lại hàng dành cho người mua là bảy ngày. | cao        | -0,050922        | Không  |
| 3    | Python là một ngôn ngữ lập trình.                                | Hôm nay trời mưa lớn ở Hà Nội.                            | thấp      | -0,063705        | Đúng  |
| 4    | Đơn hàng sẽ được giao trong ba ngày làm việc.                | Thời gian vận chuyển dự kiến là 3 ngày làm việc.        | cao        | 0,120414         | Đúng  |
| 5    | Người bán phải xác minh danh tính trước khi đăng sản phẩm. | Công thức nấu phở cần có quế và hoa hồi.                | thấp      | 0,183244         | Không  |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Cặp 5 bất ngờ nhất vì hai chủ đề không liên quan lại có điểm cao nhất. Các điểm thực tế ở bảng này dùng `MockEmbedder`: vector được sinh xác định từ chuỗi nhưng không mã hóa ngữ nghĩa, do đó kết quả chỉ kiểm tra luồng code chứ không đánh giá được ý nghĩa. Khi thử nghiệm Giai đoạn 2 cần chạy lại với multilingual embedding thật.

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

> **Trạng thái:** Chưa thể ghi kết quả trung thực vì nhóm chưa cung cấp 5 benchmark queries chung và chưa chạy thử nghiệm Giai đoạn 2. Bảng này sẽ được điền sau khi nhóm thống nhất câu hỏi và dùng embedding thật.

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá         |
| ---------------------------------------------------- | ------------------------------ |
| Khởi động (Warm-up)                               | 5 / 5                          |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                        |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                        |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                          |
| Kết quả truy xuất của tôi (Competition Results) | 0 / 10 (chờ Giai đoạn 2)    |
| **Tổng phần cá nhân**                      | **50 / 60 (tạm tính)** |
