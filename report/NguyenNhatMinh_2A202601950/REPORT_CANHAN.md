p

# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Nhật Minh -2A202601950
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

> **Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
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

> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** __ / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán  | Điểm thực tế | Đúng? |
| ---- | ------ | ------ | ----------- | ---------------- | ------- |
| 1    |        |        | cao / thấp |                  |         |
| 2    |        |        | cao / thấp |                  |         |
| 3    |        |        | cao / thấp |                  |         |
| 4    |        |        | cao / thấp |                  |         |
| 5    |        |        | cao / thấp |                  |         |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`). Chiến lược cá nhân: `HeadingChunker(max_chunk_size=400)`, chạy qua `evaluate.py` (39 chunk nạp). Embedder = `MockEmbedder` (ghi rõ giới hạn: score chỉ để kiểm luồng kỹ thuật, không phản ánh ngữ nghĩa thật — xem README).

| # | Câu hỏi (Query)                              | Top-1 Chunk truy xuất được (tóm tắt)                                 | Điểm Score | Có liên quan không? (Relevant, theo`gold_snippet`)                                                                       | Câu trả lời của Agent (tóm tắt)                                                |
| - | ---------------------------------------------- | -------------------------------------------------------------------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 1 | Số ngày trả hàng/hoàn tiền               | `shopee-shipping-policy` — "Cách tính phí vận chuyển..."           | 0.279        | Không — sai cả doc lẫn snippet "15 (mười lăm) ngày"                                                                   | Trích context sai (shipping) nên câu trả lời không có số 15 ngày            |
| 2 | Xử lý người bán vi phạm (filter=seller)  | `shopee-prohibited-restricted-products` — "Sản phẩm bị hạn chế..." | 0.197        | Đúng doc (nhờ filter) nhưng**sai section** — không có "Cấn trừ số dư tài khoản"                            | Có nhắc chế tài chung nhưng không trúng câu có cụm "cấn trừ số dư"     |
| 3 | Phương thức thanh toán + QR (filter=buyer) | `shopee-returns-refund-policy` — "Chi phí vận chuyển hoàn trả..."  | 0.092        | Không ở top-1; chunk đúng (`payment-methods`, chứa "Thanh toán QR: giá trị tối thiểu 10.000") chỉ đứng hạng 3 | Agent dùng context top-1 sai chủ đề nên trả lời lạc hướng thanh toán      |
| 4 | % đền bù khi thất lạc hàng               | `shopee-payment-methods` — "Ứng dụng ngân hàng..."                  | 0.264        | Không — đúng doc (`shipping-policy`) rớt khỏi top-3 hoàn toàn                                                       | Không thể trả lời đúng vì không có context liên quan vận chuyển          |
| 5 | Quyền dữ liệu cá nhân + liên hệ         | `shopee-shipping-policy` — "Thời hạn khiếu nại..."                  | 0.249        | Không — đúng doc (`privacy-policy`) rớt khỏi top-3                                                                    | Không có "dpo.vn@shopee.com" trong context nên agent không thể trả lời đúng |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** Chấm đúng mức chunk (`gold_snippet`): **1 / 5** (câu 3, nhưng không ở top-1 nên 1/2 điểm). Chấm chỉ theo `doc_id`: **2 / 5** ở top-1 (câu 2), cho thấy rõ khoảng cách giữa "đúng tài liệu" và "đúng đoạn có câu trả lời".

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Việc chấm chỉ dựa vào `doc_id` gold có xuất hiện trong top-3 hay không dễ đánh giá quá lạc quan: câu 2 đạt tuyệt đối nếu chỉ nhìn `doc_id` (cả 3 slot đều đúng tài liệu nhờ filter) nhưng không mảnh nào chứa câu trả lời thật. Bài học là luôn kiểm chứng bằng một chuỗi đặc trưng (`gold_snippet`) trích trực tiếp từ tài liệu, không chỉ khớp tên file.

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
