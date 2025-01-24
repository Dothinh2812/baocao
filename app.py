from flask import Flask, render_template, request, send_file, session
import pandas as pd
import io
import matplotlib
matplotlib.use('Agg')  # Thêm dòng này
import matplotlib.pyplot as plt
import base64

app = Flask(__name__)

# Thêm secret key cho session
app.secret_key = 'your_secret_key_here'  # Thay đổi thành một key phức tạp và bảo mật

# Thêm biến global để lưu trữ các DataFrame
thong_ke_doivt = None # biến của DHSC
thong_ke_nhomvt_bavi = None # biến của DHSC
thong_ke_nhomvt_phuctho = None # biến của DHSC
thong_ke_nhomvt_danphuong = None # biến của DHSC
thong_ke_nhomvt_sontay = None # biến của DHSC
thong_ke_nhomvt_thachthat = None # biến của DHSC
df_filtered = None # biến của DHSC  
df_pttb = None # biến của pttb
thong_ke_chung = None #biến của pttb


ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/DHSC', methods=['GET', 'POST'])
def dhsc():
    global thong_ke_doivt, thong_ke_nhomvt_bavi, thong_ke_nhomvt_phuctho, thong_ke_nhomvt_danphuong, thong_ke_nhomvt_sontay, thong_ke_nhomvt_thachthat, df_filtered
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Không có file được tải lên."
        file = request.files['file']
        if file.filename == '':
            return "Không có file được chọn."
        if file and allowed_file(file.filename):
            try:
                # Đọc file excel, header ở dòng thứ 2 (index 1)
                df = pd.read_excel(file, header=1)

                # Lọc dữ liệu theo cột DOIVT
                allowed_doivt = ['Thạch Thất', 'Sơn Tây', 'Ba Vì', 'Phúc Thọ', 'Đan Phượng']
                df_filtered = df[df['DOIVT'].isin(allowed_doivt)].copy()

                # Tạo bảng thống kê số lượng máy hỏng
                thong_ke_doivt = df_filtered.groupby('DOIVT').size().reset_index(name='Số lượng máy hỏng')
                thong_ke_doivt.insert(0, 'STT', range(1, len(thong_ke_doivt) + 1))
                thong_ke_doivt.rename(columns={'DOIVT': 'Đội VT'}, inplace=True)

                # Thêm cột Fiber
                fiber_counts = df_filtered[df_filtered['LOAIHINH_TB'] == 'Fiber'].groupby('DOIVT').size().reset_index(name='Fiber')
                fiber_counts.rename(columns={'DOIVT': 'Đội VT'}, inplace=True)

                thong_ke_doivt = pd.merge(thong_ke_doivt, fiber_counts, on='Đội VT', how='left')
                thong_ke_doivt['Fiber'] = thong_ke_doivt['Fiber'].fillna(0).astype(int)

                # Thêm cột MyTV
                mytv_counts = df_filtered[df_filtered['LOAIHINH_TB'] == 'MyTV'].groupby('DOIVT').size().reset_index(name='MyTV')
                mytv_counts.rename(columns={'DOIVT': 'Đội VT'}, inplace=True)

                thong_ke_doivt = pd.merge(thong_ke_doivt, mytv_counts, on='Đội VT', how='left')
                thong_ke_doivt['MyTV'] = thong_ke_doivt['MyTV'].fillna(0).astype(int)

                # Thêm cột SIP
                SIP_counts = df_filtered[df_filtered['LOAIHINH_TB'] == 'Thuê bao SIP'].groupby('DOIVT').size().reset_index(name='Thuê bao SIP')
                SIP_counts.rename(columns={'DOIVT': 'Đội VT'}, inplace=True)

                thong_ke_doivt = pd.merge(thong_ke_doivt, SIP_counts, on='Đội VT', how='left')
                thong_ke_doivt['Thuê bao SIP'] = thong_ke_doivt['Thuê bao SIP'].fillna(0).astype(int)


