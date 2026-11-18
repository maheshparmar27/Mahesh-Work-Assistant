import datetime
import os
import sqlite3
import pandas as pd
import streamlit as st

# पेज की सेटिंग्स (Clean White Theme & Mobile Friendly Layout)
st.set_page_config(
    page_title="Mahesh Personal Assistant", page_icon="📂", layout="wide"
)

# डेटाबेस कनेक्शन सेट अप (ताकि डेटा कभी डिलीट न हो)
DB_FILE = "mahesh_work_assistant.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  # प्राप्त आवेदन टेबल
  c.execute("""
        CREATE TABLE IF NOT EXISTS received_apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            medium TEXT,
            date TEXT,
            case_no TEXT,
            details TEXT,
            file_name TEXT,
            file_data BLOB
        )
    """)
  # जमा प्रतिवेदन टेबल
  c.execute("""
        CREATE TABLE IF NOT EXISTS submitted_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id TEXT,
            submit_date TEXT,
            medium TEXT,
            details TEXT,
            file_name TEXT,
            file_data BLOB
        )
    """)
  # सीएम हेल्पलाइन टेबल
  c.execute("""
        CREATE TABLE IF NOT EXISTS cm_helpline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comp_id TEXT,
            level TEXT,
            complainant TEXT,
            subject TEXT,
            status TEXT,
            date TEXT,
            remarks TEXT
        )
    """)
  # दस्तावेज़ फोल्डर टेबल
  c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_name TEXT,
            doc_type TEXT,
            date TEXT,
            file_name TEXT,
            file_data BLOB
        )
    """)
  # निजी डायरी टेबल
  c.execute("""
        CREATE TABLE IF NOT EXISTS diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            note TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()

