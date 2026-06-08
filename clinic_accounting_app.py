import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
from supabase import create_client

INCOME_TYPES = [
    "ค่าบริการพยาบาล",
    "ค่าฝากครรภ์",
    "ค่าทำแผล",
    "ค่าฉีดยา",
    "ค่าตรวจสุขภาพ",
    "ค่าบริการอื่น ๆ",
]

EXPENSE_TYPES = [
    "ค่ายา",
    "ค่าเวชภัณฑ์",
    "ค่าอุปกรณ์การแพทย์",
    "ค่าเช่า",
    "ค่าน้ำ ค่าไฟ",
    "เงินเดือน",
    "ค่าทำบัญชี",
    "ค่าใช้จ่ายสำนักงาน",
    "ค่าใช้จ่ายอื่น ๆ",
]


@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def add_income(data):
    get_supabase().table("income").insert({
        "date": data[0], "receipt_no": data[1], "patient_name": data[2],
        "service_type": data[3], "amount": data[4], "note": data[5],
    }).execute()


def add_expense(data):
    get_supabase().table("expense").insert({
        "date": data[0], "doc_no": data[1], "vendor": data[2],
        "expense_type": data[3], "net_amount": data[4],
        "vat_amount": data[5], "total_amount": data[6], "note": data[7],
    }).execute()


def update_income(row_id, data):
    get_supabase().table("income").update(data).eq("id", row_id).execute()


def update_expense(row_id, data):
    get_supabase().table("expense").update(data).eq("id", row_id).execute()


def delete_row(table, row_id):
    get_supabase().table(table).delete().eq("id", row_id).execute()


def load_table(table):
    resp = get_supabase().table(table).select("*").order("id", desc=True).execute()
    return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()


# --- UI ---
st.set_page_config(page_title="Clinic Accounting", layout="wide")
st.title("โปรแกรมบัญชีคลินิกพยาบาลและผดุงครรภ์")

menu = st.sidebar.radio(
    "เมนู",
    ["บันทึกรายรับ", "บันทึกค่าใช้จ่าย", "รายงานสรุป", "ข้อมูลรายรับ", "ข้อมูลค่าใช้จ่าย"],
)

# ============ บันทึกรายรับ ============
if menu == "บันทึกรายรับ":
    st.header("บันทึกรายรับค่ารักษาพยาบาล / ค่าบริการ")

    with st.form("income_form"):
        income_date = st.date_input("วันที่", date.today())
        receipt_no = st.text_input("เลขที่ใบเสร็จ")
        patient_name = st.text_input("ชื่อลูกค้า/ผู้รับบริการ")
        service_type = st.selectbox("ประเภทรายได้", INCOME_TYPES)
        amount = st.number_input("จำนวนเงิน", min_value=0.0, step=100.0)
        note = st.text_area("หมายเหตุ")
        submitted = st.form_submit_button("บันทึกรายรับ")

        if submitted:
            add_income((str(income_date), receipt_no, patient_name, service_type, amount, note))
            st.success("บันทึกรายรับเรียบร้อยแล้ว")

# ============ บันทึกค่าใช้จ่าย ============
elif menu == "บันทึกค่าใช้จ่าย":
    st.header("บันทึกค่าใช้จ่าย / ค่ายา / เวชภัณฑ์")
    st.info("กรณีคลินิกได้รับยกเว้น VAT ภาษีซื้อจากค่ายาและค่าใช้จ่ายต่าง ๆ มักขอคืนไม่ได้ จึงบันทึกเป็นต้นทุนรวม VAT")

    with st.form("expense_form"):
        expense_date = st.date_input("วันที่", date.today())
        doc_no = st.text_input("เลขที่เอกสาร/ใบกำกับภาษี")
        vendor = st.text_input("ผู้ขาย/เจ้าหนี้")
        expense_type = st.selectbox("ประเภทค่าใช้จ่าย", EXPENSE_TYPES)
        net_amount = st.number_input("มูลค่าก่อน VAT", min_value=0.0, step=100.0)
        vat_amount = st.number_input("VAT ซื้อ", min_value=0.0, step=10.0)
        total_amount = net_amount + vat_amount
        st.write(f"ยอดรวมที่บันทึกเป็นต้นทุน/ค่าใช้จ่าย: {total_amount:,.2f} บาท")
        note = st.text_area("หมายเหตุ")
        submitted = st.form_submit_button("บันทึกค่าใช้จ่าย")

        if submitted:
            add_expense((str(expense_date), doc_no, vendor, expense_type, net_amount, vat_amount, total_amount, note))
            st.success("บันทึกค่าใช้จ่ายเรียบร้อยแล้ว")