# --- BỔ SUNG CHỨC NĂNG MỚI ---
                # Lọc dữ liệu cho Đội VT Ba Vì
                df_bavi = df_filtered[df_filtered['DOIVT'] == 'Ba Vì'].copy()

                # Định dạng lại cột NHOMVT
                df_bavi.loc[:, 'NHOMVT'] = df_bavi['NHOMVT'].str.split(' - ').str[1].str.strip()

                # Group by theo NHOMVT cho Ba Vì
                thong_ke_nhomvt_bavi = df_bavi.groupby('NHOMVT').size().reset_index(name='Số lượng')
                thong_ke_nhomvt_bavi.insert(0, 'STT', range(1, len(thong_ke_nhomvt_bavi) + 1))


# --- BỔ SUNG CHỨC NĂNG MỚI ---
                # Lọc dữ liệu cho Đội VT Phúc Thọ
                df_phuctho = df_filtered[df_filtered['DOIVT'] == 'Phúc Thọ'].copy()

                # Định dạng lại cột NHOMVT
                # 1. Tách chuỗi theo dấu '-' và lấy phần thứ 2
                # 2. Loại bỏ nội dung trong dấu ngoặc đơn và khoảng trắng thừa
                df_phuctho.loc[:, 'NHOMVT'] = (df_phuctho['NHOMVT']
                                              .str.split('-').str[1]
                                              .str.replace(r'\([^)]*\)', '', regex=True)  # Loại bỏ nội dung trong ()
                                              .str.strip())  # Loại bỏ khoảng trắng thừa

                # Group by theo NHOMVT cho Phúc Thọ
                thong_ke_nhomvt_phuctho = df_phuctho.groupby('NHOMVT').size().reset_index(name='Số lượng')
                thong_ke_nhomvt_phuctho.insert(0, 'STT', range(1, len(thong_ke_nhomvt_phuctho) + 1))

# --- BỔ SUNG CHỨC NĂNG MỚI ---
                # Lọc dữ liệu cho Đội VT Đan Phượng
                df_danphuong = df_filtered[df_filtered['DOIVT'] == 'Đan Phượng'].copy()

                # Định dạng lại cột NHOMVT
                df_danphuong.loc[:, 'NHOMVT'] = df_danphuong['NHOMVT'].str.split('-').str[1].str.strip()

                # Group by theo NHOMVT cho Đan Phượng
                thong_ke_nhomvt_danphuong = df_danphuong.groupby('NHOMVT').size().reset_index(name='Số lượng')
                thong_ke_nhomvt_danphuong.insert(0, 'STT', range(1, len(thong_ke_nhomvt_danphuong) + 1))


# --- BỔ SUNG CHỨC NĂNG MỚI ---
                # Lọc dữ liệu cho Đội VT Sơn Tây
                df_sontay = df_filtered[df_filtered['DOIVT'] == 'Sơn Tây'].copy()

                # Định dạng lại cột NHOMVT
                df_sontay.loc[:, 'NHOMVT'] = df_sontay['NHOMVT'].str.split('-').str[1].str.strip()

                # Group by theo NHOMVT cho Sơn Tây
                thong_ke_nhomvt_sontay = df_sontay.groupby('NHOMVT').size().reset_index(name='Số lượng')
                thong_ke_nhomvt_sontay.insert(0, 'STT', range(1, len(thong_ke_nhomvt_sontay) + 1))