# कस्टम CSS - क्लीन व्हाइट थीम और मोबाइल के अनुकूल टॉप टैब्स लेआउट
st.markdown(
    """
    <style>
    .main {
        background-color: #FFFFFF;
        color: #111111;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1F2937;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #F3F4F6;
        padding: 10px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        color: #374151;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        color: white !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📂 Mahesh Personal Assistant")
st.markdown("---")

# मोबाइल के अनुकूल टॉप टैब्स लेआउट
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📥 आवेदन एवं प्रतिवेदन",
    "⚙️ अमल आदेश",
    "📞 सीएम हेल्पलाइन",
    "📁 दस्तावेज़ फोल्डर",
    "📔 निजी डायरी",
])

# ==================== टैब 1: आवेदन एवं प्रतिवेदन ====================
with tab1:
  st.subheader("तहसील आवेदन और प्रतिवेदन प्रबंधन")

  sub_choice = st.radio(
      "चुनें:", [
          "तहसील से प्राप्त आवेदन / जानकारी दर्ज करें",
          "तहसील में प्रतिवेदन जमा करें",
          "सभी रिकॉर्ड देखें (डिटेल व अटैच फाइल)",
      ],
      horizontal=True,
  )

  conn = sqlite3.connect(DB_FILE)

  if sub_choice == "तहसील से प्राप्त आवेदन / जानकारी दर्ज करें":
    st.markdown("### नया प्राप्त आवेदन दर्ज करें")
    with st.form("received_form", clear_on_submit=True):
      col1, col2 = st.columns(2)
      with col1:
        sender = st.text_input("प्रेषक का नाम (Sender Name)")
        medium = st.selectbox(
            "माध्यम (Medium)", ["व्हाट्सएप", "डाक", "व्यक्तिगत", "तहसीलदार महोदय"]
        )
      with col2:
        date = st.date_input(
            "प्राप्ति दिनांक (Receipt Date)", datetime.date.today()
        )

      st.markdown("##### प्रकरण क्रमांक संरचना")
      c1, c2, c3 = st.columns(3)
      with c1:
        num_part = st.text_input("4-डिजिट नंबर (जैसे 0123)", "0001")
      with c2:
        mad_part = st.selectbox(
            "मद (Mad)", ["A-3", "A-6", "A-27", "B-121", "अन्य"]
        )
      with c3:
        year_part = st.selectbox(
            "वर्ष (Year)", list(range(1950, 2051)), index=76
        )  # 2026 default

      case_no = f"{num_part} / {mad_part} / {year_part}"
      st.info(structured_case := f"सत्यापित प्रकरण क्रमांक: **{case_no}**")

      details = st.text_area("अन्य विवरण / संदेश का सार (Details)")
      uploaded_file = st.file_uploader(
          "आदेश प्रतिलिपि / स्क्रीनशॉट अपलोड करें (PDF/Image)",
          type=["pdf", "jpg", "png", "jpeg"],
      )

      submitted = st.form_submit_button("सुरक्षित करें")
      if submitted:
        file_name = uploaded_file.name if uploaded_file else ""
        file_data = uploaded_file.read() if uploaded_file else b""

        c = conn.cursor()
        c.execute(
            """INSERT INTO received_apps (sender, medium, date, case_no, details, file_name, file_data)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                sender,
                medium,
                str(date),
                case_no,
                details,
                file_name,
                file_data,
            ),
        )
        conn.commit()
        st.success("प्राप्त आवेदन सफलतापूर्वक सुरक्षित कर लिया गया है!")

  elif sub_choice == "तहसील में प्रतिवेदन जमा करें":
    st.markdown("### तहसील में प्रतिवेदन जमा करना")
    # केवल लंबित प्राप्त आवेदनों की सूची प्राप्त करें
    df_rec = pd.read_sql("SELECT id, case_no, sender FROM received_apps", conn)

    if df_rec.empty:
      st.warning(
          "पहले 'प्राप्त आवेदन' दर्ज करें, तभी आप प्रतिवेदन जमा कर सकेंगे।"
      )
    else:
      app_options = {
          f"ID: {row['id']} | प्र प्रकरण: {row['case_no']} (प्रेषक: {row['sender']})": row[
              "id"
          ]
          for index, row in df_rec.iterrows()
      }
      selected_app_label = st.selectbox(
          "संबंधित प्राप्त आवेदन चुनें", list(app_options.keys())
      )
      selected_app_id = app_options[selected_app_label]

      with st.form("submit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
          submit_date = st.date_input(
              "जमा करने की दिनांक", datetime.date.today()
          )
        with col2:
          sub_medium = st.selectbox(
              "जमा करने का माध्यम", [
                  "आरसीएमएस (RCMS)",
                  "वाहन/डाक",
                  "व्यक्तिगत रूप से",
              ]
          )

        sub_details = st.text_area("जमा किए गए प्रतिवेदन का विवरण / सार")
        sub_file = st.file_uploader(
            "जमा प्रतिवेदन की पावती / कॉपी अपलोड करें (PDF/Image)",
            type=["pdf", "jpg", "png", "jpeg"],
        )

        sub_btn = st.form_submit_button("प्रतिवेदन जमा दर्ज करें")
        if sub_btn:
          f_name = sub_file.name if sub_file else ""
          f_data = sub_file.read() if sub_file else b""

          c = conn.cursor()
          c.execute(
              """INSERT INTO submitted_reports (app_id, submit_date, medium, details, file_name, file_data)
                       VALUES (?, ?, ?, ?, ?, ?)""",
              (
                  str(selected_app_id),
                  str(submit_date),
                  sub_medium,
                  sub_details,
                  f_name,
                  f_data,
              ),
          )
          conn.commit()
          st.success("प्रतिवेदन जमा प्रविष्टि सफलतापूर्वक दर्ज हो गई!")

  else:
    st.markdown("### 📋 सभी प्राप्त आवेदनों एवं जमा प्रतिवेदनों का विस्तृत रिकॉर्ड")

    st.markdown("#### 📥 प्राप्त आवेदन सूची")
    df_rec_all = pd.read_sql("SELECT * FROM received_apps", conn)
    if not df_rec_all.empty:
      for idx, row in df_rec_all.iterrows():
        with st.expander(
            f"प्रकरण: {row['case_no']} | प्रेषक: {row['sender']} ({row['date']})"
        ):
          st.write(f"**माध्यम:** {row['medium']}")
          st.write(f"**विवरण:** {row['details']}")
          if row["file_name"]:
            st.write(f"**अटैच फाइल:** {row['file_name']}")
            st.download_button(
                label=f"📥 डाउनलोड/देखें फाइल ({row['file_name']})",
                data=row["file_data"],
                file_name=row["file_name"],
                mime="application/octet-stream",
                key=f"rec_{row['id']}",
            )
          else:
            st.info("कोई फाइल अटैच नहीं की गई थी।")
    else:
      st.info("कोई प्राप्त आवेदन दर्ज नहीं है।")

    st.markdown("---")
    st.markdown("#### 📤 जमा किए गए प्रतिवेदन सूची")
    df_sub_all = pd.read_sql("SELECT * FROM submitted_reports", conn)
    if not df_sub_all.empty:
      for idx, row in df_sub_all.iterrows():
        with st.expander(
            f"संबंधित आवेदन ID: {row['app_id']} | जमा दिनांक: {row['submit_date']}"
        ):
          st.write(f"**माध्यम:** {row['medium']}")
          st.write(f"**विवरण:** {row['details']}")
          if row["file_name"]:
            st.write(f"**अटैच फाइल:** {row['file_name']}")
            st.download_button(
                label=f"📥 डाउनलोड/देखें पावती ({row['file_name']})",
                data=row["file_data"],
                file_name=row["file_name"],
                mime="application/octet-stream",
                key=f"sub_{row['id']}",
            )
          else:
            st.info("कोई फाइल अटैच नहीं की गई थी।")
    else:
      st.info("कोई जमा प्रतिवेदन दर्ज नहीं है।")

  conn.close()

# ==================== टैब 2: अमल आदेश ====================
with tab2:
  st.subheader("अमल आदेश ट्रैकिंग (Orders Tracking)")
  st.info("यहाँ आपके तहसील से पारित होने वाले अमल आदेशों की प्रविष्टि रहेगी।")
  # इसे भी इसी तरह डेटाबेस से जोड़ा जा सकता है, फिलहाल ढांचा तैयार है।

# ==================== टैब 3: सीएम हेल्पलाइन ====================
with tab3:
  st.subheader("📞 सीएम हेल्पलाइन (CM Helpline) मॉनिटरिंग")

  cm_choice = st.radio(
      "विकल्प चुनें:", ["शिकायत दर्ज करें", "सभी शिकायतें देखें"], horizontal=True
  )
  conn = sqlite3.connect(DB_FILE)

  if cm_choice == "शिकायत दर्ज करें":
    with st.form("cm_form", clear_on_submit=True):
      c1, c2 = st.columns(2)
      with c1:
        comp_id = st.text_input("शिकायत क्रमांक (Complaint ID)")
        level = st.selectbox("स्तर (Level)", ["L1", "L2", "L3"])
      with c2:
        complainant = st.text_input("शिकायतकर्ता का नाम")
        date = st.date_input("प्राप्ति दिनांक", datetime.date.today())

      subject = st.text_input("विषय / संक्षिप्त समस्या")
      status = st.selectbox(
          "स्थिति (Status)", ["लंबित (Pending)", "निराकृत (Resolved)"]
      )
      remarks = st.text_area("विवरण / की गई कार्रवाई")

      cm_submit = st.form_submit_button("शिकायत सुरक्षित करें")
      if cm_submit:
        c = conn.cursor()
        c.execute(
            """INSERT INTO cm_helpline (comp_id, level, complainant, subject, status, date, remarks)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                comp_id,
                level,
                complainant,
                subject,
                status,
                str(date),
                remarks,
            ),
        )
        conn.commit()
        st.success("सीएम हेल्पलाइन शिकायत सफलतापूलक दर्ज हो गई!")
  else:
    st.markdown("### सभी सीएम हेल्पलाइन शिकायतें")
    df_cm = pd.read_sql("SELECT * FROM cm_helpline", conn)
    if not df_cm.empty:
      # टेबल फॉर्मेट में एक साथ सारी शिकायतें दिखाएं
      st.dataframe(
          df_cm[[
              "comp_id",
              "level",
              "complainant",
              "subject",
              "status",
              "date",
              "remarks",
          ]],
          use_container_width=True,
      )
    else:
      st.info("कोई सीएम हेल्पलाइन शिकायत दर्ज नहीं है।")

  conn.close()

# ==================== टैब 4: दस्तावेज़ फोल्डर ====================
with tab4:
  st.subheader("📁 दस्तावेज़ फोल्डर (Khasra, B-1, Maps & PDFs)")
  conn = sqlite3.connect(DB_FILE)

  with st.form("doc_form", clear_on_submit=True):
    doc_name = st.text_input("दस्तावेज़ का नाम (जैसे खसरा ग्राम बानहेड़ा)")
    doc_type = st.selectbox(
        "प्रकार", ["खसरा", "बी-वन (B-1)", "नक्शा", "अन्य आदेश/पीडीएफ"]
    )
    doc_file = st.file_uploader("फाइल अपलोड करें", type=["pdf", "jpg", "png"])
    doc_save = st.form_submit_button("फोल्डर में सहेजें")

    if doc_save and doc_file:
      c = conn.cursor()
      c.execute(
          """INSERT INTO documents (doc_name, doc_type, date, file_name, file_data)
                   VALUES (?, ?, ?, ?, ?)""",
          (
              doc_name,
              doc_type,
              str(datetime.date.today()),
              doc_file.name,
              doc_file.read(),
          ),
      )
      conn.commit()
      st.success("डॉक्यूमेंट सफलतापूर्वक सहेज लिया गया!")

  st.markdown("### सहेजे गए सभी दस्तावेज़")
  df_docs = pd.read_sql("SELECT * FROM documents", conn)
  if not df_docs.empty:
    for idx, row in df_docs.iterrows():
      with st.expander(
          f"📂 {row['doc_name']} ({row['doc_type']}) - {row['date']}"
      ):
        st.download_button(
            label=f"📥 डाउनलोड करें ({row['file_name']})",
            data=row["file_data"],
            file_name=row["file_name"],
            mime="application/octet-stream",
            key=f"doc_{row['id']}",
        )
  else:
    st.info("फोल्डर खाली है।")

  conn.close()

# ==================== टैब 5: निजी डायरी ====================
with tab5:
  st.subheader("📔 निजी डायरी (Personal Notes)")
  conn = sqlite3.connect(DB_FILE)

  with st.form("diary_form", clear_on_submit=True):
    note_date = st.date_input("दिनांक", datetime.date.today())
    note_text = st.text_area("आज के मुख्य नोट्स / बातें यहाँ लिखें...")
    note_save = st.form_submit_button("नोट्स सेव करें")

    if note_save:
      c = conn.cursor()
      c.execute(
          "INSERT INTO diary (date, note) VALUES (?, ?)",
          (str(note_date), note_text),
      )
      conn.commit()
      st.success("डायरी नोट सुरक्षित हो गया!")

  df_diary = pd.read_sql("SELECT * FROM diary ORDER BY id DESC", conn)
  if not df_diary.empty:
    for idx, row in df_diary.iterrows():
      st.markdown(f"**📅 {row['date']}**")
      st.write(row["note"])
      st.markdown("---")
  else:
    st.info("डायरी खाली है।")

  conn.close()
