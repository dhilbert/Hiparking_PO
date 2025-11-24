# =============================================================
# app3_tinydb.py
# 배포 메시지 기록 서비스 (MySQL → TinyDB 기반 NoSQL)
# =============================================================

from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
from tinydb import TinyDB, Query
from datetime import datetime
import pytz
import pandas as pd
import io
import os

# -------------------------------------------------------------
# DB (파일 기반 NoSQL)
# -------------------------------------------------------------
DB_PATH = "messages.json"
db = TinyDB(DB_PATH)
Msg = Query()

# -------------------------------------------------------------
# TIME
# -------------------------------------------------------------
def now_kst():
    return datetime.now(pytz.timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

# -------------------------------------------------------------
# FLASK
# -------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# -------------------------------------------------------------
# HTML TEMPLATE (기존 app3 UI 그대로 유지)
# -------------------------------------------------------------
HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>📦 배포 기록 (TinyDB NoSQL)</title>
<link rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">

<style>
body { background:#f4f4f4; }
.card { margin-top:40px; }
textarea { height:120px; }
.msg-item { position: relative; padding-right: 150px; }
.msg-actions { position: absolute; top: 10px; right: 10px; }
</style>

<script>
function saveMsg() {
    const text = document.getElementById("msg").value;
    if (text.trim() === "") {
        alert("내용을 입력하세요");
        return;
    }

    fetch("/save", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({text})
    })
    .then(r=>r.json())
    .then(res=>{
        if(res.result==="OK"){
            document.getElementById("msg").value="";
            loadList();
        }
    });
}

function loadList() {
    fetch("/list")
    .then(r=>r.json())
    .then(res=>{
        const area = document.getElementById("msg-list");
        area.innerHTML = "";

        res.data.forEach(row=>{
            const div = document.createElement("div");
            div.className = "alert alert-secondary msg-item";
            div.innerHTML = `
                <b>${row.dm_time}</b><br>${row.dm_text}
                <div class="msg-actions">
                    <button class="btn btn-warning btn-sm"
                        onclick="editMsg(${row.id}, \`${row.dm_text}\`)">수정</button>
                    <button class="btn btn-danger btn-sm"
                        onclick="deleteMsg(${row.id})">삭제</button>
                </div>
            `;
            area.appendChild(div);
        });
    });
}

function deleteMsg(id) {
    const pw = prompt("삭제 비밀번호");
    if(pw !== "1234567890"){
        alert("비밀번호 틀림");
        return;
    }

    fetch("/delete/" + id, {method:"DELETE"})
    .then(r=>r.json())
    .then(res=>{
        if(res.result==="OK") loadList();
    });
}

function editMsg(id, oldText) {
    const nt = prompt("수정할 내용", oldText);
    if(nt===null) return;

    fetch("/update/" + id, {
        method:"PUT",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({text:nt})
    })
    .then(r=>r.json())
    .then(res=>{
        if(res.result==="OK") loadList();
    });
}

window.onload = function(){
    loadList();
}
</script>

</head>
<body>
<div class="container">
    <div class="card shadow">
        <div class="card-body">

            <h3 class="mb-3">📦 배포 기록 (TinyDB NoSQL)</h3>

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

# -------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/save", methods=["POST"])
def save():
    text = request.json.get("text", "")
    db.insert({"dm_time": now_kst(), "dm_text": text})
    return jsonify({"result": "OK"})

@app.route("/list")
def list_msgs():
    rows = db.all()
    # TinyDB는 id가 없어서 doc_id 사용
    data = [{"id": r.doc_id, "dm_time": r["dm_time"], "dm_text": r["dm_text"]} for r in rows[::-1]]
    return jsonify({"data": data})

@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_msg(id):
    db.remove(doc_ids=[id])
    return jsonify({"result": "OK"})

@app.route("/update/<int:id>", methods=["PUT"])
def update_msg(id):
    text = request.json.get("text", "")
    db.update({"dm_text": text}, doc_ids=[id])
    return jsonify({"result": "OK"})

@app.route("/download")
def download_excel():
    rows = db.all()
    data = [{"id": r.doc_id, "dm_time": r["dm_time"], "dm_text": r["dm_text"]} for r in rows]

    df = pd.DataFrame(data)

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

# -------------------------------------------------------------
# RUN
# -------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5033, debug=True)