# --- BỔ SUNG CHỨC NĂNG MỚI ---
                # Lọc dữ liệu cho Đội VT Thạch Thất
                df_thachthat = df_filtered[df_filtered['DOIVT'] == 'Thạch Thất'].copy()

                # Định dạng lại cột NHOMVT
                df_thachthat.loc[:, 'NHOMVT'] = df_thachthat['NHOMVT'].str.split('-').str[1].str.strip()

                # Group by theo NHOMVT cho Thạch Thất
                thong_ke_nhomvt_thachthat = df_thachthat.groupby('NHOMVT').size().reset_index(name='Số lượng')
                thong_ke_nhomvt_thachthat.insert(0, 'STT', range(1, len(thong_ke_nhomvt_thachthat) + 1))

                # Tạo file Excel KET_QUA trong bộ nhớ
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    thong_ke_doivt.to_excel(writer, sheet_name='THONG_KE_DOIVT', index=False)
                    thong_ke_nhomvt_bavi.to_excel(writer, sheet_name='Ba Vì', index=False)
                    thong_ke_nhomvt_phuctho.to_excel(writer, sheet_name='Phúc Thọ', index=False)
                    thong_ke_nhomvt_danphuong.to_excel(writer, sheet_name='Đan Phượng', index=False)
                    thong_ke_nhomvt_sontay.to_excel(writer, sheet_name='Sơn Tây', index=False)
                    thong_ke_nhomvt_thachthat.to_excel(writer, sheet_name='Thạch Thất', index=False)

                output.seek(0)
                # Lưu file Excel vào session để tải xuống sau
                excel_data = output.getvalue()


                # Tạo đồ thị cho tổng quan
                chart_image = create_chart(thong_ke_doivt)
                # Tạo đồ thị cho Ba Vì
                chart_bavi = create_chart_bavi(thong_ke_nhomvt_bavi)
                # Tạo đồ thị cho Phúc Thọ
                chart_phuctho = create_chart_phuctho(thong_ke_nhomvt_phuctho)
                # Tạo đồ thị cho Sơn Tây
                chart_sontay = create_chart_sontay(thong_ke_nhomvt_sontay)
                # Tạo đồ thị cho Thạch Thất
                chart_thachthat = create_chart_thachthat(thong_ke_nhomvt_thachthat)
                # Tạo đồ thị cho Đan Phượng
                chart_danphuong = create_chart_danphuong(thong_ke_nhomvt_danphuong)
                

                

                
                # Đánh dấu trạng thái đã xử lý file trong session
                session['dhsc_file_processed'] = True
                session['has_data'] = True
                
                return render_template('dhsc.html', 
                                    chart_image=chart_image,
                                    chart_bavi=chart_bavi,
                                    chart_phuctho=chart_phuctho,
                                    chart_sontay=chart_sontay,
                                    chart_thachthat=chart_thachthat,
                                    chart_danphuong=chart_danphuong,
                                    show_download=True,
                                    show_download_chitiet=True,
                                    show_download_chitiet_phuctho=True,
                                    show_download_chitiet_danphuong=True,
                                    show_download_chitiet_sontay=True,
                                    show_download_chitiet_thachthat=True)

            except Exception as e:
                session['dhsc_file_processed'] = False
                session['has_data'] = False
                return f"Có lỗi xảy ra trong quá trình xử lý: {str(e)}"
        else:
            return "Định dạng file không được hỗ trợ. Vui lòng tải lên file Excel."
    return render_template('dhsc.html')



################################  phần tạo các đồ thị của báo cáo DHSC ############################################################

def create_bar_chart(df, x_column, y_column, title, xlabel=None, ylabel=None, width=0.4):
    """
    Tạo biểu đồ cột với độ rộng cột cố định
    """
    plt.figure(figsize=(12, 6))
    bars = plt.bar(df[x_column], df[y_column], width=width)  # Đặt độ rộng cột = 0.4
    plt.title(title)
    plt.xlabel(xlabel if xlabel else x_column)
    plt.ylabel(ylabel if ylabel else y_column)
    plt.xticks(rotation=45, ha='right')
    
    # Thêm giá trị trên đỉnh của mỗi cột
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom')
    
    # Lưu biểu đồ vào buffer
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    
    # Chuyển đổi sang base64
    graph_url = base64.b64encode(img.getvalue()).decode()
    return f'data:image/png;base64,{graph_url}'

