import datetime
import os
import sqlite3
import pandas as pd
import pdfplumber
import streamlit as st

# पेज की सेटिंग्स
st.set_page_config(
    page_title="Mahesh Personal Assistant", page_icon="📂", layout="wide"
)

DB_FILE = "mahesh_work_assistant.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()

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

  c.execute("""
        CREATE TABLE IF NOT EXISTS cm_helpline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comp_id TEXT UNIQUE,
            level TEXT,
            complainant TEXT,
            mobile TEXT,
            subject TEXT,
            status TEXT,
            date TEXT,
            reply TEXT,
            remarks TEXT
        )
    """)
  try:
    c.execute("ALTER TABLE cm_helpline ADD COLUMN mobile TEXT")
  except:
    pass
  try:
    c.execute("ALTER TABLE cm_helpline ADD COLUMN reply TEXT")
  except:
    pass

  # डुप्लीकेट शिकायतों को हटाने के लिए
  try:
    c.execute("""
            DELETE FROM cm_helpline 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM cm_helpline 
                GROUP BY comp_id
            )
        """)
  except:
    pass

  c.execute("""
        CREATE TABLE IF NOT EXISTS execution_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT UNIQUE,
            receipt_date TEXT,
            details TEXT,
            status TEXT,
            orig_file_name TEXT,
            orig_file_data BLOB,
            khasra_file_name TEXT,
            khasra_file_data BLOB,
            b1_file_name TEXT,
            b1_file_data BLOB
        )
    """)

  c.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            father_name TEXT,
            mobile TEXT,
            aadhaar TEXT,
            survey_no TEXT
        )
    """)

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

st.markdown(
    """
    <style>
    .main { background-color: #FFFFFF; color: #111111; }
    h1, h2, h3, h4, h5, h6 { color: #1F2937; }
    .stTabs [data-baseweb="tab-list"] { gap: 5px; background-color: #F3F4F6; padding: 8px; border-radius: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #FFFFFF; border-radius: 6px; padding: 6px 12px; font-weight: bold; color: #374151; font-size: 14px; }
    .stTabs [aria-selected="true"] { background-color: #2563EB !important; color: white !important; }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📂 Mahesh Personal Assistant")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📥 आवेदन व प्रतिवेदन",
    "⚙️ अमल आदेश",
    "📞 सीएम हेल्पलाइन",
    "👨‍🌾 किसान डायरेक्टरी",
    "📁 दस्तावेज़ फोल्डर",
    "📔 निजी डायरी",
])

# ==================== टैब 1: आवेदन एवं प्रतिवेदन ====================
with tab1:
  st.subheader("तहसील आवेदन और प्रतिवेदन प्रबंधन")
  conn = sqlite3.connect(DB_FILE)

  df_rec_count = pd.read_sql("SELECT COUNT(*) as cnt FROM received_apps", conn)
  df_sub_count = pd.read_sql(
      "SELECT COUNT(*) as cnt FROM submitted_reports", conn
  )
  total_rec = df_rec_count["cnt"].iloc[0]
  total_sub = df_sub_count["cnt"].iloc[0]
  pending_rep = total_rec - total_sub

  col_c1, col_c2, col_c3 = st.columns(3)
  col_c1.metric("📥 कुल प्राप्त आवेदन", total_rec)
  col_c2.metric("📤 जमा प्रतिवेदन", total_sub)
  col_c3.metric("⏳ प्रतिवेदन बाकी", max(0, pending_rep))
  st.markdown("---")

  sub_choice = st.radio(
      "चुनें:", [
          "तहसील से प्राप्त आवेदन दर्ज करें",
          "तहसील में प्रतिवेदन जमा करें",
          "सभी रिकॉर्ड देखें व डिलीट करें",
      ],
      horizontal=True,
      key="app_radio",
  )

  if sub_choice == "तहसील से प्राप्त आवेदन दर्ज करें":
    st.markdown("### नया प्राप्त आवेदन दर्ज करें")
    with st.form("received_form", clear_on_submit=True):
      col1, col2 = st.columns(2)
      with col1:
        sender = st.text_input("प्रेषक का नाम (Sender Name) *")
        medium = st.selectbox(
            "माध्यम (Medium)", [
                "व्हाट्सएप",
                "डाक",
                "व्यक्तिगत",
                "तहसीलदार महोदय",
                "SAARA App",
                "SAARA Portal 2.0",
            ]
        )
      with col2:
        date = st.date_input(
            "प्राप्ति दिनांक (Receipt Date)", datetime.date.today()
        )

      st.markdown("##### प्रकरण क्रमांक संरचना")
      c1, c2, c3 = st.columns(3)
      with c1:
        num_part = st.text_input(
            "4-डिजिट नंबर (जैसे 0123)",
            "",
            placeholder="नंबर दर्ज करें",
        )
      with c2:
        mad_part = st.selectbox(
            "मद (Mad)", ["A-3", "A-6", "A-27", "B-121", "अन्य"]
        )
      with c3:
        year_part = st.selectbox(
            "वर्ष (Year)", list(range(1950, 2051)), index=76
        )

      case_no = ""
      if num_part.strip():
        case_no = f"{num_part.strip()} / {mad_part} / {year_part}"
        st.info(f"सत्यापित प्रकरण क्रमांक: **{case_no}**")

      details = st.text_area("अन्य विवरण / संदेश का सार (Details)")
      uploaded_file = st.file_uploader(
          "आदेश प्रतिलिपि / स्क्रीनशॉट अपलोड करें (PDF/Image)",
          type=["pdf", "jpg", "png", "jpeg"],
      )

      submitted = st.form_submit_button("सुरक्षित करें")
      if submitted:
        if not sender.strip() or not num_part.strip():
          st.error("कृपया प्रेषक का नाम और प्रकरण नंबर ठीक से भरें!")
        else:
          cursor = conn.cursor()
          cursor.execute(
              "SELECT id FROM received_apps WHERE case_no = ?", (case_no,)
          )
          if cursor.fetchone():
            st.error(f"त्रुटि: प्रकरण क्रमांक '{case_no}' पहले से दर्ज है!")
          else:
            file_name = uploaded_file.name if uploaded_file else ""
            file_data = uploaded_file.read() if uploaded_file else b""
            cursor.execute(
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
            st.rerun()

  elif sub_choice == "तहसील में प्रतिवेदन जमा करें":
    st.markdown("### तहसील में प्रतिवेदन जमा करना")
    df_rec = pd.read_sql("SELECT id, case_no, sender FROM received_apps", conn)
    if df_rec.empty:
      st.warning(
          "पहले 'प्राप्त आवेदन' दर्ज करें, तभी आप प्रतिवेदन जमा कर सकेंगे।"
      )
    else:
      app_options = {
          f"ID: {row['id']} | प्रकरण: {row['case_no']} (प्रेषक: {row['sender']})": row[
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
                  "SAARA App",
              ]
          )

        sub_details = st.text_area("जमा किए गए प्रतिवेदन का विवरण / सार *")
        sub_file = st.file_uploader(
            "जमा प्रतिवेदन की पावती / कॉपी अपलोड करें (PDF/Image)",
            type=["pdf", "jpg", "png", "jpeg"],
        )

        sub_btn = st.form_submit_button("प्रतिवेदन जमा दर्ज करें")
        if sub_btn:
          if not sub_details.strip():
            st.error("कृपया प्रतिवेदन का विवरण अवश्य भरें!")
          else:
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
            st.rerun()

  else:
    st.markdown("### 📋 सभी प्राप्त आवेदनों एवं जमा प्रतिवेदनों का विस्तृत रिकॉर्ड")
    st.markdown("#### 📥 प्राप्त आवेदन सूची")
    df_rec_all = pd.read_sql("SELECT * FROM received_apps", conn)
    if not df_rec_all.empty:
      for idx, row in df_rec_all.iterrows():
        serial_no = idx + 1
        with st.expander(
            f"[{serial_no}] प्रकरण: {row['case_no']} | प्रेषक: {row['sender']}"
            f" ({row['date']})"
        ):
          st.write(f"**माध्यम:** {row['medium']}")
          st.write(f"**विवरण:** {row['details']}")
          if row["file_name"]:
            st.download_button(
                label=f"📥 डाउनलोड फाइल ({row['file_name']})",
                data=row["file_data"],
                file_name=row["file_name"],
                mime="application/octet-stream",
                key=f"rec_dl_{row['id']}",
            )
          if st.button("🗑️ यह आवेदन डिलीट करें", key=f"del_rec_{row['id']}"):
            c = conn.cursor()
            c.execute(
                "DELETE FROM received_apps WHERE id = ?", (row["id"],)
            )
            conn.commit()
            st.success("आवेदन डिलीट कर दिया गया है!")
            st.rerun()
    else:
      st.info("कोई प्राप्त आवेदन दर्ज नहीं है।")

    st.markdown("---")
    st.markdown("#### 📤 जमा किए गए प्रतिवेदन सूची")
    df_sub_all = pd.read_sql("SELECT * FROM submitted_reports", conn)
    if not df_sub_all.empty:
      for idx, row in df_sub_all.iterrows():
        serial_no = idx + 1
        with st.expander(
            f"[{serial_no}] संबंधित आवेदन ID: {row['app_id']} | जमा दिनांक:"
            f" {row['submit_date']}"
        ):
          st.write(f"**माध्यम:** {row['medium']}")
          st.write(f"**विवरण:** {row['details']}")
          if row["file_name"]:
            st.download_button(
                label=f"📥 डाउनलोड पावती ({row['file_name']})",
                data=row["file_name"],
                mime="application/octet-stream",
                key=f"sub_dl_{row['id']}",
            )
          if st.button(
              "🗑️ यह प्रतिवेदन डिलीट करें", key=f"del_sub_{row['id']}"
          ):
            c = conn.cursor()
            c.execute(
                "DELETE FROM submitted_reports WHERE id = ?", (row["id"],)
            )
            conn.commit()
            st.success("प्रतिवेदन डिलीट कर दिया गया है!")
            st.rerun()
    else:
      st.info("कोई जमा प्रतिवेदन दर्ज नहीं है।")

  conn.close()

# ==================== टैब 2: अमल आदेश ====================
with tab2:
  st.subheader("⚙️ अमल आदेश ट्रैकिंग (Orders Execution & Tracking)")
  conn = sqlite3.connect(DB_FILE)
  df_exec_all = pd.read_sql("SELECT * FROM execution_orders", conn)

  total_orders = len(df_exec_all)
  executed_orders = (
      len(df_exec_all[df_exec_all["status"] == "अमल कर दिया गया"])
      if total_orders > 0
      else 0
  )
  pending_orders = total_orders - executed_orders

  col_e1, col_e2, col_e3 = st.columns(3)
  col_e1.metric("📦 कुल प्राप्त आदेश", total_orders)
  col_e2.metric("⏳ अमल बाकी (Pending)", pending_orders)
  col_e3.metric("✅ अमल हो चुका", executed_orders)
  st.markdown("---")

  exec_choice = st.radio(
      "विकल्प चुनें:", [
          "नया अमल आदेश दर्ज करें",
          "लंबित व पूर्ण आदेश सूची (अमल करें/डिलीट)",
      ],
      horizontal=True,
      key="exec_radio",
  )

  if exec_choice == "नया अमल आदेश दर्ज करें":
    st.markdown("### तहसील से प्राप्त अमल आदेश दर्ज करें")
    with st.form("exec_form", clear_on_submit=True):
      c1, c2 = st.columns(2)
      with c1:
        order_no = st.text_input(
            "प्रकरण / आदेश क्रमांक *", "", placeholder="जैसे 12/अ-6/2026"
        )
      with c2:
        receipt_date = st.date_input(
            "प्राप्ति दिनांक", datetime.date.today(), key="exec_dt"
        )

      details = st.text_area("आदेश का विवरण / किसके पक्ष में है *")
      orig_file = st.file_uploader(
          "तहसील से प्राप्त मूल आदेश अपलोड करें (PDF/Image)",
          type=["pdf", "jpg", "png", "jpeg"],
      )

      exec_sub = st.form_submit_button("आदेश सुरक्षित करें")
      if exec_sub:
        if not order_no.strip() or not details.strip():
          st.error("कृपया आदेश क्रमांक और विवरण अवश्य भरें!")
        else:
          cursor = conn.cursor()
          cursor.execute(
              "SELECT id FROM execution_orders WHERE order_no = ?", (order_no,)
          )
          if cursor.fetchone():
            st.error(f"त्रुटि: आदेश क्रमांक '{order_no}' पहले से दर्ज है!")
          else:
            f_name = orig_file.name if orig_file else ""
            f_data = orig_file.read() if orig_file else b""
            cursor.execute(
                """INSERT INTO execution_orders (order_no, receipt_date, details, status, orig_file_name, orig_file_data)
                         VALUES (?, ?, ?, 'लंबित (Pending)', ?, ?)""",
                (
                    order_no.strip(),
                    str(receipt_date),
                    details,
                    f_name,
                    f_data,
                ),
            )
            conn.commit()
            st.success("अमल आदेश सफलतापूर्वक दर्ज हो गया!")
            st.rerun()

  else:
    st.markdown("### सभी अमल आदेश सूची व निष्पादन (Execution)")
    if not df_exec_all.empty:
      for idx, row in df_exec_all.iterrows():
        serial_no = idx + 1
        st.markdown(
            f"**{serial_no}. आदेश क्र.: {row['order_no']}** | दिनांक:"
            f" {row['receipt_date']} | स्थिति: **{row['status']}**"
        )
        with st.expander(f"विवरण व दस्तावेज़ देखें (आदेश क्र. {row['order_no']})"):
          st.write(f"**विवरण:** {row['details']}")
          if row["orig_file_name"]:
            st.download_button(
                label=f"📥 मूल आदेश डाउनलोड ({row['orig_file_name']})",
                data=row["orig_file_data"],
                file_name=row["orig_file_name"],
                mime="application/octet-stream",
                key=f"orig_dl_{row['id']}",
            )
          if row["status"] == "अमल कर दिया गया":
            st.success("✅ इस आदेश पर अमल किया जा चुका है।")
            if row["khasra_file_name"]:
              st.download_button(
                  label=f"📥 अमल पश्चात खसरा ({row['khasra_file_name']})",
                  data=row["khasra_file_data"],
                  file_name=row["khasra_file_name"],
                  mime="application/octet-stream",
                  key=f"kh_dl_{row['id']}",
              )
            if row["b1_file_name"]:
              st.download_button(
                  label=f"📥 अमल पश्चात B-1 ({row['b1_file_name']})",
                  data=row["b1_file_data"],
                  file_name=row["b1_file_name"],
                  mime="application/octet-stream",
                  key=f"b1_dl_{row['id']}",
              )
          else:
            st.markdown("---")
            st.markdown("##### ✍️ अमल करें और प्रूफ अपलोड करें")
            with st.form(f"do_exec_form_{row['id']}"):
              new_status = st.selectbox(
                  "स्थिति बदलें", ["लंबित (Pending)", "अमल कर दिया गया"], index=1
              )
              kh_file = st.file_uploader(
                  "अमल के बाद का खसरा अपलोड करें (PDF/Image)",
                  type=["pdf", "jpg", "png", "jpeg"],
                  key=f"kh_{row['id']}",
              )
              b1_file = st.file_uploader(
                  "अमल के बाद का B-1 अपलोड करें (PDF/Image)",
                  type=["pdf", "jpg", "png", "jpeg"],
                  key=f"b1_{row['id']}",
              )
              update_btn = st.form_submit_button("अमल सुरक्षित करें")
              if update_btn:
                kh_name = kh_file.name if kh_file else ""
                kh_data = kh_file.read() if kh_file else b""
                b1_name = b1_file.name if b1_file else ""
                b1_data = b1_file.read() if b1_file else b""
                cur = conn.cursor()
                cur.execute(
                    """UPDATE execution_orders SET status = ?, khasra_file_name = ?, khasra_file_data = ?, b1_file_name = ?, b1_file_data = ?
                             WHERE id = ?""",
                    (
                        new_status,
                        kh_name,
                        kh_data,
                        b1_name,
                        b1_data,
                        row["id"],
                    ),
                )
                conn.commit()
                st.success("अमल स्टेटस अपडेट हो गया!")
                st.rerun()

          if st.button("🗑️ यह अमल आदेश डिलीट करें", key=f"del_exec_{row['id']}"):
            cur = conn.cursor()
            cur.execute("DELETE FROM execution_orders WHERE id = ?", (row["id"],))
            conn.commit()
            st.success("आदेश डिलीट कर दिया गया है!")
            st.rerun()
        st.markdown("---")
    else:
      st.info("कोई अमल आदेश दर्ज नहीं है।")
  conn.close()

# ==================== टैब 3: सीएम हेल्पलाइन ====================
with tab3:
  st.subheader("📞 सीएम हेल्पलाइन (CM Helpline) मॉनिटरिंग")
  conn = sqlite3.connect(DB_FILE)

  df_cm_all = pd.read_sql("SELECT * FROM cm_helpline", conn)

  df_active = (
      df_cm_all[df_cm_all["status"] != "बंद हो गई (Closed)"]
      if not df_cm_all.empty
      else pd.DataFrame()
  )
  df_closed = (
      df_cm_all[df_cm_all["status"] == "बंद हो गई (Closed)"]
      if not df_cm_all.empty
      else pd.DataFrame()
  )
  df_reply_pending = (
      df_active[
          (df_active["reply"].isna()) | (df_active["reply"].str.strip() == "")
      ]
      if not df_active.empty
      else pd.DataFrame()
  )

  total_active = len(df_active)
  total_closed = len(df_closed)
  total_reply_pending = len(df_reply_pending)
  total_all_cm = len(df_cm_all)

  st.markdown("##### 📊 काउंटर और फ़िल्टर")

  cm_choice = st.radio(
      "विकल्प चुनें:", [
          f"सक्रिय शिकायतें ({total_active})",
          f"जवाब बाकी ({total_reply_pending})",
          f"बंद हुई शिकायतें ({total_closed})",
          f"सभी शिकायतें ({total_all_cm})",
          "शिकायत दर्ज करें",
          "📂 PDF ऑटो-स्कैन व डेटाबेस जोड़ें",
      ],
      horizontal=True,
      key="cm_radio_menu",
  )

  st.markdown("---")

  if "शिकायत दर्ज करें" in cm_choice:
    with st.form("cm_form", clear_on_submit=True):
      c1, c2 = st.columns(2)
      with c1:
        comp_id = st.text_input(
            "शिकायत क्रमांक (Complaint ID) *", "", placeholder="नंबर दर्ज करें"
        )
        level = st.selectbox("स्तर (Level)", ["L1", "L2", "L3"])
        complainant = st.text_input("शिकायतकर्ता का नाम")
      with c2:
        mobile = st.text_input("शिकायतकर्ता का मोबाइल नंबर")
        date = st.date_input(
            "प्राप्ति दिनांक", datetime.date.today(), key="cm_dt"
        )
        status = st.selectbox(
            "स्थिति (Status)", [
                "पेंडिंग (Pending)",
                "जवाब दर्ज (Reply Submitted)",
                "बंद हो गई (Closed)",
            ]
        )

      subject = st.text_input("विषय / संक्षिप्त समस्या *")
      reply = st.text_area("जवाब / कार्रवाई का विवरण (Reply / Action Taken)")
      remarks = st.text_area("अन्य टिप्पणी (Remarks)")

      cm_submit = st.form_submit_button("शिकायत सुरक्षित करें")
      if cm_submit:
        if not comp_id.strip() or not subject.strip():
          st.error("कृपया शिकायत क्रमांक और विषय अवश्य भरें!")
        else:
          cursor = conn.cursor()
          cursor.execute(
              "SELECT id FROM cm_helpline WHERE comp_id = ?", (comp_id.strip(),)
          )
          if cursor.fetchone():
            st.error(f"त्रुटि: शिकायत क्रमांक '{comp_id}' पहले से दर्ज है!")
          else:
            cursor.execute(
                """INSERT INTO cm_helpline (comp_id, level, complainant, mobile, subject, status, date, reply, remarks)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    comp_id.strip(),
                    level,
                    complainant,
                    mobile,
                    subject,
                    status,
                    str(date),
                    reply,
                    remarks,
                ),
            )
            conn.commit()
            st.success("सीएम हेल्पलाइन शिकायत सफलतापूर्वक दर्ज हो गई!")
            st.rerun()

  elif "सक्रिय शिकायतें" in cm_choice:
    st.markdown("### ⏳ सक्रिय / पेंडिंग सीएम हेल्पलाइन शिकायतें")
    if not df_active.empty:
      for idx, row in df_active.reset_index(drop=True).iterrows():
        serial_no = idx + 1
        try:
          d_date = datetime.datetime.strptime(row["date"], "%Y-%m-%d").date()
          days_pending = (datetime.date.today() - d_date).days
        except:
          days_pending = 0

        mob_display = (
            row["mobile"]
            if "mobile" in df_active.columns and pd.notna(row["mobile"])
            else "उपलब्ध नहीं"
        )
        rep_display = (
            row["reply"]
            if "reply" in df_active.columns and pd.notna(row["reply"])
            else ""
        )

        with st.expander(
            f"[{serial_no}] 🆔 {row['comp_id']} | स्तर: {row['level']} | प्रेषक:"
            f" {row['complainant']} | ⏳ पेंडिंग दिन: {days_pending} दिन"
        ):
          st.write(f"**मोबाइल नंबर:** {mob_display}")
          st.write(f"**विषय:** {row['subject']}")
          st.write(f"**प्राप्ति दिनांक (मूल तारीख):** {row['date']}")
          st.write(f"**वर्तमान स्थिति:** {row['status']}")
          st.write(
              f"**दर्ज जवाब:** {rep_display if rep_display else 'अभी जवाब नहीं डला है'}"
          )
          st.write(f"**अन्य टिप्पणी:** {row['remarks']}")

          st.markdown("---")
          st.markdown("##### ✏️ जवाब व स्टेटस अपडेट करें")
          with st.form(f"update_cm_{row['id']}"):
            up_status = st.selectbox(
                "स्टेट्स चुनें", [
                    "पेंडिंग (Pending)",
                    "जवाब दर्ज (Reply Submitted)",
                    "बंद हो गई (Closed)",
                ],
                index=1
                if row["status"] == "जवाब दर्ज (Reply Submitted)"
                else 0,
            )
            up_reply = st.text_area(
                "यहाँ जवाब / कार्रवाई दर्ज करें",
                value=rep_display,
            )
            up_btn = st.form_submit_button("अपडेट सुरक्षित करें")
            if up_btn:
              cur = conn.cursor()
              cur.execute(
                  "UPDATE cm_helpline SET status = ?, reply = ? WHERE id = ?",
                  (up_status, up_reply, row["id"]),
              )
              conn.commit()
              st.success("शिकायत अपडेट हो गई!")
              st.rerun()

          if st.button("🗑️ यह शिकायत डिलीट करें", key=f"del_cm_{row['id']}"):
            cur = conn.cursor()
            cur.execute("DELETE FROM cm_helpline WHERE id = ?", (row["id"],))
            conn.commit()
            st.success("शिकायत डिलीट कर दी गई है!")
            st.rerun()
    else:
      st.info("कोई सक्रिय पेंडिंग शिकायत नहीं है।")

  elif "जवाब बाकी" in cm_choice:
    st.markdown("### ⚠️ जिन शिकायतों में अभी जवाब दर्ज नहीं हुआ है")
    if not df_reply_pending.empty:
      for idx, row in df_reply_pending.reset_index(drop=True).iterrows():
        serial_no = idx + 1
        try:
          d_date = datetime.datetime.strptime(row["date"], "%Y-%m-%d").date()
          days_pending = (datetime.date.today() - d_date).days
        except:
          days_pending = 0

        with st.expander(
            f"[{serial_no}] 🆔 {row['comp_id']} | प्रेषक: {row['complainant']} |"
            f" ⏳ पेंडिंग दिन: {days_pending}"
        ):
          st.write(f"**विषय:** {row['subject']}")
          st.write(f"**प्राप्ति दिनांक:** {row['date']}")
          st.warning(
              "⚠️ इस शिकायत में अभी तक कोई जवाब/कार्रवाई दर्ज नहीं की गई है।"
          )
    else:
      st.success("बहुत बढ़िया! ऐसी कोई शिकायत नहीं है जिसमें जवाब बाकी हो।")

  elif "बंद हुई शिकायतें" in cm_choice:
    st.markdown("### 🔒 बंद हो चुकी सीएम हेल्पलाइन शिकायतें (Closed History)")
    if not df_closed.empty:
      for idx, row in df_closed.reset_index(drop=True).iterrows():
        serial_no = idx + 1
        mob_display = (
            row["mobile"]
            if "mobile" in df_closed.columns and pd.notna(row["mobile"])
            else "उपलब्ध नहीं"
        )
        rep_display = (
            row["reply"]
            if "reply" in df_closed.columns and pd.notna(row["reply"])
            else ""
        )
        with st.expander(
            f"[{serial_no}] 🆔 {row['comp_id']} | प्रेषक: {row['complainant']}"
            f" | विषय: {row['subject']}"
        ):
          st.write(f"**मोबाइल नंबर:** {mob_display}")
          st.write(f"**स्तर:** {row['level']} | **प्राप्ति दिनांक:** {row['date']}")
          st.write(f"**अंतिम जवाब/कारण:** {rep_display}")
          if st.button(
              "🗑️ बंद शिकायत को डिलीट करें", key=f"del_closed_{row['id']}"
          ):
            cur = conn.cursor()
            cur.execute("DELETE FROM cm_helpline WHERE id = ?", (row["id"],))
            conn.commit()
            st.success("प्रविष्टि डिलीट कर दी गई है!")
            st.rerun()
    else:
      st.info("कोई भी शिकायत बंद नहीं हुई है।")

  elif "सभी शिकायतें" in cm_choice:
    st.markdown("### 🗂️ सभी दर्ज सीएम हेल्पलाइन शिकायतें (सक्रिय + बंद)")
    if not df_cm_all.empty:
      for idx, row in df_cm_all.reset_index(drop=True).iterrows():
        serial_no = idx + 1
        with st.expander(
            f"[{serial_no}] 🆔 {row['comp_id']} | स्थिति: {row['status']} |"
            f" प्रेषक: {row['complainant']}"
        ):
          st.write(f"**विषय:** {row['subject']}")
          st.write(
              f"**प्राप्ति दिनांक:** {row['date']} | **मोबाइल:** {row['mobile']}"
          )
          st.write(f"**जवाब:** {row['reply']}")
    else:
      st.info("कोई शिकायत दर्ज नहीं है।")

  else:
    st.markdown("### 📂 PDF ऑटो-स्कैन व डेटाबेस जोड़ें (pdfplumber)")
    st.info(
        "यहाँ अपनी सीएम हेल्पलाइन PDF अपलोड करें। ऐप अंतिम कॉलम में 'MAHRESH"
        " PARMAR' या 'MAHESH PARMAR' ढूंढकर पूरी रो का डेटा साफ-साफ अलग करेगा"
        " और आप उसे एक क्लिक में जोड़ सकेंगे।"
    )

    uploaded_file = st.file_uploader(
        "सीएम हेल्पलाइन की PDF अपलोड करें", type="pdf"
    )
    search_name = st.text_input(
        "खोजने के लिए नाम दर्ज करें", value="MAHESH PARMAR"
    )

    if uploaded_file is not None:
      if st.button("शिकायतें खोजें व प्रीव्यू देखें"):
        with st.spinner("PDF स्कैन की जा रही है..."):
          extracted_rows = []

          with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
              tables = page.extract_tables()
              for table in tables:
                for row in table:
                  clean_row = [
                      str(cell).strip().replace("\n", " ") if cell else ""
                      for cell in row
                  ]
                  if (
                      len(clean_row) > 0
                      and search_name.upper() in clean_row[-1].upper()
                  ):
                    extracted_rows.append(clean_row)

          if extracted_rows:
            st.success(
                f"🎉 कुल {len(extracted_rows)} शिकायतें मिली हैं जिनमें अंतिम"
                f" कॉलम में '{search_name}' दर्ज है!"
            )

            # हर एक मिली हुई शिकायत को कार्ड के रूप में दिखाना और सेव करने का विकल्प देना
            with st.form("auto_save_form"):
              selected_records = []
              for idx, r in enumerate(extracted_rows):
                # टेबल के फॉर्मेट के अनुसार डेटा अलग करना:
                # आमतौर पर: r[2] शिकायत नंबर होता है, r[3] प्रेषक, r[4] विषय, आदि
                comp_id = (
                    r[2]
                    if len(r) > 2 and r[2].isdigit()
                    else f"COMP_{idx}_{int(datetime.datetime.now().timestamp()) % 1000}"
                )
                complainant = r[3] if len(r) > 3 else "अज्ञात"
                subject = r[4] if len(r) > 4 else "पीडीएफ से प्राप्त शिकायत"
                reply_text = r[-1] if len(r) > 0 else ""

                st.markdown(
                    f"**शिकायत ID: {comp_id}** | प्रेषक: {complainant}"
                )
                st.write(f"📝 **विषय:** {subject}")
                st.write(f"💬 **अंतिम कॉलम विवरण:** {reply_text}")

                is_checked = st.checkbox(
                    f"इस शिकायत को डेटाबेस में जोड़ें (ID: {comp_id})",
                    value=True,
                    key=f"chk_row_{idx}",
                )
                if is_checked:
                  selected_records.append({
                      "comp_id": comp_id,
                      "complainant": complainant,
                      "subject": subject,
                      "reply": reply_text,
                  })
                st.markdown("---")

              save_button = st.form_submit_button(
                  "🚀 चुनी गई शिकायतें डेटाबेस में सेव करें"
              )
              if save_button:
                saved_count = 0
                cur = conn.cursor()
                for rec in selected_records:
                  try:
                    cur.execute(
                        """INSERT OR IGNORE INTO cm_helpline (comp_id, level, complainant, mobile, subject, status, date, reply, remarks)
                                 VALUES (?, 'L1', ?, 'उपलब्ध नहीं', ?, 'पेंडिंग (Pending)', ?, ?, 'PdfPlumber Auto Saved')""",
                        (
                            rec["comp_id"],
                            rec["complainant"],
                            rec["subject"],
                            str(datetime.date.today()),
                            rec["reply"],
                        ),
                    )
                    if cur.rowcount > 0:
                      saved_count += 1
                  except:
                    pass
                conn.commit()

                st.success(
                    f"सफलतापूर्वक **{saved_count}** नई शिकायतें आपकी सक्रिय"
                    " लिस्ट में जोड़ दी गई हैं!"
                )
                st.rerun()
          else:
            st.warning("इस नाम से अंतिम कॉलम में कोई शिकायत नहीं मिली।")

  conn.close()

# ==================== टैब 4: किसान डायरेक्टरी ====================
with tab4:
  st.subheader("👨‍🌾 किसान डेटाबेस (Farmer Directory)")
  conn = sqlite3.connect(DB_FILE)
  f_choice = st.radio(
      "विकल्प चुनें:", ["नया किसान दर्ज करें", "सभी किसानों की सूची व खोज"],
      horizontal=True,
  )

  if f_choice == "नया किसान दर्ज करें":
    with st.form("farmer_form", clear_on_submit=True):
      c1, c2 = st.columns(2)
      with c1:
        fname = st.text_input("किसान का पूरा नाम *")
        ffather = st.text_input("पिता/पति का नाम")
        fmobile = st.text_input("मोबाइल नंबर")
      with c2:
        faadhaar = st.text_input("आधार नंबर (अंतिम अंक या सुरक्षित)")
        fsurvey = st.text_input("जमीन का सर्वे नंबर / गाला नंबर *")

      f_submit = st.form_submit_button("किसान रिकॉर्ड सुरक्षित करें")
      if f_submit:
        if not fname.strip() or not fsurvey.strip():
          st.error("कृपया किसान का नाम और सर्वे नंबर अवश्य भरें!")
        else:
          cur = conn.cursor()
          cur.execute(
              """INSERT INTO farmers (name, father_name, mobile, aadhaar, survey_no)
                       VALUES (?, ?, ?, ?, ?)""",
              (
                  fname.strip(),
                  ffather,
                  fmobile,
                  faadhaar,
                  fsurvey.strip(),
              ),
          )
          conn.commit()
          st.success("किसान का डेटा सफलतापूर्वक सुरक्षित हो गया!")
          st.rerun()
  else:
    st.markdown("### दर्ज किसानों की सूची")
    search_q = st.text_input("🔍 नाम, मोबाइल या सर्वे नंबर से खोजें...")
    query = (
        f"SELECT * FROM farmers WHERE name LIKE '%{search_q}%' OR mobile LIKE"
        f" '%{search_q}%' OR survey_no LIKE '%{search_q}%'"
        if search_q.strip()
        else "SELECT * FROM farmers"
    )
    df_farmers = pd.read_sql(query, conn)
    if not df_farmers.empty:
      for idx, row in df_farmers.iterrows():
        serial_no = idx + 1
        st.markdown(
            f"**{serial_no}. {row['name']}** (पिता: {row['father_name']})"
        )
        st.write(
            f"📱 मोबाइल: {row['mobile']} | 🗺️ सर्वे नं.: {row['survey_no']}"
        )
        if st.button("🗑️ किसान रिकॉर्ड डिलीट करें", key=f"del_f_{row['id']}"):
          cur = conn.cursor()
          cur.execute("DELETE FROM farmers WHERE id = ?", (row["id"],))
          conn.commit()
          st.success("रिकॉर्ड डिलीट हो गया!")
          st.rerun()
        st.markdown("---")
    else:
      st.info("कोई किसान रिकॉर्ड नहीं मिला।")
  conn.close()

# ==================== टैब 5: दस्तावेज़ फोल्डर ====================
with tab5:
  st.subheader("📁 दस्तावेज़ फोल्डर (Khasra, B-1, Maps & PDFs)")
  conn = sqlite3.connect(DB_FILE)

  with st.form("doc_form", clear_on_submit=True):
    doc_name = st.text_input("दस्तावेज़ का नाम *")
    doc_type = st.selectbox(
        "प्रकार", ["खसरा", "बी-वन (B-1)", "नक्शा", "अन्य आदेश/पीडीएफ"]
    )
    doc_file = st.file_uploader(
        "फाइल अपलोड करें *", type=["pdf", "jpg", "png", "jpeg"]
    )
    doc_save = st.form_submit_button("फोल्डर में सहेजें")
    if doc_save:
      if not doc_name.strip() or not doc_file:
        st.error("कृपया दस्तावेज़ का नाम और फाइल दोनों दें!")
      else:
        c = conn.cursor()
        c.execute(
            """INSERT INTO documents (doc_name, doc_type, date, file_name, file_data)
                     VALUES (?, ?, ?, ?, ?)""",
            (
                doc_name.strip(),
                doc_type,
                str(datetime.date.today()),
                doc_file.name,
                doc_file.read(),
            ),
        )
        conn.commit()
        st.success("डॉक्यूमेंट सफलतापूर्वक सहेज लिया गया!")
        st.rerun()

  st.markdown("### सहेजे गए सभी दस्तावेज़")
  df_docs = pd.read_sql("SELECT * FROM documents", conn)
  if not df_docs.empty:
    for idx, row in df_docs.iterrows():
      serial_no = idx + 1
      with st.expander(
          f"[{serial_no}] 📂 {row['doc_name']} ({row['doc_type']}) -"
          f" {row['date']}"
      ):
        st.download_button(
            label=f"📥 डाउनलोड करें ({row['file_name']})",
            data=row["file_data"],
            file_name=row["file_name"],
            mime="application/octet-stream",
            key=f"doc_{row['id']}",
        )
        if st.button("🗑️ दस्तावेज़ डिलीट करें", key=f"del_doc_{row['id']}"):
          cur = conn.cursor()
          cur.execute("DELETE FROM documents WHERE id = ?", (row["id"],))
          conn.commit()
          st.success("दस्तावेज़ डिलीट कर दिया गया!")
          st.rerun()
  else:
    st.info("कोई दस्तावेज नहीं मिला।")
  conn.close()

# ==================== टैब 6: निजी डायरी ====================
with tab6:
  st.subheader("📔 निजी डायरी (Personal Notes)")
  conn = sqlite3.connect(DB_FILE)

  with st.form("diary_form", clear_on_submit=True):
    note_date = st.date_input(
        "दिनांक", datetime.date.today(), key="diary_dt"
    )
    note_text = st.text_area("आज के मुख्य नोट्स / बातें यहाँ लिखें... *")
    note_save = st.form_submit_button("नोट्स सेव करें")
    if note_save:
      if not note_text.strip():
        st.error("डायरी नोट खाली नहीं हो सकता!")
      else:
        c = conn.cursor()
        c.execute(
            "INSERT INTO diary (date, note) VALUES (?, ?)",
            (str(note_date), note_text),
        )
        conn.commit()
        st.success("डायरी नोट सुरक्षित हो गया!")
        st.rerun()

  df_diary = pd.read_sql("SELECT * FROM diary ORDER BY id DESC", conn)
  if not df_diary.empty:
    for idx, row in df_diary.iterrows():
      serial_no = idx + 1
      st.markdown(f"**[{serial_no}] 📅 {row['date']}**")
      st.write(row["note"])
      if st.button("🗑️ नोट डिलीट करें", key=f"del_diary_{row['id']}"):
        cur = conn.cursor()
        cur.execute("DELETE FROM diary WHERE id = ?", (row["id"],))
        conn.commit()
        st.success("नोट डिलीट हो गया!")
        st.rerun()
      st.markdown("---")
  else:
    st.info("डायरी खाली है।")
  conn.close()
