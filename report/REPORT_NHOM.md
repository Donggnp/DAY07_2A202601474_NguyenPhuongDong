# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**

> *1 câu — ví dụ: đổi trả + điều kiện người bán.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu                               | Nguồn (Source URL)                            | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán                                                                   |
| - | --------------------------------------------- | ---------------------------------------------- | ------------------------ | ----------- | ------------------------------------------------------------------------------------ |
| 1 | GearVN - Chính sách bảo hành              | https://gearvn.com/pages/chinh-sach-bao-hanh   | 2026-08-01 / v1.0        | 4.250       | `doc_id`, `source_url`, `customer_role="buyer"`, `category="warranty"`       |
| 2 | GearVN - Quy định đổi trả                | https://gearvn.com/pages/chinh-sach-doi-tra    | 2026-08-01 / v1.0        | 3.800       | `doc_id`, `source_url`, `customer_role="buyer"`, `category="return"`         |
| 3 | GearVN - Hướng dẫn thanh toán             | https://gearvn.com/pages/huong-dan-thanh-toan  | 2026-08-01 / v1.0        | 2.950       | `doc_id`, `source_url`, `customer_role="buyer"`, `category="payment"`        |
| 4 | CellphoneS - Chính sách giao hàng          | https://cellphones.com.vn/chinh-sach-giao-hang | 2026-08-02 / v1.2        | 5.100       | `doc_id`, `source_url`, `customer_role="buyer"`, `category="shipping"`       |
| 5 | CellphoneS - Hủy đơn & Hoàn tiền         | https://cellphones.com.vn/chinh-sach-huan-tien | 2026-08-02 / v1.2        | 3.400       | `doc_id`, `source_url`, `customer_role="buyer"`, `category="cancellation"`   |
| 6 | Shopee - Điều khoản dịch vụ Người bán | https://shopee.vn/docs/seller-terms            | 2026-08-02 / v2.0        | 8.500       | `doc_id`, `source_url`, `customer_role="seller"`, `category="seller_policy"` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [X] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [X] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

---

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata    | Kiểu  | Ví dụ giá trị                                | Tại sao hữu ích cho truy xuất (retrieval)?                                                                                                      |
| -------------------- | ------ | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `doc_id`           | String | `gearvn-warranty-policy`                       | Định danh duy nhất tài liệu, hỗ trợ cập nhật hoặc xóa tài liệu khỏi vector store.                                                     |
| `customer_role`    | String | `buyer` / `seller` / `both`                | **Bắt buộc cho K4**: Cho phép lọc nhanh chính sách dành riêng cho Người mua hoặc Người bán, tránh truy xuất nhầm ngữ cảnh. |
| `category`         | String | `warranty`, `payment`, `shipping`          | Phân loại chủ đề chính sách để truy xuất chính xác theo nhu cầu người dùng.                                                         |
| `source_url`       | String | `https://gearvn.com/pages/chinh-sach-bao-hanh` | Truy xuất nguồn gốc trích dẫn (attribution), tăng độ tin cậy của câu trả lời RAG.                                                      |
| `retrieved_at`     | String | `2026-08-01`                                   | Quản lý vòng đời dữ liệu, nhận biết thời điểm thu thập.                                                                                |
| `document_version` | String | `v1.0`                                         | Đảm bảo tính chính xác khi chính sách của trang thương mại điện tử thay đổi theo thời gian.                                       |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy)           | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
| ---------- | ---------------------------------- | ----------------- | --------------------- | ------------------------------- |
|            | FixedSizeChunker (`fixed_size`)  |                   |                       |                                 |
|            | SentenceChunker (`by_sentences`) |                   |                       |                                 |
|            | RecursiveChunker (`recursive`)   |                   |                       |                                 |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**

- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**

```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**

- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**

- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
| ------------ | ------------------------ | ----------------------- | ------------ | ----------- |
|              |                          |                         |              |             |
|              |                          |                         |              |             |
|              |                          |                         |              |             |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query)                                                                                                                                                                                 | Câu trả lời chuẩn (Gold Answer)                                                                    | Chunk nào chứa thông tin?                                                                                     |
| - | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| 1 | Sản phẩm được mua tại GearVN sẽ được đổi mới trong vòng bao nhiêu ngày nếu phát sinh lỗi từ nhà sản xuất đối với các sản phẩm gaming gear?                           | Khách hàng sẽ được đổi mới trong vòng 30 ngày tính từ ngày mua hàng.                    | `gearvn-warranty-policy` (phần 4.1 Chính sách đổi mới)                                                   |
| 2 | Thời gian tối đa để gửi chuyển trả sản phẩm lỗi cho GearVN là bao lâu?                                                                                                               | Trong vòng 14 ngày kể từ khi nhận sản phẩm.                                                     | `gearvn-return-policy` (phần 2. Quy định về thời gian thông báo và gửi sản phẩm đổi trả)         |
| 3 | Khi thanh toán bằng ZaloPay trên website GearVN, tôi cần làm gì sau khi chọn hình thức thanh toán này?                                                                                | Mở ứng dụng ZaloPay của bạn và quét mã QR được cung cấp để hoàn tất việc đặt hàng. | `gearvn-payment-guide` (phần Thanh toán qua Ứng dụng ZaloPay / Bước 1 & Bước 2)                        |
| 4 | Phí vận chuyển của CellphoneS cho đơn hàng 250.000đ đối với người mua bình thường (không phải thành viên Smem/SVip) là bao nhiêu? (Lọc metadata:`customer_role="buyer"`) | Đơn hàng dưới 300.000đ sẽ có phí giao hàng là 15.000đ.                                     | `cellphones-shipping-policy` (phần 2. THÔNG TIN THANH TOÁN VÀ GIAO HÀNG / mục e. Chí phí vận chuyển) |
| 5 | Nếu tôi hủy đơn hàng CellphoneS và đã thanh toán qua thẻ ATM, tôi sẽ nhận lại tiền trong bao lâu?                                                                                | Trong vòng 7 - 10 ngày làm việc.                                                                   | `cellphones-shipping-policy` (phần 4. THÔNG TIN VỀ HUỶ ĐƠN HÀNG VÀ THỜI GIAN HOÀN TIỀN)             |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
| - | --------- | -------------------------------------- | --------------------------------- | -------- |
| 1 |           |                                        |                                   |          |
| 2 |           |                                        |                                   |          |
| 3 |           |                                        |                                   |          |
| 4 |           |                                        |                                   |          |
| 5 |           |                                        |                                   |          |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**

> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                   | Điểm tự đánh giá |
| -------------------------------------------- | ---------------------- |
| Lựa chọn tài liệu (Document Set Quality) | / 10                   |
| Thiết kế chiến lược (Strategy Design)   | / 15                   |
| Chất lượng truy xuất (Retrieval Quality) | / 10                   |
| Thuyết trình (Demo)                        | / 5                    |
| **Tổng phần nhóm**                  | **/ 40**         |