# Sử dụng hàm chung cho các biểu đồ
def create_chart(df):
    return create_bar_chart(
        df=df,
        x_column='Đội VT',
        y_column='Số lượng máy hỏng',
        title='Thống kê số lượng máy hỏng theo Đội VT',
        xlabel='Đội VT',
        ylabel='Số lượng máy hỏng',
        width=0.4
    )

def create_chart_bavi(df):
    return create_bar_chart(
        df=df,
        x_column='NHOMVT',
        y_column='Số lượng',
        title='Thống kê số lượng máy hỏng theo Nhóm VT - Ba Vì',
        xlabel='Nhóm VT',
        ylabel='Số lượng',
        width=0.4
    )

def create_chart_phuctho(df):
    return create_bar_chart(
        df=df,
        x_column='NHOMVT',
        y_column='Số lượng',
        title='Thống kê số lượng máy hỏng theo Nhóm VT - Phúc Thọ',
        xlabel='Nhóm VT',
        ylabel='Số lượng',
        width=0.4
    )

def create_chart_sontay(df):
    return create_bar_chart(
        df=df,
        x_column='NHOMVT',
        y_column='Số lượng',
        title='Thống kê số lượng máy hỏng theo Nhóm VT - Sơn Tây',
        xlabel='Nhóm VT',
        ylabel='Số lượng',
        width=0.4
    )

def create_chart_thachthat(df):
    return create_bar_chart(
        df=df,
        x_column='NHOMVT',
        y_column='Số lượng',
        title='Thống kê số lượng máy hỏng theo Nhóm VT - Thạch Thất',
        xlabel='Nhóm VT',
        ylabel='Số lượng',
        width=0.4
    )

def create_chart_danphuong(df):
    return create_bar_chart(
        df=df,
        x_column='NHOMVT',
        y_column='Số lượng',
        title='Thống kê số lượng máy hỏng theo Nhóm VT - Đan Phượng',
        xlabel='Nhóm VT',
        ylabel='Số lượng',
        width=0.4
    )
##########################################################################################################################

# Thêm route mới để tải file Excel
@app.route('/download_excel')
def download_excel():
    if not session.get('dhsc_file_processed', False):
        return "Vui lòng xử lý file trước khi tải xuống"
    
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            thong_ke_doivt.to_excel(writer, sheet_name='THONG_KE_DOIVT', index=False)
            thong_ke_nhomvt_bavi.to_excel(writer, sheet_name='Ba Vì', index=False)
            thong_ke_nhomvt_phuctho.to_excel(writer, sheet_name='Phúc Thọ', index=False)
            thong_ke_nhomvt_danphuong.to_excel(writer, sheet_name='Đan Phượng', index=False)
            thong_ke_nhomvt_sontay.to_excel(writer, sheet_name='Sơn Tây', index=False)
            thong_ke_nhomvt_thachthat.to_excel(writer, sheet_name='Thạch Thất', index=False)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='KET_QUA.xlsx'
        )
    except Exception as e:
        return f"Có lỗi xảy ra: {str(e)}"

