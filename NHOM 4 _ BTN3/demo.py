import streamlit as st
from pdf import generate_pdf
from readdata import process_financial_data
from drawchart import draw_chart

st.title("📝 The Professional Business Intelligence Times")

# Thanh tìm kiếm đúng chuẩn
search_query = st.text_input("🔍 Tìm kiếm mã cổ phiếu", "", placeholder="Nhập mã hoặc tên công ty...")

# Khi người dùng nhập xong
if search_query:
    # Gọi hàm xử lý dữ liệu
    transposed_df = process_financial_data(search_query)

    if not transposed_df.empty:
        # Lấy thông tin tên công ty và mã cổ phiếu từ DataFrame gốc
        company_name = transposed_df.loc[transposed_df['Chỉ tiêu'] == 'TÊN CÔNG TY', '2024'].values[0]
        exchange_code = transposed_df.loc[transposed_df['Chỉ tiêu'] == 'MÃ', '2024'].values[0]

        st.write(f"**🏢 Tên công ty:** {company_name}")
        st.write(f"**📈 Mã cổ phiếu:** {exchange_code}")

        # Nút xuất báo cáo PDF
        if st.button("📄 Xuất báo cáo PDF"):
            with st.spinner("⏳ Đang tạo biểu đồ..."):
                draw_chart(search_query)
            with st.spinner("⏳ Đang tạo báo cáo PDF..."):
                generate_pdf(search_query)
            st.success(f"✅ Báo cáo PDF cho {company_name} ({exchange_code}) đã được tạo thành công!")

    else:
        st.error("❌ Không tìm thấy dữ liệu. Vui lòng kiểm tra lại!")
