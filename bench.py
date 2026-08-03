import os
import sys
import time

# Trỏ đường dẫn Python vào thư mục chứa code src/ của Kiều Trang
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "report", "TranThiKieuTrang_2A202601498"))

# Đảm bảo in tiếng Việt không bị lỗi trên Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv(override=False)

import google.generativeai as genai

from ingest import build_knowledge_base
from src.chunking import FixedSizeChunker
from src.agent import KnowledgeBaseAgent

# ── Cấu hình Gemini API ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash")


def gemini_embedder(text: str) -> list[float]:
    """Sử dụng Gemini API (models/gemini-embedding-001) để tạo vector embedding 3072 chiều."""
    try:
        res = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return res['embedding']
    except Exception as e:
        print(f"       ⚠️ Gemini Embedding Error: {e}")
        # Fallback nếu gặp lỗi
        import hashlib, math
        digest = hashlib.md5(text.encode()).hexdigest()
        seed = int(digest, 16)
        vec = []
        for _ in range(64):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vec.append((seed / 0xFFFFFFFF) * 2 - 1)
        norm = math.sqrt(sum(v*v for v in vec)) or 1.0
        return [v/norm for v in vec]


def gemini_llm(prompt: str) -> str:
    """Gọi Gemini 2.5 Flash API để sinh câu trả lời từ context."""
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[Lỗi gọi Gemini]: {e}"


def main():
    print("=" * 80)
    print("  BENCHMARK 100% GEMINI API: TranThiKieuTrang — FixedSizeChunker(400, overlap=0)")
    print("  Embedding Backend: Gemini Text Embedding API (gemini-embedding-001)")
    print("  LLM Backend: Gemini 2.5 Flash (Google AI)")
    print("=" * 80)

    # 1. Chọn chunker của Kiều Trang
    chunker = FixedSizeChunker(chunk_size=400, overlap=0)

    # 2. Nạp dữ liệu sử dụng Gemini Embedder thật
    print("\n⏳ Đang nhúng dữ liệu bằng Gemini Embedding API...")
    store = build_knowledge_base("data/k4_crawled", gemini_embedder, chunker=chunker)
    print(f"✅ Đã nạp tổng cộng {store.get_collection_size()} chunks vào hệ thống bằng Gemini Embedding!\n")

    # 3. Khởi tạo Agent sử dụng Gemini LLM
    agent = KnowledgeBaseAgent(store, llm_fn=gemini_llm)

    # 4. Chạy 5 query đánh giá của nhóm
    queries = [
        "Sản phẩm được mua tại GearVN sẽ được đổi mới trong vòng bao nhiêu ngày nếu phát sinh lỗi từ nhà sản xuất đối với các sản phẩm gaming gear?",
        "Thời gian tối đa để gửi chuyển trả sản phẩm lỗi cho GearVN là bao lâu?",
        "Khi thanh toán bằng ZaloPay trên website GearVN, tôi cần làm gì sau khi chọn hình thức thanh toán này?",
        "Phí vận chuyển của CellphoneS cho đơn hàng 250.000đ đối với người mua bình thường (không phải thành viên Smem/SVip) là bao nhiêu?",
        "Nếu tôi hủy đơn hàng CellphoneS và đã thanh toán qua thẻ ATM, tôi sẽ nhận lại tiền trong bao lâu?"
    ]

    # Metadata filter tương ứng (Câu 4 có filter buyer)
    filters = [None, None, None, {"customer_role": "buyer"}, None]

    for i, query in enumerate(queries):
        print(f"\n{'='*80}")
        print(f"🔴 CÂU HỎI {i+1}: {query}")
        if filters[i]:
            print(f"   [Filter metadata: {filters[i]}]")
        print("-" * 80)

        results = store.search_with_filter(query, top_k=3, metadata_filter=filters[i])

        for j, r in enumerate(results, start=1):
            doc_id = r['metadata'].get('doc_id', 'unknown')
            preview = r['content'][:200].replace('\n', ' ')
            print(f"   Top {j} [Score={r['score']:.4f} | File={doc_id}]:")
            print(f"       {preview}...")

        # Gọi Agent với Gemini AI
        print(f"\n   🤖 GEMINI AGENT ANSWER:")
        answer = agent.answer(query, top_k=3)
        print(f"   {answer}")
        print("-" * 80)
        time.sleep(2)

    print("\n" + "=" * 80)
    print("  BENCHMARK HOÀN TẤT")
    print("=" * 80)


if __name__ == "__main__":
    main()