# Định nghĩa route để tải file chi tiết cho đội Ba Vì
@app.route('/download_chitiet_bavi')
def download_chitiet_bavi():
    if not session.get('dhsc_file_processed', False):
        return "Vui lòng xử lý file trước khi tải xuống"
    
    try:
        # Danh sách tên các nhân viên cần tạo sheet riêng
        nhan_vien_list = [
            'Bùi Văn Biên', 'Chu Minh Tám', 'Hoàng Tuấn Hải', 'Lê Phương Thuyết',
            'Lê Quyết Tiến', 'Nguyễn Chí Công', 'Nguyễn Quảng Ba', 'Nguyễn Tất Mạnh',
            'Nguyễn Văn Thanh', 'Phùng Công Vinh', 'Trần Thành', 'Trịnh Xuân Bách',
            'Đào Ngọc Hải', 'Đỗ Anh Mẫn', 'Đỗ Quyết Tiến', 'Đỗ Trần Quý', 'Đỗ Đức Trí'
        ]
        
        # Danh sách các cột cần hiển thị trong file chi tiết
        columns_to_keep = [
            'MA_MEN',           # Mã MEN
            'MA_TB',            # Mã thuê bao
            'GHICHU_HONG',      # Ghi chú hỏng
            'TEN_TB',           # Tên thuê bao
            'DIACHI_LD',        # Địa chỉ lắp đặt
            'GIO_DA_QUA',       # Số giờ đã qua
            'LOAIHINH_TB',      # Loại hình thuê bao
            'DIENTHOAI_LH'      # Điện thoại liên hệ
        ]
        
        # Lọc dữ liệu chỉ lấy các bản ghi thuộc đội Ba Vì
        df_bavi = df_filtered[df_filtered['DOIVT'] == 'Ba Vì'].copy()
        
        # Tạo buffer trong bộ nhớ để lưu file Excel
        output = io.BytesIO()
        
        # Tạo ExcelWriter với engine xlsxwriter để ghi nhiều sheet
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Duyệt qua từng nhân viên trong danh sách
            for nhan_vien in nhan_vien_list:
                # Lọc dữ liệu của từng nhân viên dựa vào tên trong cột NHOMVT
                df_nhan_vien = df_bavi[df_bavi['NHOMVT'].str.contains(nhan_vien, na=False)].copy()
                
                # Chỉ giữ lại các cột đã được chỉ định trong columns_to_keep
                df_nhan_vien = df_nhan_vien[columns_to_keep]
                
                # Ghi dữ liệu vào sheet với tên là tên nhân viên
                df_nhan_vien.to_excel(writer, sheet_name=nhan_vien, index=False)
            
        # Đưa con trỏ về đầu buffer để chuẩn bị đọc
        output.seek(0)
        
        # Trả về file Excel để người dùng tải xuống
        return send_file(
            output,  # Buffer chứa dữ liệu file Excel
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # Định dạng MIME cho file Excel
            as_attachment=True,  # Cho phép tải xuống thay vì mở trực tiếp
            download_name='Chi_tiet_BaVi.xlsx'  # Tên file khi tải xuống
        )
        
    # Bắt và xử lý các lỗi có thể xảy ra
    except Exception as e:
        return f"Có lỗi xảy ra: {str(e)}"


#tạo file chi tiết cho Đội VT Phúc Thọ

@app.route('/download_chitiet_phuctho')
def download_chitiet_phuctho():
    if not session.get('dhsc_file_processed', False):
        return "Vui lòng xử lý file trước khi tải xuống"
    
    try:
        # Danh sách các nhân viên cần tạo sheet
        nhan_vien_list = [
            'Bùi Văn Duẩn', 'Hoàng Tung', 'Khuất Anh Chiến', 'Khuất Duy Hiệp',
            'Nguyễn Huy Tuyến', 'Nguyễn Mạnh Hùng', 'Trần Huy Soát', 'Vương Văn Chung',
            'Vương Văn Khánh', 'Đỗ Hữu Nghị'
        ]
        
        
        # Các cột cần giữ lại
        columns_to_keep = ['MA_MEN', 'MA_TB', 'GHICHU_HONG', 'TEN_TB', 
                          'DIACHI_LD', 'GIO_DA_QUA', 'LOAIHINH_TB', 'DIENTHOAI_LH']
        
        # Lọc dữ liệu cho Đội VT Phúc Thọ
        df_phuctho = df_filtered[df_filtered['DOIVT'] == 'Phúc Thọ'].copy()
        
        # Tạo file Excel mới
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Tạo sheet cho từng nhân viên
            for nhan_vien in nhan_vien_list:
                # Lọc dữ liệu cho từng nhân viên
                df_nhan_vien = df_phuctho[df_phuctho['NHOMVT'].str.contains(nhan_vien, na=False)].copy()
                # Chỉ giữ lại các cột được yêu cầu
                df_nhan_vien = df_nhan_vien[columns_to_keep]
                # Ghi vào sheet mới
                df_nhan_vien.to_excel(writer, sheet_name=nhan_vien, index=False)
            
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='Chi_tiet_PhucTho.xlsx'
        )
        
    except Exception as e:
        return f"Có lỗi xảy ra: {str(e)}"

