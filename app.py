import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# डेटाबेस कनेक्शन और टेबल सेटअप
def init_db():
    conn = sqlite3.connect('revenue_app.db')
    c = conn.cursor()
    
    # 1. आवेदन और प्रतिवेदन टेबल
    c.execute('''CREATE TABLE IF NOT EXISTS applications_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    type_side TEXT, 
                    app_type TEXT, 
                    name TEXT, 
                    village TEXT, 
                    case_no TEXT, 
                    mad TEXT, 
                    year TEXT, 
                    order_date TEXT, 
                    sender_name TEXT,
                    send_mode TEXT,
                    file_name TEXT, 
                    details TEXT, 
                    status TEXT, 
                    date TEXT)''')
    
    # 2. अमल आदेश टेबल
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    order_type TEXT, 
                    order_no TEXT, 
                    khasra TEXT, 
                    status TEXT, 
                    date TEXT)''')
    
    # 3. सीएम हेल्पलाइन टेबल
    c.execute('''CREATE TABLE IF NOT EXISTS cm_helpline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    comp_no TEXT, 
                    name TEXT, 
                    phone TEXT, 
                    comp_type TEXT, 
                    level TEXT, 
                    due_date TEXT, 
                    status TEXT)''')
    
    # 4. कॉमन दस्तावेज़ / रिकॉर्ड्स फोल्डर टेबल
    c.execute('''CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    doc_title TEXT, 
                    village TEXT, 
                    file_name TEXT, 
                    notes TEXT, 
                    date TEXT)''')
    
    # 5. निजी नोट्स टेबल
    c.execute('''CREATE TABLE IF NOT EXISTS personal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    title TEXT, 
                    notes TEXT, 
                    date TEXT)''')
    
    try:
        c.execute("ALTER TABLE applications_reports ADD COLUMN sender_name TEXT")
        c.execute("ALTER TABLE applications_reports ADD COLUMN send_mode TEXT")
        c.execute("ALTER TABLE applications_reports ADD COLUMN status TEXT")
        c.execute("ALTER TABLE applications_reports ADD COLUMN case_no TEXT")
        c.execute("ALTER TABLE applications_reports ADD COLUMN mad TEXT")
        c.execute("ALTER TABLE applications_reports ADD COLUMN year TEXT")
        c.execute("ALTER TABLE applications_reports ADD COLUMN order_date TEXT")
        c.execute("ALTER TABLE applications_reports ADD COLUMN file_name TEXT")
    except:
        pass

    conn.commit()
    conn.close()

init_db()

# ऐप का लेआउट सेटअप (Clean White Theme & Custom CSS)
st.set_page_config(page_title="Mahesh Personal Assistant", page_icon="📁", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        background-color: #ffffff;
    }
    h1 {
        color: #4B0082;
        font-family: sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# नया नाम और हेडर शीर्षक
st.title("📂 Mahesh Personal Assistant")
st.markdown("---")

conn = sqlite3.connect('revenue_app.db')

# ऊपर टॉप टैब्स (Tabs) लेआउट
main_tab1, main_tab2, main_tab3, main_tab4, main_tab5 = st.tabs([
    "📋 आवेदन एवं प्रतिवेदन", 
    "⚙️ अमल आदेश", 
    "📞 सीएम हेल्पलाइन", 
    "📁 दस्तावेज़ फोल्डर", 
    "🔒 निजी डायरी"
])

# 1. आवेदन और प्रतिवेदन ब्लॉक
with main_tab1:
    st.header("तहसील आवेदन और प्रतिवेदन प्रबंधन")
    
    try:
        total_rec = pd.read_sql("SELECT COUNT(*) as cnt FROM applications_reports WHERE type_side='Received'", conn)['cnt'][0]
        total_sub = pd.read_sql("SELECT COUNT(*) as cnt FROM applications_reports WHERE type_side='Submitted'", conn)['cnt'][0]
        pending_cnt = total_rec - total_sub
    except:
        total_rec, total_sub, pending_cnt = 0, 0, 0

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("📥 कुल प्राप्त आवेदन/जानकारी", total_rec)
    col_m2.metric("📤 कुल जमा प्रतिवेदन", total_sub)
    col_m3.metric("⏳ लंबित (Pending) प्रतिवेदन", pending_cnt, delta_color="inverse")
    
    st.markdown("---")
    
    sub_tab1, sub_tab2 = st.tabs(["📥 तहसील से प्राप्त आवेदन / जानकारी", "📤 तहसील में प्रतिवेदन जमा करें"])
    
    with sub_tab1:
        st.subheader("नया आवेदन या जानकारी दर्ज करें")
        with st.form("app_form"):
            app_type = st.selectbox("आवेदन / जानकारी का प्रकार", ["नामांतरण", "बँटवारा", "सीमांकन", "डायवर्जन", "फौत नामांतरण", "व्हाट्सएप द्वारा मांगी गई जानकारी", "अन्य"])
            name = st.text_input("आवेदक का नाम / पक्षकार")
            village = st.text_input("ग्राम / हल्का")
            
            st.markdown("##### भेजने वाले का विवरण")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                sender_name = st.text_input("किसके द्वारा भेजा गया (नाम/पद)")
            with col_s2:
                send_mode = st.selectbox("भेजने का माध्यम", ["व्हाट्सएप (WhatsApp)", "डाक द्वारा (By Post)", "व्यक्तिगत (Personally)", "अन्य"])
            with col_s3:
                rec_date = st.date_input("प्राप्ति दिनांक")
            
            if app_type == "व्हाट्सएप द्वारा मांगी गई जानकारी":
                st.info("💡 व्हाट्सएप जानकारी के लिए प्रकरण क्रमांक अनिवार्य नहीं है।")
                case_no, mad, year = "WhatsApp", "WhatsApp", "-"
            else:
                st.markdown("##### प्रकरण क्रमांक विवरण")
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    case_no = st.text_input("4-डिजिट नंबर (जैसे 0005)", max_chars=4, value="")
                with col_c2:
                    mad = st.selectbox("मद चयन करें", ["A-1 | अ-1", "A-2 | अ-2", "A-3 | अ-3", "A-6 | अ-6", "A-27 | अ-27", "बी-121 | B-121", "अन्य"])
                with col_c3:
                    year_list = [str(y) for y in range(2050, 1949, -1)]
                    default_idx = year_list.index("2026") if "2026" in year_list else 0
                    year = st.selectbox("वर्ष चुनें", year_list, index=default_idx)
            
            uploaded_file = st.file_uploader("आदेश प्रतिलिपि / स्क्रीनशॉट अपलोड करें (PDF/Image)", type=["pdf", "jpg", "jpeg", "png"])
            details = st.text_area("अन्य विवरण / संदेश का सार")
            submitted = st.form_submit_button("सुरक्षित करें")
            
            if submitted and name:
                file_name_str = uploaded_file.name if uploaded_file else "कोई फाइल नहीं"
                full_case_str = f"{case_no} / {mad} / {year}" if app_type != "व्हाट्सएप द्वारा मांगी गई जानकारी" else "व्हाट्सएप जानकारी"
                
                c = conn.cursor()
                c.execute("""INSERT INTO applications_reports 
                            (type_side, app_type, name, village, case_no, mad, year, order_date, sender_name, send_mode, file_name, details, status, date) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                          ("Received", app_type, name, village, full_case_str, mad, year, str(rec_date), sender_name, send_mode, file_name_str, details, "Pending", str(datetime.now().date())))
                conn.commit()
                st.success("सफलतापूर्वक दर्ज कर लिया गया है!")
                st.rerun()
        
        st.subheader("प्राप्त आवेदनों एवं सूचियों की स्थिति")
        df_app = pd.read_sql("SELECT id, app_type as 'प्रकार', name as 'नाम', village as 'ग्राम', case_no as 'प्रकरण क्रमांक', sender_name as 'प्रेषक', send_mode as 'माध्यम', order_date as 'प्राप्ति दिनांक', file_name as 'अटैच फाइल', status as 'स्थिति' FROM applications_reports WHERE type_side='Received' ORDER BY id DESC", conn)
        st.dataframe(df_app, use_container_width=True)

    with sub_tab2:
        st.subheader("प्राप्त आवेदन के विरुद्ध प्रतिवेदन जमा करें")
        pending_df = pd.read_sql("SELECT id, name, case_no, village, app_type FROM applications_reports WHERE type_side='Received' AND (status='Pending' OR status IS NULL)", conn)
        
        if pending_df.empty:
            st.info("📌 वर्तमान में कोई भी आवेदन लंबित (Pending) नहीं है। सभी के प्रतिवेदन जमा हो चुके हैं!")
        else:
            options_dict = {}
            for index, row in pending_df.iterrows():
                label = f"ID: {row['id']} | {row['app_type']} - {row['name']} (ग्राम: {row['village']}) [{row['case_no']}]"
                options_dict[label] = row['id']
            
            with st.form("report_form"):
                selected_label = st.selectbox("लंबित आवेदन चुनें (जिसका प्रतिवेदन देना है)", list(options_dict.keys()))
                rep_type = st.selectbox("प्रतिवेदन का प्रकार", ["सीमांकन प्रतिवेदन", "जाँच प्रतिवेदन (नामांतरण/बँटवारा)", "व्हाट्सएप जानकारी प्रेषित प्रतिवेदन", "अन्य"])
                
                st.markdown("##### जमा करने का विवरण")
                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    submit_mode = st.selectbox("जमा करने का माध्यम", ["तहसील में व्यक्तिगत रूप से", "व्हाट्सएप द्वारा प्रेषित", "डाक द्वारा प्रेषित", "अन्य"])
                with col_sub2:
                    submit_date = st.date_input("जमा करने की दिनांक")

                rep_file = st.file_uploader("जाँच प्रतिवेदन / रिपोर्ट कॉपी अपलोड करें", type=["pdf", "jpg", "jpeg", "png"])
                details = st.text_area("प्रतिवेदन का निष्कर्ष / टिप्पणी विवरण")
                
                submitted_rep = st.form_submit_button("प्रतिवेदन दर्ज करें")
                
                if submitted_rep:
                    chosen_id = options_dict[selected_label]
                    selected_row = pending_df[pending_df['id'] == chosen_id].iloc[0]
                    
                    file_str = rep_file.name if rep_file else "रिपोर्ट फाइल नहीं"
                    c = conn.cursor()
                    c.execute("""INSERT INTO applications_reports 
                                (type_side, app_type, name, village, case_no, mad, year, order_date, sender_name, send_mode, file_name, details, status, date) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                              ("Submitted", rep_type, selected_row['name'], selected_row['village'], selected_row['case_no'], "-", "-", str(submit_date), "स्वयं (Patwari)", submit_mode, file_str, details, "Completed", str(datetime.now().date())))
                    
                    c.execute("UPDATE applications_reports SET status='Completed' WHERE id=?", (chosen_id,))
                    conn.commit()
                    st.success("प्रतिवेदन सफलतापूर्वक जमा और लिंक कर दिया गया है!")
                    st.rerun()
        
        st.subheader("तहसील में जमा किए गए सभी प्रतिवेदनों की सूची")
        df_rep = pd.read_sql("SELECT id, app_type as 'प्रतिवेदन प्रकार', name as 'पक्षकार/नाम', village as 'ग्राम', send_mode as 'जमा माध्यम', order_date as 'जमा दिनांक', details as 'निष्कर्ष' FROM applications_reports WHERE type_side='Submitted' ORDER BY id DESC", conn)
        st.dataframe(df_rep, use_container_width=True)

# 2. अमल आदेश ब्लॉक
with main_tab2:
    st.header("अमल आदेश प्रविष्टि (Order Implementation)")
    with st.form("order_form"):
        col1, col2 = st.columns(2)
        with col1:
            order_type = st.selectbox("आदेश का प्रकार", ["नामांतरण", "बँटवारा", "डायवर्जन", "शुद्धि पत्र", "अन्य"])
            order_no = st.text_input("आदेश क्रमांक / दिनांक")
        with col2:
            khasra = st.text_input("खसरा नंबर एवं ग्राम")
            status = st.selectbox("अमल स्थिति", ["शेष (Pending)", "पूर्ण (Completed)"])
        submitted = st.form_submit_button("अमल आदेश सुरक्षित करें")
        if submitted and order_no:
            c = conn.cursor()
            c.execute("INSERT INTO orders (order_type, order_no, khasra, status, date) VALUES (?, ?, ?, ?, ?)", 
                      (order_type, order_no, khasra, status, str(datetime.now().date())))
            conn.commit()
            st.success("अमल आदेश दर्ज कर लिया गया!")
    
    st.subheader("अमल आदेश सूची")
    df_orders = pd.read_sql("SELECT * FROM orders ORDER BY id DESC", conn)
    st.dataframe(df_orders, use_container_width=True)

# 3. सीएम हेल्पलाइन ब्लॉक
with main_tab3:
    st.header("सीएम हेल्पलाइन मॉनिटरिंग (CM Helpline)")
    with st.form("cm_form"):
        col1, col2 = st.columns(2)
        with col1:
            comp_no = st.text_input("शिकायत क्रमांक (Complaint ID)")
            name = st.text_input("शिकायतकर्ता का नाम")
            phone = st.text_input("शिकायतकर्ता का मोबाइल नंबर")
        with col2:
            comp_type = st.selectbox("शिकायत का प्रकार", ["राजस्व विभाग", "सीमांकन संबंधी", "नामांतरण", "अन्य"])
            level = st.selectbox("शिकायत स्तर", ["L1", "L2", "L3"])
            due_date = st.text_input("अंतिम तिथि (Due Date - YYYY-MM-DD)")
        status = st.selectbox("शिकायत की स्थिति", ["लंबित (Pending)", "निराकृत (Resolved)"])
        submitted = st.form_submit_button("शिकायत दर्ज करें")
        if submitted and comp_no:
            c = conn.cursor()
            c.execute("INSERT INTO cm_helpline (comp_no, name, phone, comp_type, level, due_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                      (comp_no, name, phone, comp_type, level, due_date, status))
            conn.commit()
            st.success("सीएम हेल्पलाइन शिकायत सफलतापूर्वक जोड़ दी गई!")
    
    st.subheader("सीएम हेल्पलाइन शिकायत सूची")
    df_cm = pd.read_sql("SELECT * FROM cm_helpline ORDER BY id DESC", conn)
    st.dataframe(df_cm, use_container_width=True)

# 4. कॉमन दस्तावेज़ फोल्डर ब्लॉक
with main_tab4:
    st.header("कॉमन दस्तावेज़ फोल्डर (खसरा, नक्शा, B-1 व अन्य फाइलें)")
    with st.form("doc_folder_form"):
        doc_title = st.text_input("दस्तावेज़ का शीर्षक / नाम (जैसे: खसरा नं 12 का नक्शा)")
        village = st.text_input("ग्राम का नाम")
        doc_file = st.file_uploader("फाइल अपलोड करें (PDF / Image)", type=["pdf", "jpg", "jpeg", "png"])
        notes = st.text_area("अतिरिक्त टिप्पणी / विवरण")
        
        submitted_doc = st.form_submit_button("दस्तावेज़ सुरक्षित करें")
        
        if submitted_doc and doc_title:
            file_str = doc_file.name if doc_file else "फाइल संलग्न नहीं"
            c = conn.cursor()
            c.execute("""INSERT INTO records (doc_title, village, file_name, notes, date) 
                        VALUES (?, ?, ?, ?, ?)""", 
                      (doc_title, village, file_str, notes, str(datetime.now().date())))
            conn.commit()
            st.success("दस्तावेज़ सफलतापूर्वक सुरक्षित कर लिया गया है!")
    
    st.subheader("आपके सभी सुरक्षित दस्तावेज़ों की सूची")
    df_docs = pd.read_sql("SELECT id, doc_title as 'दस्तावेज़ शीर्षक', village as 'ग्राम', file_name as 'फाइल', notes as 'टिप्पणी', date as 'दिनांक' FROM records ORDER BY id DESC", conn)
    st.dataframe(df_docs, use_container_width=True)

# 5. निजी डायरी ब्लॉक
with main_tab5:
    st.header("निजी नोट्स और डायरी (Personal)")
    with st.form("personal_form"):
        title = st.text_input("शीर्षक (Title)")
        notes = st.text_area("महत्वपूर्ण नोट्स / विवरण")
        submitted = st.form_submit_button("नोट्स सुरक्षित करें")
        if submitted and title:
            c = conn.cursor()
            c.execute("INSERT INTO personal (title, notes, date) VALUES (?, ?, ?)", (title, notes, str(datetime.now().date())))
            conn.commit()
            st.success("निजी नोट्स सहेजे गए!")
    
    st.subheader("आपके निजी नोट्स")
    df_per = pd.read_sql("SELECT * FROM personal ORDER BY id DESC", conn)
    st.dataframe(df_per, use_container_width=True)

conn.close()