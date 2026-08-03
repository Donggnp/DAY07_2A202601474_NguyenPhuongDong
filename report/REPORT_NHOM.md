# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store (Biến thể K4)

**Nhóm:** Nhóm 4 — K4 E-commerce Policy Retrieval
**Thành viên:**

1. Nguyễn Phương Đông (2A202601474)
2. Nguyễn Quý Dũng (2A202601200)
3. Nguyễn Nhất Minh (2A202601950)
4. Trần Thị Kiều Trang (2A202601498)
   **Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**

> Nhóm tập trung vào bộ tài liệu chính sách mua hàng, đổi trả, bảo hành, thanh toán và vận chuyển từ các nền tảng bán lẻ E-commerce Việt Nam (GearVN, CellphoneS, Shopee), áp dụng phân loại metadata theo vai trò `customer_role` (`buyer` / `seller`).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu                      | Nguồn (Source URL)                            | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán                                                             |
| - | ------------------------------------ | ---------------------------------------------- | ------------------------ | ----------- | ------------------------------------------------------------------------------ |
| 1 | GearVN - Chính sách bảo hành     | https://gearvn.com/pages/chinh-sach-bao-hanh   | 2026-08-01 / v1.0        | 9.379       | `doc_id`, `source_url`, `customer_role="buyer"`, `category="warranty"` |
| 2 | GearVN - Quy định đổi trả       | https://gearvn.com/pages/chinh-sach-doi-tra    | 2026-08-01 / v1.0        | 1.862       | `doc_id`, `source_url`, `customer_role="buyer"`, `category="return"`   |
| 3 | GearVN - Hướng dẫn thanh toán    | https://gearvn.com/pages/huong-dan-thanh-toan  | 2026-08-01 / v1.0        | 3.800       | `doc_id`, `source_url`, `customer_role="buyer"`, `category="payment"`  |
| 4 | CellphoneS - Chính sách giao hàng | https://cellphones.com.vn/chinh-sach-giao-hang | 2026-08-02 / v1.2        | 11.175      | `doc_id`, `source_url`, `customer_role="buyer"`, `category="shipping"` |
| 5 | GearVN - Chính sách giao hàng     | https://gearvn.com/pages/chinh-sach-giao-hang  | 2026-08-01 / v1.0        | 4.866       | `doc_id`, `source_url`, `customer_role="buyer"`, `category="shipping"` |
| 6 | GearVN - Chính sách bảo mật      | https://gearvn.com/pages/chinh-sach-bao-mat    | 2026-08-01 / v1.0        | 7.278       | `doc_id`, `source_url`, `customer_role="both"`, `category="privacy"`   |

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

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu `gearvn-warranty-policy.md` (9.379 ký tự):

| Tài liệu                 | Chiến lược (Strategy)           | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không?                                           |
| -------------------------- | ---------------------------------- | ----------------- | --------------------- | ------------------------------------------------------------------------- |
| `gearvn-warranty-policy` | FixedSizeChunker (`fixed_size`)  | 21                | 387.9 ký tự         | Không — hay bị cắt đứt giữa câu hoặc ranh giới điều khoản    |
| `gearvn-warranty-policy` | SentenceChunker (`by_sentences`) | 38                | 184.7 ký tự         | Có — giữ được từng câu trọn vẹn nhưng chunk khá nhỏ          |
| `gearvn-warranty-policy` | RecursiveChunker (`recursive`)   | 23                | 308.8 ký tự         | Khá tốt — ưu tiên tách đoạn (`\n\n`) và dòng (`\n`) trước |

---

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Phương Đông**

- **Loại chiến lược:** Custom `DocumentStructureChunker` (Markdown / Structural Chunker)
- **Mô tả & lý do chọn:** Chia theo Markdown header (`#`, `##`, `###`) và tiêu đề mục nhỏ (`4.1`, `e.`, `Bước 1:`), đồng thời neo chuỗi tiêu đề cha vào đầu mỗi chunk. Giúp trích xuất đúng từng điều khoản độc lập mà không bị mất chủ đề cha.
- **Kết quả:** Sinh 56 chunks trên toàn bộ corpus. Điểm truy xuất với OpenAI Embeddings: **5/5 câu trả lời đúng**.

**Thành viên 2 — Nguyễn Quý Dũng**

- **Loại chiến lược:** `OverlapChunker` (Sliding Window Fixed-Size Chunker)
- **Mô tả & lý do chọn:** `chunk_size = 400`, `overlap_size = 80` (~20%). Tạo ra các chunk có phần gối đầu lên nhau để khắc phục tình trạng bị cắt đứt ranh giới thông tin ở giữa câu.
- **Kết quả:** Sinh 90 chunks. Đạt điểm tương đồng OpenAI **0.5985 – 0.7422**, trả lời chính xác **5/5 câu**.