@app.route('/download_chitiet_danphuong')
def download_chitiet_danphuong():
    if not session.get('dhsc_file_processed', False):
        return "Vui lòng xử lý file trước khi tải xuống"
    
    try:
        # Danh sách các nhân viên cần tạo sheet
        nhan_vien_list = [
            'Bùi Anh Tuấn', 'Cao Anh Thọ', 'Kim Ngọc Trực', 'Lê Văn Sơn',
            'Lê Văn Tiếp', 'Lưu Mạnh Hùng', 'Nguyễn Hữu Thọ', 'Nguyễn Xuân Bình',
            'Nguyễn Đình Thắng', 'Trần Anh Tuấn', 'Tạ Thạc Yên', 'Tạ Đình Kiên',
            'Đặng Xuân Tập'
        ]
        
        # Các cột cần giữ lại
        columns_to_keep = ['MA_MEN', 'MA_TB', 'GHICHU_HONG', 'TEN_TB', 
                          'DIACHI_LD', 'GIO_DA_QUA', 'LOAIHINH_TB', 'DIENTHOAI_LH']
        
        # Lọc dữ liệu cho Đội VT Đan Phượng
        df_danphuong = df_filtered[df_filtered['DOIVT'] == 'Đan Phượng'].copy()
        
        # Tạo file Excel mới
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Tạo sheet cho từng nhân viên
            for nhan_vien in nhan_vien_list:
                # Lọc dữ liệu cho từng nhân viên
                df_nhan_vien = df_danphuong[df_danphuong['NHOMVT'].str.contains(nhan_vien, na=False)].copy()
                # Chỉ giữ lại các cột được yêu cầu
                df_nhan_vien = df_nhan_vien[columns_to_keep]
                # Ghi vào sheet mới
                df_nhan_vien.to_excel(writer, sheet_name=nhan_vien, index=False)
            
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='Chi_tiet_DanPhuong.xlsx'
        )
        
    except Exception as e:
        return f"Có lỗi xảy ra: {str(e)}"

@app.route('/download_chitiet_sontay')
def download_chitiet_sontay():
    if not session.get('dhsc_file_processed', False):
        return "Vui lòng xử lý file trước khi tải xuống"
    
    try:
        # Danh sách các nhân viên cần tạo sheet
        nhan_vien_list = [
            'Hà Thanh Trọng', 'Hồ Việt Quyền', 'Khuất Duy Kết', 'Lê Văn Hoàng Anh',
            'Lê Văn Tuấn', 'Nguyễn Thành Sơn', 'Nguyễn Văn Minh', 'Phùng Tuấn Anh',
            'Phạm Anh Tuấn', 'Trần Bình Minh', 'Trần Văn Minh', 'Đỗ Huy Thông',
            'Đỗ Minh Thăng'
        ]
        
        # Các cột cần giữ lại
        columns_to_keep = ['MA_MEN', 'MA_TB', 'GHICHU_HONG', 'TEN_TB', 
                          'DIACHI_LD', 'GIO_DA_QUA', 'LOAIHINH_TB', 'DIENTHOAI_LH']
        
        # Lọc dữ liệu cho Đội VT Sơn Tây
        df_sontay = df_filtered[df_filtered['DOIVT'] == 'Sơn Tây'].copy()
        
        # Tạo file Excel mới
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Tạo sheet cho từng nhân viên
            for nhan_vien in nhan_vien_list:
                # Lọc dữ liệu cho từng nhân viên
                df_nhan_vien = df_sontay[df_sontay['NHOMVT'].str.contains(nhan_vien, na=False)].copy()
                # Chỉ giữ lại các cột được yêu cầu
                df_nhan_vien = df_nhan_vien[columns_to_keep]
                # Ghi vào sheet mới
                df_nhan_vien.to_excel(writer, sheet_name=nhan_vien, index=False)
            
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='Chi_tiet_SonTay.xlsx'
        )
        
    except Exception as e:
        return f"Có lỗi xảy ra: {str(e)}"

