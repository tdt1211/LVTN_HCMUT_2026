from flask import Flask, render_template, request, redirect, url_for, jsonify
import threading
import time
import os
import json
import datetime
import signal
import sys 

#from module.capture import capture_images
from module.train import train_model
from module.delete import delete_employee
from module.capture import get_global_session
from flask import Response, stream_with_context
from module.cleanup import cleanup_attendance_log

APP_ROOT = os.path.dirname(__file__)
EMP_FILE = os.path.join(APP_ROOT, 'employees.json')
ATT_FILE = os.path.join(APP_ROOT, 'attendance_log.json')

def shutdown_handler(sig, frame):
    print("Shutdown signal received")
    sess = get_global_session()
    sess.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, shutdown_handler)  # systemd stop

app = Flask(__name__)

def load_employees():
    if os.path.exists(EMP_FILE):
        with open(EMP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_employees(data):
    with open(EMP_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # The UI will control camera preview and guided capture via AJAX
    return render_template('register.html')


@app.route('/start_session', methods=['POST'])
def start_session():
    employees = load_employees()
    
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'ok': False, 'error': 'Tên không được để trống'})
        # 🔒 CHỐNG GHI TRÙNG
    if any(e.get("name") == name for e in employees):
        return jsonify({
            'ok': False,
            'error': 'Nhân viên đã tồn tại'
        })

    # save employee record
    
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    employees.append({'name': name, 'registered_at': now})
    save_employees(employees)

    sess = get_global_session()
    sess.start_preview(name)
    return jsonify({'ok': True})


def gen_mjpeg(session):
    while True:
        frame = session.get_frame_jpeg()
        if frame is None:
            time.sleep(0.05)
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    sess = get_global_session()
    return Response(stream_with_context(gen_mjpeg(sess)), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start_capture', methods=['POST'])
def start_capture():
    sess = get_global_session()
    if sess.name is None:
        return jsonify({'ok': False, 'error': 'Chưa tạo session đăng ký'})
    threading.Thread(target=sess.start_capture).start()
    return jsonify({'ok': True})


@app.route('/capture_status')
def capture_status():
    sess = get_global_session()
    return jsonify({
        'status': sess.status,
        'message': sess.message,
        'counts': sess.counts,
        'targets': sess.targets,
        'name': sess.name
    })

@app.route('/list')
def list_employees():
    employees = load_employees()
    return render_template('list.html', employees=employees)

@app.route('/delete/<name>', methods=['POST'])
def delete(name):
    name = name.strip()
    employees = load_employees()
    new_emps = [e for e in employees if e.get('name') != name]
    save_employees(new_emps)

    # run delete in background
    threading.Thread(target=lambda: delete_employee(name), daemon=True).start()

    return redirect(url_for('list_employees'))

def load_attendance():
    if os.path.exists(ATT_FILE):
        with open(ATT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.route('/history')
def history():
    logs = load_attendance()
    # logs: list of {name, datetime, type}
    # group by name + date
    from collections import defaultdict
    grouped = defaultdict(list)
    for rec in logs:
        try:
            dt = datetime.datetime.strptime(rec['datetime'], '%Y-%m-%d %H:%M:%S')
        except Exception:
            continue
        key = (rec.get('name'), dt.date().isoformat())
        grouped[key].append({'dt': dt, 'type': rec.get('type')})

    rows = []
    for (name, date), recs in grouped.items():
        # find first check-in and last check-out for the day
        ins = [r['dt'] for r in recs if r.get('type') == 'in']
        outs = [r['dt'] for r in recs if r.get('type') == 'out']
        check_in = min(ins) if ins else None
        check_out = max(outs) if outs else None
        work_time = ''
        check_in_str = check_in.strftime('%H:%M:%S') if check_in else ''
        check_out_str = check_out.strftime('%H:%M:%S') if check_out else ''
        if check_in and check_out:
            duration = check_out - check_in
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            work_time = f"{hours:02d}:{minutes:02d}"

        rows.append({
            'name': name,
            'date': date,
            'check_in': check_in_str,
            'check_out': check_out_str,
            'work_time': work_time
        })

    rows = sorted(rows, key=lambda r: (r['date'], r['name']))
    return render_template('history.html', rows=rows)

@app.route("/api/cleanup", methods=["POST"])
def api_cleanup():
    try:
        cleanup_attendance_log()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

def clear_all_records(log_file="attendance_log.json"):
    init_record = {
        "name": "_SYSTEM_",
        "datetime": "1970-01-01 00:00:00",
        "type": "init"
    }

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump([init_record], f, ensure_ascii=False, indent=2)

@app.route("/clear_history", methods=["POST"])
def clear_history():
    try:
        clear_all_records()
        return "", 200
    except Exception as e:
        print("[CLEAR HISTORY ERROR]", e)
        return "", 500

if __name__ == '__main__':
    app.run(
        debug=False,
        use_reloader=False,   # 🔥 BẮT BUỘC
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