# ============ รายงานสรุป ============
elif menu == "รายงานสรุป":
    st.header("รายงานสรุปรายรับ - ค่าใช้จ่าย")

    income_df = load_table("income")
    expense_df = load_table("expense")

    total_income = income_df["amount"].sum() if not income_df.empty else 0
    total_expense = expense_df["total_amount"].sum() if not expense_df.empty else 0
    profit = total_income - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("รายรับรวม", f"{total_income:,.2f} บาท")
    col2.metric("ค่าใช้จ่ายรวม", f"{total_expense:,.2f} บาท")
    col3.metric("กำไร/ขาดทุนเบื้องต้น", f"{profit:,.2f} บาท")

    st.subheader("สรุปรายรับตามประเภท")
    if not income_df.empty:
        st.dataframe(income_df.groupby("service_type")["amount"].sum().reset_index())

    st.subheader("สรุปค่าใช้จ่ายตามประเภท")
    if not expense_df.empty:
        st.dataframe(expense_df.groupby("expense_type")["total_amount"].sum().reset_index())

# ============ ข้อมูลรายรับ ============
elif menu == "ข้อมูลรายรับ":
    st.header("ข้อมูลรายรับทั้งหมด")
    income_data = load_table("income")

    # --- ค้นหา & กรอง ---
    if not income_data.empty:
        st.subheader("🔍 ค้นหา & กรอง")
        fc1, fc2, fc3 = st.columns(3)
        search_text = fc1.text_input("ค้นหา (ชื่อ/เลขใบเสร็จ/หมายเหตุ)", key="search_income")
        filter_type = fc2.selectbox("ประเภทรายได้", ["ทั้งหมด"] + INCOME_TYPES, key="filter_income_type")
        date_range = fc3.date_input("ช่วงวันที่", value=[], key="filter_income_date")

        filtered = income_data.copy()
        if search_text:
            mask = filtered.apply(lambda r: search_text.lower() in str(r.values).lower(), axis=1)
            filtered = filtered[mask]
        if filter_type != "ทั้งหมด":
            filtered = filtered[filtered["service_type"] == filter_type]
        if date_range:
            if len(date_range) == 2:
                filtered = filtered[(filtered["date"] >= str(date_range[0])) & (filtered["date"] <= str(date_range[1]))]
            elif len(date_range) == 1:
                filtered = filtered[filtered["date"] == str(date_range[0])]

        st.caption(f"แสดง {len(filtered)} จาก {len(income_data)} รายการ")
        st.dataframe(filtered, use_container_width=True)

        buf = BytesIO()
        filtered.to_excel(buf, index=False, sheet_name="รายรับ", engine="openpyxl")
        st.download_button(
            label="📥 Export Excel รายรับ",
            data=buf.getvalue(),
            file_name="income_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        st.divider()
        st.subheader("แก้ไข / ลบรายการรายรับ")

        labels = [
            f"#{r['id']} | {r['date']} | {r['patient_name']} | {r['service_type']} | {r['amount']:,.2f}"
            for _, r in filtered.iterrows()
        ]
        if not labels:
            st.info("ไม่พบรายการที่ตรงกับเงื่อนไข")
            st.stop()
        selected_label = st.selectbox("เลือกรายการ", labels, key="sel_income")
        selected_idx = labels.index(selected_label)
        row = filtered.iloc[selected_idx]
        row_id = int(row["id"])

        col_edit, col_del = st.columns(2)

        # --- ลบ ---
        with col_del:
            st.markdown("#### ลบรายการ")
            if st.button("🗑️ ลบรายการนี้", key="del_income", type="primary"):
                st.session_state["confirm_del_income"] = row_id

            if st.session_state.get("confirm_del_income") == row_id:
                st.warning(f"ยืนยันลบรายการ #{row_id}?")
                c1, c2 = st.columns(2)
                if c1.button("✅ ยืนยันลบ", key="confirm_y_income"):
                    delete_row("income", row_id)
                    st.session_state.pop("confirm_del_income", None)
                    st.success("ลบเรียบร้อย")
                    st.rerun()
                if c2.button("❌ ยกเลิก", key="confirm_n_income"):
                    st.session_state.pop("confirm_del_income", None)
                    st.rerun()

        # --- แก้ไข ---
        with col_edit:
            st.markdown("#### แก้ไขรายการ")
            with st.form("edit_income_form"):
                edit_date = st.date_input("วันที่", datetime.strptime(row["date"], "%Y-%m-%d").date(), key="ei_date")
                edit_receipt = st.text_input("เลขที่ใบเสร็จ", row["receipt_no"], key="ei_receipt")
                edit_patient = st.text_input("ชื่อลูกค้า", row["patient_name"], key="ei_patient")
                edit_type = st.selectbox("ประเภท", INCOME_TYPES, index=INCOME_TYPES.index(row["service_type"]) if row["service_type"] in INCOME_TYPES else 0, key="ei_type")
                edit_amount = st.number_input("จำนวนเงิน", value=float(row["amount"]), min_value=0.0, step=100.0, key="ei_amount")
                edit_note = st.text_area("หมายเหตุ", row["note"] or "", key="ei_note")
                if st.form_submit_button("💾 บันทึกแก้ไข"):
                    update_income(row_id, {
                        "date": str(edit_date), "receipt_no": edit_receipt,
                        "patient_name": edit_patient, "service_type": edit_type,
                        "amount": edit_amount, "note": edit_note,
                    })
                    st.success("แก้ไขเรียบร้อย")
                    st.rerun()

# ============ ข้อมูลค่าใช้จ่าย ============
elif menu == "ข้อมูลค่าใช้จ่าย":
    st.header("ข้อมูลค่าใช้จ่ายทั้งหมด")
    expense_data = load_table("expense")

    # --- ค้นหา & กรอง ---
    if not expense_data.empty:
        st.subheader("🔍 ค้นหา & กรอง")
        fc1, fc2, fc3 = st.columns(3)
        search_exp = fc1.text_input("ค้นหา (ผู้ขาย/เลขเอกสาร/หมายเหตุ)", key="search_expense")
        filter_exp_type = fc2.selectbox("ประเภทค่าใช้จ่าย", ["ทั้งหมด"] + EXPENSE_TYPES, key="filter_expense_type")
        date_range_exp = fc3.date_input("ช่วงวันที่", value=[], key="filter_expense_date")

        filtered_exp = expense_data.copy()
        if search_exp:
            mask = filtered_exp.apply(lambda r: search_exp.lower() in str(r.values).lower(), axis=1)
            filtered_exp = filtered_exp[mask]
        if filter_exp_type != "ทั้งหมด":
            filtered_exp = filtered_exp[filtered_exp["expense_type"] == filter_exp_type]
        if date_range_exp:
            if len(date_range_exp) == 2:
                filtered_exp = filtered_exp[(filtered_exp["date"] >= str(date_range_exp[0])) & (filtered_exp["date"] <= str(date_range_exp[1]))]
            elif len(date_range_exp) == 1:
                filtered_exp = filtered_exp[filtered_exp["date"] == str(date_range_exp[0])]

        st.caption(f"แสดง {len(filtered_exp)} จาก {len(expense_data)} รายการ")
        st.dataframe(filtered_exp, use_container_width=True)

        buf = BytesIO()
        filtered_exp.to_excel(buf, index=False, sheet_name="ค่าใช้จ่าย", engine="openpyxl")
        st.download_button(
            label="📥 Export Excel ค่าใช้จ่าย",
            data=buf.getvalue(),
            file_name="expense_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        st.divider()
        st.subheader("แก้ไข / ลบรายการค่าใช้จ่าย")

        labels_exp = [
            f"#{r['id']} | {r['date']} | {r['vendor']} | {r['expense_type']} | {r['total_amount']:,.2f}"
            for _, r in filtered_exp.iterrows()
        ]
        if not labels_exp:
            st.info("ไม่พบรายการที่ตรงกับเงื่อนไข")
            st.stop()
        selected_label_exp = st.selectbox("เลือกรายการ", labels_exp, key="sel_expense")
        selected_idx_exp = labels_exp.index(selected_label_exp)
        row_exp = filtered_exp.iloc[selected_idx_exp]
        row_id_exp = int(row_exp["id"])

        col_edit2, col_del2 = st.columns(2)

        # --- ลบ ---
        with col_del2:
            st.markdown("#### ลบรายการ")
            if st.button("🗑️ ลบรายการนี้", key="del_expense", type="primary"):
                st.session_state["confirm_del_expense"] = row_id_exp

            if st.session_state.get("confirm_del_expense") == row_id_exp:
                st.warning(f"ยืนยันลบรายการ #{row_id_exp}?")
                c1, c2 = st.columns(2)
                if c1.button("✅ ยืนยันลบ", key="confirm_y_expense"):
                    delete_row("expense", row_id_exp)
                    st.session_state.pop("confirm_del_expense", None)
                    st.success("ลบเรียบร้อย")
                    st.rerun()
                if c2.button("❌ ยกเลิก", key="confirm_n_expense"):
                    st.session_state.pop("confirm_del_expense", None)
                    st.rerun()

        # --- แก้ไข ---
        with col_edit2:
            st.markdown("#### แก้ไขรายการ")
            with st.form("edit_expense_form"):
                ed_date = st.date_input("วันที่", datetime.strptime(row_exp["date"], "%Y-%m-%d").date(), key="ee_date")
                ed_doc = st.text_input("เลขที่เอกสาร", row_exp["doc_no"], key="ee_doc")
                ed_vendor = st.text_input("ผู้ขาย", row_exp["vendor"], key="ee_vendor")
                ed_type = st.selectbox("ประเภท", EXPENSE_TYPES, index=EXPENSE_TYPES.index(row_exp["expense_type"]) if row_exp["expense_type"] in EXPENSE_TYPES else 0, key="ee_type")
                ed_net = st.number_input("มูลค่าก่อน VAT", value=float(row_exp["net_amount"]), min_value=0.0, step=100.0, key="ee_net")
                ed_vat = st.number_input("VAT ซื้อ", value=float(row_exp["vat_amount"]), min_value=0.0, step=10.0, key="ee_vat")
                ed_total = ed_net + ed_vat
                st.write(f"ยอดรวม: {ed_total:,.2f} บาท")
                ed_note = st.text_area("หมายเหตุ", row_exp["note"] or "", key="ee_note")
                if st.form_submit_button("💾 บันทึกแก้ไข"):
                    update_expense(row_id_exp, {
                        "date": str(ed_date), "doc_no": ed_doc, "vendor": ed_vendor,
                        "expense_type": ed_type, "net_amount": ed_net,
                        "vat_amount": ed_vat, "total_amount": ed_total, "note": ed_note,
                    })
                    st.success("แก้ไขเรียบร้อย")
                    st.rerun()