@app.route('/download_chitiet_thachthat')
def download_chitiet_thachthat():
    if not session.get('dhsc_file_processed', False):
        return "Vui lòng xử lý file trước khi tải xuống"
    
    try:
        # Danh sách các nhân viên cần tạo sheet
        nhan_vien_list = [
            'Cao Tuấn Thành', 'Kiều Nguyễn Hồng Lịch', 'Kiều Văn Tuyên', 'Nguyễn Duy Đại',
            'Nguyễn Hữu Quốc Khánh', 'Nguyễn Khương Tiên', 'Nguyễn Ngọc Hải', 'Nguyễn Trung Kiên',
            'Nguyễn Văn Cường', 'Nguyễn Văn Khánh', 'Nguyễn Đức Hòa', 'Phí Hùng Mạnh',
            'Trần Ngọc Đáng', 'Vương Vũ Tuấn', 'Đỗ Anh Đức', 'Đỗ Hữu Văn', 'Đỗ Xuân Định'
        ]
        
        # Các cột cần giữ lại
        columns_to_keep = ['MA_MEN', 'MA_TB', 'GHICHU_HONG', 'TEN_TB', 
                          'DIACHI_LD', 'GIO_DA_QUA', 'LOAIHINH_TB', 'DIENTHOAI_LH']
        
        # Lọc dữ liệu cho Đội VT Thạch Thất
        df_thachthat = df_filtered[df_filtered['DOIVT'] == 'Thạch Thất'].copy()
        
        # Tạo file Excel mới
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Tạo sheet cho từng nhân viên
            for nhan_vien in nhan_vien_list:
                # Lọc dữ liệu cho từng nhân viên
                df_nhan_vien = df_thachthat[df_thachthat['NHOMVT'].str.contains(nhan_vien, na=False)].copy()
                # Chỉ giữ lại các cột được yêu cầu
                df_nhan_vien = df_nhan_vien[columns_to_keep]
                # Ghi vào sheet mới
                df_nhan_vien.to_excel(writer, sheet_name=nhan_vien, index=False)
            
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='Chi_tiet_ThachThat.xlsx'
        )
        
    except Exception as e:
        return f"Có lỗi xảy ra: {str(e)}"

