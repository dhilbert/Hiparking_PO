from flask import Flask, render_template_string, request, jsonify, send_file
import pymysql
from datetime import datetime
import pytz
import pandas as pd
import io
import os
from dotenv import load_dotenv

# =============================
# Flask App
# =============================
app = Flask(__name__)
load_dotenv()

# =============================
# DB CONFIG
# =============================
LOCAL_DB = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": 3306,
}

TABLE_NAME = "tessss"   # ★★★ app6과 동일하게 여기에 테이블명만 적으면 됨 ★★★


# =============================
# DB Connect
# =============================
def get_conn():
    return pymysql.connect(
        host=LOCAL_DB["host"],
        user=LOCAL_DB["user"],
        password=LOCAL_DB["password"],
        database=LOCAL_DB["database"],
        port=LOCAL_DB["port"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )


# =============================
# Time Helper
# =============================
def now_kst():
    return datetime.now(pytz.timezone("Asia/Seoul"))


# =============================
# HTML TEMPLATE
# =============================
HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>배포 메시지 기록</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">

<style>
body { background:#f4f4f4; }
.card { margin-top:40px; }
textarea { height:120px; }
.msg-item { position: relative; padding-right: 150px; }
.msg-actions {
    position: absolute;
    top: 10px;
    right: 10px;
}
</style>

<script>
function saveMsg() {
    const text = document.getElementById("msg").value;
    if (text.trim() === "") {
        alert("내용을 입력하세요");
        return;
    }
    fetch("/save", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text})
    }).then(r => r.json()).then(res => {
        if(res.result === "OK"){
            document.getElementById("msg").value="";
            loadList();
        }
    });
}

function loadList() {
    fetch("/list").then(r => r.json()).then(res => {
        const area = document.getElementById("msg-list");
        area.innerHTML = "";
        res.data.forEach(row => {
            const div = document.createElement("div");
            div.className = "alert alert-secondary msg-item";
            div.innerHTML = `
                <b>${row.dm_time}</b><br>${row.dm_text}
                <div class="msg-actions">
                    <button class="btn btn-warning btn-sm" onclick="editMsg(${row.dm_idx}, \`${row.dm_text}\`)">수정</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteMsg(${row.dm_idx})">삭제</button>
                </div>
            `;
            area.appendChild(div);
        });
    });
}

function deleteMsg(id) {
    const pw = prompt("삭제 비밀번호");
    if (pw !== "1234567890") {
        alert("비밀번호 틀림");
        return;
    }
    fetch("/delete/" + id, {method:"DELETE"})
    .then(r => r.json())
    .then(res => {
        if(res.result === "OK") loadList();
    });
}

function editMsg(id, oldText) {
    const newText = prompt("수정할 내용", oldText);
    if(newText === null) return;
    fetch("/update/" + id, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text:newText})
    }).then(r=>r.json()).then(res=>{
        if(res.result==="OK") loadList();
    });
}

window.onload = function(){ loadList(); }
</script>

</head>
<body>
<div class="container">
    <div class="card shadow">
        <div class="card-body">

            <h3 class="mb-3">📦 배포 기록</h3>
            <textarea id="msg" class="form-control"></textarea>
            <button class="btn btn-primary mt-3 w-100" onclick="saveMsg()">저장</button>
            <a href="/download" class="btn btn-success w-100 mt-2">엑셀 다운로드</a>

            <div id="msg-list" class="mt-3"></div>

        </div>
    </div>
</div>
</body>
</html>
"""


# =============================
# ROUTES
# =============================

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/save", methods=["POST"])
def save():
    data = request.get_json()
    text = data.get("text", "")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        f"INSERT INTO {TABLE_NAME} (dm_time, dm_text) VALUES (%s, %s)",
        (now_kst(), text)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"result": "OK"})


@app.route("/list")
def list_data():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY dm_idx DESC")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"data": rows})


@app.route("/delete/<int:id>", methods=["DELETE"])
def delete(id):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE dm_idx=%s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"result": "OK"})


@app.route("/update/<int:id>", methods=["PUT"])
def update(id):
    data = request.get_json()
    text = data.get("text", "")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        f"UPDATE {TABLE_NAME} SET dm_text=%s WHERE dm_idx=%s",
        (text, id)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"result": "OK"})


@app.route("/download")
def download():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY dm_idx DESC")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    df = pd.DataFrame(rows)
    df["dm_time"] = df["dm_time"].astype(str)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="messages")

    output.seek(0)

    filename = f"messages_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =============================
# MAIN
# =============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=True)