**Thành viên 3 — Nguyễn Nhất Minh**

- **Loại chiến lược:** `RecursiveChunker` (chunk_size = 300)
- **Mô tả & lý do chọn:** Phân tách ưu tiên theo thứ tự `\n\n → \n → .  → " "`. Tự động gom các đoạn nhỏ theo cấu trúc phân cấp tự nhiên của tài liệu mà không cắt ngang giữa câu.
- **Kết quả:** Sinh 124 chunks. Chạy thử nghiệm chi tiết với `LocalEmbedder`, phân tích tốt hiện tượng "đúng docid nhưng khác section".

**Thành viên 4 — Trần Thị Kiều Trang**

- **Loại chiến lược:** `FixedSizeChunker` (chunk_size = 400, overlap = 0)
- **Mô tả & lý do chọn:** Cắt cố định 400 ký tự không overlap để làm đường cơ sở so sánh đơn giản nhất về tốc độ và số lượng chunk.
- **Kết quả:** Sinh 73 chunks. Kết hợp thử nghiệm với Gemini Embedding / OpenAI API đạt kết quả cao ở các câu hỏi thông dụng.

---

### So Sánh Giữa Các Thành Viên

| Thành viên            | Chiến lược (Strategy)               | Điểm truy xuất (/10) | Điểm mạnh                                                                                                            | Điểm yếu                                                      |
| ----------------------- | -------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Nguyễn Phương Đông | Custom`DocumentStructureChunker`     | 10 / 10                 | Giữ nguyên vẹn cấu trúc từng mục/khoản chính sách, neo tiêu đề cha nên không bao giờ bị mất chủ đề | Cần parser Markdown/Regex phức tạp hơn                       |
| Nguyễn Quý Dũng      | `OverlapChunker` (400, overlap=80)   | 10 / 10                 | Giữ ngữ cảnh liên tục ở ranh giới cắt, không bị đứt đoạn thông tin                                       | Tạo nhiều chunk hơn (90 chunks), tăng dung lượng lưu trữ |
| Nguyễn Nhất Minh      | `RecursiveChunker` (300)             | 8 / 10                  | Linh hoạt theo phân cấp tự nhiên của văn bản                                                                    | Đôi khi gom nhầm các section khác nhau nếu ngắn           |
| Trần Thị Kiều Trang  | `FixedSizeChunker` (400, no overlap) | 8 / 10                  | Đơn giản, tốc độ xử lý nhanh nhất                                                                              | Dễ bị cắt đứt câu/số liệu ở ranh giới cắt             |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> Chiến lược **`DocumentStructureChunker` (cắt theo cấu trúc mục/khoản Markdown)** kết hợp **`OverlapChunker`** là tốt nhất cho bộ tài liệu chính sách E-commerce. Do chính sách thương mại điện tử được tổ chức dạng các điều khoản/quy định rõ ràng (ví dụ: *Điều 4.1 Chính sách đổi mới*), việc tách theo tiêu đề và giữ tiêu đề cha giúp vector embedding bắt chính xác phạm vi áp dụng mà không bị nhiễu bởi các điều khoản khác trong cùng một file.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query)                                                                                                                                                                                 | Câu trả lời chuẩn (Gold Answer)                                                                    | Chunk nào chứa thông tin?                                                                                     |
| - | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| 1 | Sản phẩm được mua tại GearVN sẽ được đổi mới trong vòng bao nhiêu ngày nếu phát sinh lỗi từ nhà sản xuất đối với các sản phẩm gaming gear?                           | Khách hàng sẽ được đổi mới trong vòng 30 ngày tính từ ngày mua hàng.                    | `gearvn-warranty-policy` (phần 4.1 Chính sách đổi mới)                                                   |
| 2 | Thời gian tối đa để gửi chuyển trả sản phẩm lỗi cho GearVN là bao lâu?                                                                                                               | Trong vòng 14 ngày kể từ khi nhận sản phẩm.                                                     | `gearvn-return-policy` (phần 2. Quy định về thời gian thông báo và gửi sản phẩm đổi trả)         |
| 3 | Khi thanh toán bằng ZaloPay trên website GearVN, tôi cần làm gì sau khi chọn hình thức thanh toán này?                                                                                | Mở ứng dụng ZaloPay của bạn và quét mã QR được cung cấp để hoàn tất việc đặt hàng. | `gearvn-payment-guide` (phần Thanh toán qua Ứng dụng ZaloPay / Bước 1 & Bước 2)                        |
| 4 | Phí vận chuyển của CellphoneS cho đơn hàng 250.000đ đối với người mua bình thường (không phải thành viên Smem/SVip) là bao nhiêu? (Lọc metadata:`customer_role="buyer"`) | Đơn hàng dưới 300.000đ sẽ có phí giao hàng là 15.000đ.                                     | `cellphones-shipping-policy` (phần 2. THÔNG TIN THANH TOÁN VÀ GIAO HÀNG / mục e. Chí phí vận chuyển) |
| 5 | Nếu tôi hủy đơn hàng CellphoneS và đã thanh toán qua thẻ ATM, tôi sẽ nhận lại tiền trong bao lâu?                                                                                | Trong vòng 7 - 10 ngày làm việc.                                                                   | `cellphones-shipping-policy` (phần 4. THÔNG TIN VỀ HUỶ ĐƠN HÀNG VÀ THỜI GIAN HOÀN TIỀN)             |