######################################################## route xử lý báo cáo pttb ####################################################
@app.route('/pttb', methods=['GET', 'POST'])
def pttb():
    global df_pttb, thong_ke_chung
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                app.logger.error('Không có file được tải lên')
                return "Không có file được tải lên."
                
            file = request.files['file']
            if file.filename == '':
                app.logger.error('Không có file được chọn')
                return "Không có file được chọn."
                
            if file and allowed_file(file.filename):
                app.logger.info(f'Bắt đầu xử lý file: {file.filename}')
                
                # Xử lý file Excel
                df_pttb = pd.read_excel(file, header=1)
                
                # Lọc dữ liệu theo DOIVT_KV
                allowed_doivt = ['Ba Vì', 'Phúc Thọ', 'Đan Phượng', 'Sơn Tây', 'Thạch Thất']
                df_pttb = df_pttb[df_pttb['DOIVT_KV'].isin(allowed_doivt)]
                
                # Tạo thống kê chung
                thong_ke_chung = df_pttb.groupby('DOIVT_KV').size().reset_index(name='Số phiếu tồn')
                
                # Tạo biểu đồ tổng quan
                chart_tong_quan = create_bar_chart(
                    df=thong_ke_chung,
                    x_column='DOIVT_KV',
                    y_column='Số phiếu tồn',
                    title='Thống kê số phiếu tồn theo Đội VT',
                    xlabel='Đội VT',
                    ylabel='Số phiếu tồn',
                    width=0.4
                )
                
                # Tạo biểu đồ cho từng đội
                charts = {}
                for doi_vt in allowed_doivt:
                    df_doi = df_pttb[df_pttb['DOIVT_KV'] == doi_vt].copy()
                    df_doi.loc[:, 'TEN_KV'] = (df_doi['TEN_KV']
                                              .str.split('-').str[1]
                                              .str.replace(r'\([^)]*\)', '', regex=True)
                                              .str.strip())
                    
                    thong_ke_doi = df_doi.groupby('TEN_KV').size().reset_index(name='Số lượng')
                    
                    charts[doi_vt] = create_bar_chart(
                        df=thong_ke_doi,
                        x_column='TEN_KV',
                        y_column='Số lượng',
                        title=f'Thống kê số phiếu tồn theo Khu vực - {doi_vt}',
                        xlabel='Khu vực',
                        ylabel='Số lượng',
                        width=0.4
                    )
                
                # Đánh dấu trạng thái trong session
                session['pttb_file_processed'] = True
                session['has_data'] = True
                
                app.logger.info('Xử lý file thành công')
                return render_template('pttb.html',
                                     show_download=True,
                                     chart_tong_quan=chart_tong_quan,
                                     chart_bavi=charts['Ba Vì'],
                                     chart_phuctho=charts['Phúc Thọ'],
                                     chart_danphuong=charts['Đan Phượng'],
                                     chart_sontay=charts['Sơn Tây'],
                                     chart_thachthat=charts['Thạch Thất'])
            else:
                app.logger.error('Định dạng file không được hỗ trợ')
                return "Định dạng file không được hỗ trợ. Vui lòng tải lên file Excel."
                
        except Exception as e:
            app.logger.error(f'Lỗi xử lý file: {str(e)}')
            session['pttb_file_processed'] = False
            session['has_data'] = False
            return f"Có lỗi xảy ra trong quá trình xử lý: {str(e)}"
            
    # GET request - hiển thị form upload
    return render_template('pttb.html', show_download=False)

@app.route('/download_pttb')
def download_pttb():
    if not session.get('pttb_file_processed', False):
        return "Vui lòng xử lý file trước khi tải xuống"
    
    try:
        # Tạo buffer trong bộ nhớ để lưu file Excel
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Ghi sheet thống kê chung
            thong_ke_chung.to_excel(writer, sheet_name='THONG_KE_CHUNG', index=False)
            
            # Ghi các sheet cho từng đội
            allowed_doivt = ['Ba Vì', 'Phúc Thọ', 'Đan Phượng', 'Sơn Tây', 'Thạch Thất']
            for doi_vt in allowed_doivt:
                df_doi = df_pttb[df_pttb['DOIVT_KV'] == doi_vt].copy()
                df_doi.loc[:, 'TEN_KV'] = (df_doi['TEN_KV']
                                          .str.split('-').str[1]
                                          .str.replace(r'\([^)]*\)', '', regex=True)
                                          .str.strip())
                thong_ke_kv = df_doi.groupby('TEN_KV').size().reset_index(name='Số lượng')
                sheet_name = f'pttb_{doi_vt}'
                thong_ke_kv.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Đưa con trỏ về đầu buffer
        output.seek(0)
        
        # Trả về file Excel để người dùng tải xuống
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='KET_QUA_PTTB.xlsx'
        )
        
    except Exception as e:
        app.logger.error(f'Lỗi khi tạo file Excel: {str(e)}')
        return f"Có lỗi xảy ra: {str(e)}"

##########################################################################################################################

if __name__ == '__main__':
    app.run(debug=True)