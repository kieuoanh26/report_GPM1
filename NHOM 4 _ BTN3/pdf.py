import os
import platform
import subprocess
import datetime as dt
from fpdf import FPDF
from dotenv import load_dotenv
import requests
from datetime import datetime

from readdata import process_financial_data
from caculate import calculate_financial_ratios
from drawchart import draw_chart


# Hàm tạo PDF
def generate_pdf(stock_code):
    # Lấy dữ liệu tài chính
    transposed_df = process_financial_data(stock_code)
    if transposed_df.empty:
        print(f"Không tìm thấy dữ liệu cho mã cổ phiếu {stock_code}")
        return

    # Tính các chỉ số tài chính
    financial_ratios = calculate_financial_ratios(transposed_df)

    # Thông tin công ty
    today = dt.date.today()
    company_name = transposed_df.iloc[1]['2024']
    stock_symbol = transposed_df.iloc[0]['2024']
    exchange_code = transposed_df.iloc[2]['2024']
    industry = " - ".join(map(str, transposed_df.iloc[3:7]['2024'].values))

    # Dữ liệu thông tin chung
    general_info = [
        ("Tên công ty", company_name),
        ("Mã chứng khoán", stock_symbol),
        ("Sàn giao dịch", exchange_code),
        ("Ngành (ICB)", industry)
    ]

    # Dữ liệu bảng tài chính
    balance_sheet_data = {
        "Total Current Assets": financial_ratios["Total Current Assets"],
        "Property/Plant/Equipment": financial_ratios["Property/Plant/Equipment"],
        "Total Assets": financial_ratios["Total Assets"],
        "Total Current Liabilities": financial_ratios["Total Current Liabilities"],
        "Total Long-Term Debt": financial_ratios["Total Long-Term Debt"],
        "Total Liabilities": financial_ratios["Total Liabilities"]
    }

    fundamental_data = {
        "EBITDA": financial_ratios["EBITDA"]
    }

    income_statement_data = {
        "Revenue": financial_ratios["Revenue"],
        "Total Operating Expense": financial_ratios["Total Operating Expense"],
        "Net Income Before Taxes": financial_ratios["Net Income Before Taxes"],
        "Net Income After Taxes": financial_ratios["Net Income After Taxes"],
        "Net Income Before Extraordinary Items": financial_ratios["Net Income Before Extraordinary Items"]
    }

    profitability_analysis_data = {
        "ROE, %": financial_ratios["ROE"],
        "ROA, %": financial_ratios["ROA"],
        "Income After Tax Margin, %": financial_ratios["Income After Tax Margin"],
        "Revenue/Total Assets, %": financial_ratios["Revenue/Total Assets"],
        "Long Term Debt/Equity, %": financial_ratios["Long Term Debt/Equity"],
        "Total Debt/Equity, %": financial_ratios["Total Debt/Equity"],
        "ROS, %": financial_ratios["ROS"]
    }

    # Danh sách năm
    years = list(transposed_df.columns[1:])

    # Tạo lớp PDF kế thừa từ FPDF
    class PDF(FPDF):
        def header(self):
            # Thêm phông chữ 
            pdf.add_font("DejaVu", "", "Roboto-Regular.ttf", uni=True)  # Regular
            pdf.add_font("DejaVu", "B", "Roboto-Bold.ttf", uni=True)  # Bold
            pdf.add_font("DejaVu", "I", "Roboto-Italic.ttf", uni=True)  # Italic
            pdf.add_font("DejaVu", "BI", "Roboto-BoldItalic.ttf", uni=True)  # Bold Italic
            
            self.set_fill_color(0, 0, 128)  # Màu xanh navy (#000080)
            self.rect(0, 0, self.w, 28, 'F')# Tô nền header toàn trang (cao 20px) 
            # Sử dụng phông chữ DejaVu Sans, cỡ 16
            self.set_text_color(255, 255, 255)  # Màu xám đậm (RGB: 64, 64, 64)
            self.set_font('DejaVu', 'B', 16)
            self.cell(0, 10, company_name.upper(), 0, 1, 'R')  # Chuyển thành chữ hoa và căn phải

            # Dòng chứa Document Date, căn lề phải
            self.set_font('DejaVu', '', 10)  # Phông chữ DejaVu Sans, cỡ 8 cho Document Date
            self.cell(0, 5, f"Document Date: {today.strftime('%d-%b-%Y')}", 0, 1, 'R')

            self.ln(8)  # Thêm một khoảng trống nhỏ sau phần header
            
        def footer(self):
            # Vị trí 1.5 cm từ đáy trang
            self.set_y(-10)
            self.set_font('DejaVu', 'I', 8)  # Phông chữ nghiêng
            # Sử dụng `new_x` và `new_y` thay cho `ln` để không gặp cảnh báo DeprecationWarning
            self.cell(0, 5, f'Page {self.page_no()} of {{nb}}', 0, 1, 'C', new_x='RIGHT', new_y='NEXT')
        def chapter_title(self, title):
            self.set_text_color(0, 0, 128)  # Màu xanh dương cho chữ
            self.set_font('DejaVu', 'B', 13)  # Phông chữ đậm, cỡ 12 cho tiêu đề
            self.cell(0, 5, title, 0, 1, 'L')  # Title căn trái
            self.ln(5)

        def create_table_information(self, data): 
            
            # Vẽ đường nét đứt phía trên bảng
            self.set_draw_color(0, 0, 0)  # Màu xám đậm cho đường kẻ
            self.dashed_line(10, self.get_y(), 200, self.get_y(), 1, 1)  # (x1, y1, x2, y2, độ dài nét, khoảng cách)

            self.set_text_color(0, 0, 0)  # Màu chữ mặc định (đen)
            row_count = 0

            for item in data:
                # Tô màu nền xanh pastel cho hàng chẵn
                if row_count % 2 == 0:
                    self.set_fill_color(230, 240, 250)  # Màu xanh pastel 
                else:
                    self.set_fill_color(255, 255, 255)  # Màu trắng
        
                # Cột "Thông tin" có chữ xám đậm
                self.set_text_color(0, 0, 0)  # Màu xám 
                self.set_font('DejaVu', 'B', 8)  # Đậm hơn một chút

                self.cell(50, 6, item[0], 0, 0, 'L', fill=True)  

                # Cột "Giá trị" trở về màu đen bình thường
                self.set_text_color(0, 0, 0)  
                self.set_font('DejaVu', '', 8)  # Chữ thường

                self.cell(140, 6, item[1], 0, 1, 'L', fill=True)  

                row_count += 1
            # Vẽ đường nét đứt phía dưới bảng
            self.set_draw_color(0, 0, 0)
            end_y = self.get_y()  # Lưu vị trí kết thúc bảng
            self.dashed_line(10, end_y, 200, end_y, 1, 1)  # Đường nét đứt ngang
            
            self.ln(8)  # Thêm một khoảng trống sau bảng
        
        def create_table(self, title, data, years, header_color):
            self.set_font("DejaVu", "B", 8)

            # Chiều rộng trang A4 = 210mm, trừ đi lề 2 bên (10mm mỗi bên)
            page_width = 210 - 20  # 190mm là không gian sử dụng được
            col_width = page_width * 0.35  # 35% chiều rộng cho cột đầu tiên
            year_width = (page_width * 0.65) / len(years)  # 65% còn lại chia đều cho các năm

            self.set_x(10)  # Đặt vị trí x để bảng căn sát lề trái

            # Tiêu đề bảng trong ô đầu tiên với màu nền theo yêu cầu
            self.set_fill_color(*header_color)  # Đặt màu nền theo bảng cụ thể
            self.set_text_color(255, 255, 255)  # Màu chữ trắng cho dòng đầu tiên
            self.cell(col_width, 6, title, 0, 0, "L", fill=True)  # Không có viền
            for year in years:
                self.cell(year_width, 6, year, 0, 0, "R", fill=True)  # Căn phải
            self.ln()

            # In dữ liệu từng hàng
            self.set_x(10)  # Đảm bảo từng hàng bắt đầu từ lề trái
            self.set_font("DejaVu", "", 8)
            self.set_text_color(0, 0, 0)  # Đặt lại màu chữ đen cho các dòng tiếp theo
            row_count = 0
            line_height = 6

            for key, values in data.items():
                # Tô màu xen kẽ cho từng dòng (trừ dòng đầu tiên)
                self.set_fill_color(230, 240, 250) if row_count % 2 == 0 else self.set_fill_color(255, 255, 255)

                # In cột đầu tiên
                self.cell(col_width, line_height, key, 0, 0, "L", fill=True)

                # In dữ liệu theo từng năm (không viền, căn phải)
                for value in values:
                    self.cell(year_width, line_height, value, 0, 0, "R", fill=True)
                self.ln()
                row_count += 1

            self.ln(10)  # Tạo khoảng trống 10mm giữa các bảng

    pdf = PDF()
    pdf.add_page()
    pdf.create_table("BALANCE SHEET", balance_sheet_data, years,header_color=(128, 0, 0) )
    pdf.create_table("FUNDAMENTAL", fundamental_data, years, header_color=(0, 128, 0))
    pdf.create_table("INCOME STATEMENT", income_statement_data, years, header_color=(76, 0, 153))
    pdf.create_table("PROFITABILITY ANALYSIS", profitability_analysis_data, years, header_color=(0, 102, 204))
    import os
    import google.generativeai as genai
    import requests
    from dotenv import load_dotenv

    # Tải API key từ file môi trường
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    # Kiểm tra xem API key có tồn tại không
    if not api_key:
        raise ValueError("API Key chưa được đặt. Vui lòng kiểm tra file .env")

    # Cấu hình model Google Gemini
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        safety_settings=safety_settings,
        generation_config=generation_config,
        system_instruction="Chatbot này sẽ hoạt động như một broker chứng khoán chuyên nghiệp..."
    )

    # Kiểm tra nếu các biến dữ liệu chưa được khai báo
    balance_sheet = balance_sheet_data
    income_statement = income_statement_data
    profitability_analysis = profitability_analysis_data

    # Thêm thông tin chung và bảng BALANCE SHEET trên cùng một trang
    pdf.chapter_title("THÔNG TIN CHUNG")
    pdf.set_font("DejaVu", size=12)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    # Tạo nội dung prompt
    prompt = f""" 
    Bạn là một chuyên gia phân tích tài chính chuyên về phân tích cổ phiếu. Hãy đánh giá rủi ro và triển vọng đầu tư của một mã cổ phiếu dựa trên các chỉ số tài chính và thông tin sau.
Giữ văn phong chuyên nghiệp, phân tích súc tích, tổng số từ không quá 300 từ. 

📊 Dữ liệu tài chính:

Bảng cân đối kế toán (Balance Sheet):
{balance_sheet}
Báo cáo thu nhập (Income Statement):
{income_statement}
Phân tích khả năng sinh lời (Profitability Analysis):
{profitability_analysis}
🔍 Yêu cầu phân tích:

1️⃣ PHÂN TÍCH TÀI CHÍNH (Dưới 200 từ)
Hãy đánh giá các chỉ số tài chính quan trọng sau:

Thanh khoản:
Chỉ số thanh toán hiện thời (Current Ratio),
Chỉ số thanh toán nhanh (Quick Ratio).
Hiệu quả hoạt động:
ROA (Return on Assets),
ROE (Return on Equity).
Hiệu suất kinh doanh:
Vòng quay khoản phải thu (Receivables Turnover),
Vòng quay tài sản cố định (Fixed Asset Turnover).
Đòn bẩy tài chính:
Chỉ số nợ trên tài sản (Debt to Assets),
Chỉ số nợ trên vốn chủ sở hữu (Debt to Equity),
Khả năng trả lãi vay (Interest Coverage Ratio).
Tỷ suất sinh lời:
Tỷ suất lợi nhuận trên doanh thu (ROS - Return on Sales),
Chỉ số EPS (Earnings Per Share),
Chỉ số P/E (Price to Earnings Ratio).
👉 Nhận xét: Xu hướng tăng trưởng qua các năm, so sánh với trung bình ngành.

2️⃣ SO SÁNH VỚI TRUNG BÌNH NGÀNH (Dưới 100 từ)
So sánh các chỉ số sau với trung bình ngành để đánh giá vị thế công ty:

Vòng quay hàng tồn kho (Inventory Turnover).
Tỷ số nợ trên vốn chủ sở hữu (Debt to Equity).
Tỷ số nợ trên tài sản (Debt to Assets).
So sánh ROA, ROE với trung bình ngành.
👉 Nhận xét: Công ty có lợi thế cạnh tranh hay không?

3️⃣ PHÂN TÍCH KỸ THUẬT (Dưới 100 từ)
Sử dụng dữ liệu giá cổ phiếu để đánh giá xu hướng:

Moving Average (MA): Xu hướng giá ngắn hạn và dài hạn.
Bollinger Bands: Đánh giá mức độ biến động.
RSI (Relative Strength Index): Xác định vùng quá mua/quá bán.
MACD (Moving Average Convergence Divergence): Đánh giá xu hướng tăng/giảm.
Stochastic Oscillator: Xác định tín hiệu mua/bán.
👉 Nhận xét: Xu hướng giá cổ phiếu hiện tại có tích cực không?

4️⃣ KẾT LUẬN: ĐÁNH GIÁ RỦI RO & TRIỂN VỌNG ĐẦU TƯ
Rủi ro tài chính: Thanh khoản, đòn bẩy, dòng tiền.
Tiềm năng tăng trưởng: Doanh thu, lợi nhuận, hiệu quả sử dụng vốn.
Khuyến nghị: Mua, giữ hay bán?
🎯 Định dạng đầu ra mong muốn:

Đoạn văn súc tích (<300 từ), logic, có kết luận rõ ràng.
Trích dẫn số liệu cụ thể từ dữ liệu {balance_sheet}, {income_statement}, {profitability_analysis}.
👉 Mục tiêu: Cung cấp báo cáo tài chính & kỹ thuật ngắn gọn, giúp nhà đầu tư ra quyết định nhanh chóng.
    """

    headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }


    try:
        response = model.generate_content(prompt)
        result = response.text
        formatted_comment = result.replace("*", "")
        print("API Response:", formatted_comment)  # Kiểm tra phản hồi từ API
    except Exception as e:
        print(f"Lỗi khi gọi API: {str(e)}")
        
    # Khởi tạo đối tượng PDF
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Thêm thông tin chung và bảng BALANCE SHEET trên cùng một trang
    pdf.chapter_title("THÔNG TIN CHUNG")
    pdf.set_font("DejaVu", size=12)
    pdf.set_text_color(0, 0, 0)  # Màu chữ đen
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    info = [
        f"🏢 Tên công ty: {company_name}",
        f"📈 Mã cổ phiếu: {stock_symbol}",
        f"🏛️ Sàn giao dịch: {exchange_code}"
    ]

    # Dùng pdf.cell() cho các dòng ngắn
    for line in info:
        pdf.cell(0, 10, line, ln=True)

    # Dùng pdf.multi_cell() cho dòng dài
    pdf.multi_cell(0, 10, f"🏭 Ngành nghề: {industry}")
    pdf.ln(5)  # Giảm khoảng cách giữa phần thông tin và bảng
    
    # Thêm bảng BALANCE SHEET ngay trên cùng trang
    pdf.create_table("BALANCE SHEET", balance_sheet_data, years,header_color=(128, 0, 0) )
    pdf.create_table("FUNDAMENTAL", fundamental_data, years, header_color=(0, 128, 0))
    pdf.create_table("INCOME STATEMENT", income_statement_data, years, header_color=(76, 0, 153))
    pdf.create_table("PROFITABILITY ANALYSIS", profitability_analysis_data, years, header_color=(0, 102, 204))

    # Thêm 4 biểu đồ vào PDF
    pdf.add_page()
    pdf.chapter_title("BIỂU ĐỒ")
    pdf.image(f"images/output/revenue_totalassets_equity_{stock_code}.png", x=45, y=35, w=120, h=100)
    pdf.image(f"images/output/asset_structure_{stock_code}.png", x=45, y=145, w=120, h=100)

    pdf.add_page()
    pdf.chapter_title("BIỂU ĐỒ")
    pdf.image(f"images/output/equity_roe_roa_{stock_code}.png", x=45, y=35, w=120, h=100)
    pdf.image(f"images/output/income_after_tax_margin_{stock_code}.png", x=45, y=145, w=120, h=100)

   # Trang cuối: Nhận xét từ AI
    pdf.add_page()
    pdf.chapter_title("NHẬN XÉT TÀI CHÍNH")
    pdf.set_font("DejaVu", size=12)
    pdf.set_text_color(0, 0, 0) 
    # Chèn nhận xét đã được định dạng (xóa dấu *) vào PDF
    pdf.multi_cell(0, 10, formatted_comment)
    

    # Xuất file PDF
    pdf_filename = f"{stock_symbol}_FINANCIAL_REPORT.pdf"
    pdf.output(pdf_filename)
    print(f"PDF file created successfully: {pdf_filename}")
    def open_file(file_path):
        system_name = platform.system()
        
        if system_name == "Windows":
            os.startfile(file_path)  # Chỉ dùng cho Windows
        elif system_name == "Darwin":  # macOS
            subprocess.run(["open", file_path])
        elif system_name == "Linux":
            subprocess.run(["xdg-open", file_path])
        else:
            print(f"Không hỗ trợ mở file trên hệ điều hành {system_name}")

    # Gọi hàm này khi muốn mở PDF
    open_file(pdf_filename)