---

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi                                                  | Chiến lược tốt nhất cho câu này                     | Có chunk liên quan trong top-3? | Ghi chú                                                  |
| - | ---------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------- | --------------------------------------------------------- |
| 1 | Gaming gear GearVN đổi mới bao nhiêu ngày?            | `DocumentStructureChunker` / `OverlapChunker`          | Có (Top-1, Score > 0.74)         | Cắt đúng mục 4.1 chính sách đổi mới 30 ngày     |
| 2 | Thời gian tối đa chuyển trả sản phẩm lỗi GearVN?   | `OverlapChunker` / `RecursiveChunker`                  | Có (Top-1/Top-3, Score > 0.72)   | Trả về đúng quy định gửi trả trong 14 ngày       |
| 3 | Thao tác thanh toán ZaloPay trên GearVN?                | `DocumentStructureChunker`                               | Có (Top-1, Score > 0.71)         | Bắt trọn vẹn Bước 1 & Bước 2 quét mã QR          |
| 4 | Phí ship CellphoneS đơn 250k cho khách thường?       | `OverlapChunker` (với Filter `customer_role="buyer"`) | Có (Top-1, Score > 0.62)         | Lọc metadata chính xác, lấy đúng mốc phí 15.000đ |
| 5 | Thời gian hoàn tiền thẻ ATM khi hủy đơn CellphoneS? | `DocumentStructureChunker` / `OverlapChunker`          | Có (Top-1, Score > 0.59)         | Trả về đúng khung thời gian 7 - 10 ngày làm việc  |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> **Lọc bằng metadata cực kỳ hữu ích**, đặc biệt ở **Câu 4** (và các câu hỏi phân biệt phạm vi đối tượng). Trong K4, việc lọc theo `customer_role="buyer"` giúp loại bỏ ngay lập tức các điều khoản dành cho Người bán (`seller`), tránh tình trạng mô hình tìm kiếm trả về các quy định chiết khấu/chi phí của nhà bán hàng trên sàn E-commerce.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

1. **Sự khác biệt giữa Mock vs Real Embedding:** `MockEmbedder` chỉ hash chuỗi nên điểm số ngẫu nhiên (~0.2-0.3) và không tìm đúng ngữ nghĩa. Khi đổi sang **OpenAI (`text-embedding-3-small`)** hoặc **Local Multilingual**, điểm tương đồng đạt **0.60 – 0.85** và truy xuất chính xác Top-1.
2. **Ưu thế của Structural & Overlap Chunking:** Với văn bản chính sách có tiêu đề mục-khoản rõ ràng, việc cắt theo cấu trúc Markdown hoặc giữ Overlap giúp câu trả lời của RAG Agent luôn đầy đủ ngữ cảnh, không bị cắt cụt số liệu quan trọng.
3. **Vai trò của Pre-filtering Metadata:** Lọc theo `customer_role` và `category` trước khi Vector Search giúp giảm nhiễu không gian vector và tăng độ chính xác của kết quả Top-k.

**Bài học rút ra khi so sánh trong nhóm:**

> Cùng một bộ tài liệu chính sách, các chiến lược chia nhỏ khác nhau dẫn đến khác biệt lớn về chất lượng truy xuất. Cắt cố định (`FixedSize`) dễ làm rách thông tin ranh giới; trong khi cắt theo cấu trúc (`DocumentStructure`) và có độ chồng chéo (`Overlap`) đem lại hiệu quả truy xuất cao nhất cho bài toán RAG hỗ trợ khách hàng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> Nhóm sẽ thiết kế thêm bước **Reranking** (xếp hạng lại) sau khi truy xuất Top-k để ưu tiên các chunk chứa thông tin thời gian/con số cụ thể, đồng thời chuẩn hóa triệt để cấu trúc Markdown Header cho tất cả tài liệu ngay từ khâu cào dữ liệu (crawling).

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                   | Điểm tự đánh giá |
| -------------------------------------------- | ---------------------- |
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10                |
| Thiết kế chiến lược (Strategy Design)   | 15 / 15                |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10                |
| Thuyết trình (Demo)                        | 0 / 5                  |
| **Tổng phần nhóm**                  | **35 / 40**      |
