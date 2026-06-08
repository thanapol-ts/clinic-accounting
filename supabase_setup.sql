-- รันใน Supabase SQL Editor เพื่อสร้างตาราง

CREATE TABLE income (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    date TEXT,
    receipt_no TEXT,
    patient_name TEXT,
    service_type TEXT,
    amount DOUBLE PRECISION,
    note TEXT
);

CREATE TABLE expense (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    date TEXT,
    doc_no TEXT,
    vendor TEXT,
    expense_type TEXT,
    net_amount DOUBLE PRECISION,
    vat_amount DOUBLE PRECISION,
    total_amount DOUBLE PRECISION,
    note TEXT
);
