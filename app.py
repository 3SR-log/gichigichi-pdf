import streamlit as st
import io
from pypdf import PdfReader, PdfWriter, PageObject, Transformation

st.set_page_config(page_title="PDF N-up Grid Generator", layout="centered")

st.title("📄 PDF ギチギチレイアウトツール")
st.write("「テスト前なのにパワポの印刷機能では余白が多くてカンペが上手く作れない、、、」")
st.write("パワポをそのままPDF化してアップロード→お好みの枚数構成を選択→ギチギチに敷き詰めたPDF完成✨️")

# --- UI設定項目 ---
uploaded_file = st.file_uploader("PDFファイルを選択してください", type=["pdf"])

# 配置プリセットの選択
layout_option = st.selectbox(
    "1ページあたりの配置構成を選択してください",
    options=[
        "3 × 5 (15枚) - 余白最小・最大密度",
        "3 × 4 (12枚) - A4縦にジャストサイズ",
        "3 × 3 (9枚) - 標準的な高密度配置",
        "2 × 3 (6枚) - 見やすさ重視",
        "2 × 2 (4枚) - 大判で見やすい",
        "4 × 4 (16枚) - 超高密度"
    ],
    index=0 # デフォルトは 3x5
)

# 選択肢から列数(cols)と行数(rows)を抽出
layout_map = {
    "3 × 5 (15枚) - 余白最小・最大密度": (3, 5),
    "3 × 4 (12枚) - A4縦にジャストサイズ": (3, 4),
    "3 × 3 (9枚) - 標準的な高密度配置": (3, 3),
    "2 × 3 (6枚) - 見やすさ重視": (2, 3),
    "2 × 2 (4枚) - 大判で見やすい": (2, 2),
    "4 × 4 (16枚) - 超高密度": (4, 4)
}
cols, rows = layout_map[layout_option]

# 詳細設定（アコーディオン）
with st.expander("詳細パラメータ設定（微調整用）"):
    margin = st.slider("外枠余白 (pt)", min_value=0, max_value=20, value=4)
    gap = st.slider("スライド間の隙間 (pt)", min_value=0, max_value=10, value=1)


# --- PDF変換ロジック ---
def process_nup(input_stream, cols, rows, margin_pt, gap_pt):
    reader = PdfReader(input_stream)
    writer = PdfWriter()
    
    total_pages = len(reader.pages)
    page_w, page_h = 595.28, 841.89  # A4縦 (ポイント単位)
    
    pages_per_sheet = cols * rows
    cell_w = (page_w - (margin_pt * 2) - (gap_pt * (cols - 1))) / cols
    cell_h = (page_h - (margin_pt * 2) - (gap_pt * (rows - 1))) / rows
    
    for group_idx in range(0, total_pages, pages_per_sheet):
        new_page = PageObject.create_blank_page(width=page_w, height=page_h)
        
        for i in range(pages_per_sheet):
            if group_idx + i >= total_pages:
                break
                
            src_page = reader.pages[group_idx + i]
            src_w = float(src_page.mediabox.width)
            src_h = float(src_page.mediabox.height)
            
            # 拡大縮小スケール計算
            scale = min(cell_w / src_w, cell_h / src_h)
            col = i % cols
            row = i // cols
            
            x = margin_pt + col * (cell_w + gap_pt)
            y = page_h - margin_pt - (row + 1) * cell_h + (cell_h - src_h * scale) / 2
            
            # トランスフォームの適用
            op = Transformation().scale(scale, scale).translate(x, y)
            temp_page = PageObject.create_blank_page(width=page_w, height=page_h)
            temp_page.merge_page(src_page)
            temp_page.add_transformation(op)
            
            new_page.merge_page(temp_page)
            
        writer.add_page(new_page)
        
    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream


# --- 実行処理 ---
if uploaded_file is not None:
    if st.button(f"PDFを変換する ({cols}x{rows} 配置)", type="primary"):
        with st.spinner("PDFを変換中..."):
            output_pdf = process_nup(uploaded_file, cols, rows, margin, gap)
            
        st.success("変換が完了しました！")
        
        # ダウンロードボタン
        st.download_button(
            label="📥 変換後のPDFをダウンロード",
            data=output_pdf,
            file_name=f"{cols}x{rows}_{uploaded_file.name}",
            mime="application/pdf"
        )
