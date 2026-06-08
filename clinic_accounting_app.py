import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from supabase import create_client

@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def add_income(data):
    supabase = get_supabase()
    supabase.table("income").insert({
        "date": data[0],
        "receipt_no": data[1],
        "patient_name": data[2],
        "service_type": data[3],
        "amount": data[4],
        "note": data[5],
    }).execute()

def add_expense(data):
    supabase = get_supabase()
    supabase.table("expense").insert({
        "date": data[0],
        "doc_no": data[1],
        "vendor": data[2],
        "expense_type": data[3],
        "net_amount": data[4],
        "vat_amount": data[5],
        "total_amount": data[6],
        "note": data[7],
    }).execute()

def load_table(table):
    supabase = get_supabase()
    resp = supabase.table(table).select("*").execute()
    return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()

st.set_page_config(page_title="Clinic Accounting", layout="wide")
st.title("โปรแกรมบัญชีคลินิกพยาบาลและผดุงครรภ์")

menu = st.sidebar.radio(
    "เมนู",
    ["บันทึกรายรับ", "บันทึกค่าใช้จ่าย", "รายงานสรุป", "ข้อมูลรายรับ", "ข้อมูลค่าใช้จ่าย"]
)

if menu == "บันทึกรายรับ":
    st.header("บันทึกรายรับค่ารักษาพยาบาล / ค่าบริการ")

    with st.form("income_form"):
        income_date = st.date_input("วันที่", date.today())
        receipt_no = st.text_input("เลขที่ใบเสร็จ")
        patient_name = st.text_input("ชื่อลูกค้า/ผู้รับบริการ")
        service_type = st.selectbox(
            "ประเภทรายได้",
            [
                "ค่าบริการพยาบาล",
                "ค่าฝากครรภ์",
                "ค่าทำแผล",
                "ค่าฉีดยา",
                "ค่าตรวจสุขภาพ",
                "ค่าบริการอื่น ๆ"
            ]
        )
        amount = st.number_input("จำนวนเงิน", min_value=0.0, step=100.0)
        note = st.text_area("หมายเหตุ")

        submitted = st.form_submit_button("บันทึกรายรับ")

        if submitted:
            add_income((
                str(income_date),
                receipt_no,
                patient_name,
                service_type,
                amount,
                note
            ))
            st.success("บันทึกรายรับเรียบร้อยแล้ว")

elif menu == "บันทึกค่าใช้จ่าย":
    st.header("บันทึกค่าใช้จ่าย / ค่ายา / เวชภัณฑ์")

    st.info("กรณีคลินิกได้รับยกเว้น VAT ภาษีซื้อจากค่ายาและค่าใช้จ่ายต่าง ๆ มักขอคืนไม่ได้ จึงบันทึกเป็นต้นทุนรวม VAT")

    with st.form("expense_form"):
        expense_date = st.date_input("วันที่", date.today())
        doc_no = st.text_input("เลขที่เอกสาร/ใบกำกับภาษี")
        vendor = st.text_input("ผู้ขาย/เจ้าหนี้")
        expense_type = st.selectbox(
            "ประเภทค่าใช้จ่าย",
            [
                "ค่ายา",
                "ค่าเวชภัณฑ์",
                "ค่าอุปกรณ์การแพทย์",
                "ค่าเช่า",
                "ค่าน้ำ ค่าไฟ",
                "เงินเดือน",
                "ค่าทำบัญชี",
                "ค่าใช้จ่ายสำนักงาน",
                "ค่าใช้จ่ายอื่น ๆ"
            ]
        )
        net_amount = st.number_input("มูลค่าก่อน VAT", min_value=0.0, step=100.0)
        vat_amount = st.number_input("VAT ซื้อ", min_value=0.0, step=10.0)
        total_amount = net_amount + vat_amount
        st.write(f"ยอดรวมที่บันทึกเป็นต้นทุน/ค่าใช้จ่าย: {total_amount:,.2f} บาท")

        note = st.text_area("หมายเหตุ")
        submitted = st.form_submit_button("บันทึกค่าใช้จ่าย")

        if submitted:
            add_expense((
                str(expense_date),
                doc_no,
                vendor,
                expense_type,
                net_amount,
                vat_amount,
                total_amount,
                note
            ))
            st.success("บันทึกค่าใช้จ่ายเรียบร้อยแล้ว")

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

elif menu == "ข้อมูลรายรับ":
    st.header("ข้อมูลรายรับทั้งหมด")
    income_data = load_table("income")
    st.dataframe(income_data)

    if not income_data.empty:
        buf = BytesIO()
        income_data.to_excel(buf, index=False, sheet_name="รายรับ", engine="openpyxl")
        st.download_button(
            label="📥 Export Excel รายรับ",
            data=buf.getvalue(),
            file_name="income_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

elif menu == "ข้อมูลค่าใช้จ่าย":
    st.header("ข้อมูลค่าใช้จ่ายทั้งหมด")
    expense_data = load_table("expense")
    st.dataframe(expense_data)

    if not expense_data.empty:
        buf = BytesIO()
        expense_data.to_excel(buf, index=False, sheet_name="ค่าใช้จ่าย", engine="openpyxl")
        st.download_button(
            label="📥 Export Excel ค่าใช้จ่าย",
            data=buf.getvalue(),
            file_name="expense_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
