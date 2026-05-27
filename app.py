from flask import Flask, render_template, request, redirect, session, make_response
from flask_mail import Mail, Message
import sqlite3
from datetime import datetime
import openpyxl
from io import BytesIO

app = Flask(__name__)
app.secret_key = "admin123"

# EMAIL SETTINGS - REPLACE THESE
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'bhukyanaveeen999@gmail.com'
app.config['MAIL_PASSWORD'] = 'uepa tqxo vzut dqsm'
app.config['MAIL_DEFAULT_SENDER'] = 'bhukyanaveeen999@gmail.com'

mail = Mail(app)

def connect_db():
    conn = sqlite3.connect('complaints.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = connect_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            category TEXT,
            complaint TEXT,
            status TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_table()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    category = request.form['category']
    complaint = request.form['complaint']
    date = datetime.now().strftime("%d %b %Y - %I:%M %p")

    conn = connect_db()
    conn.execute('''
        INSERT INTO complaints
        (name, email, category, complaint, status, date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, email, category, complaint, 'Pending', date))
    conn.commit()
    conn.close()
    return redirect('/?success=true')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "1234":
            session['admin'] = True
            return redirect('/admin')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')

@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect('/login')

    conn = connect_db()
    filter = request.args.get('filter', 'All')

    if filter == 'Pending':
        complaints = conn.execute("SELECT * FROM complaints WHERE status='Pending'").fetchall()
    elif filter == 'Resolved':
        complaints = conn.execute("SELECT * FROM complaints WHERE status='Resolved'").fetchall()
    else:
        complaints = conn.execute("SELECT * FROM complaints").fetchall()

    total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'").fetchone()[0]
    conn.close()

    return render_template(
        'admin.html',
        complaints=complaints,
        total=total,
        pending=pending,
        resolved=resolved,
        filter=filter
    )

@app.route('/update/<int:id>')
def update(id):
    conn = connect_db()
    complaint = conn.execute('SELECT * FROM complaints WHERE id = ?', (id,)).fetchone()
    conn.execute("UPDATE complaints SET status='Resolved' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    try:
        msg = Message(
            subject="Your Complaint Has Been Resolved ✅",
            recipients=[complaint['email']],
            body=f"""
Hello {complaint['name']},

Your complaint has been resolved!

Category: {complaint['category']}
Complaint: {complaint['complaint']}
Status: Resolved ✅

Thank you for reaching out to us.

Regards,
Complaint Manager Team
            """
        )
        mail.send(msg)
    except:
        pass

    return redirect('/admin')

@app.route('/delete/<int:id>')
def delete(id):
    conn = connect_db()
    conn.execute('DELETE FROM complaints WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/export')
def export():
    if 'admin' not in session:
        return redirect('/login')

    conn = connect_db()
    complaints = conn.execute('SELECT * FROM complaints').fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Complaints"
    ws.append(['ID', 'Name', 'Email', 'Category', 'Complaint', 'Status', 'Date'])

    for c in complaints:
        ws.append([c['id'], c['name'], c['email'], c['category'], c['complaint'], c['status'], c['date']])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = make_response(output.read())
    response.headers['Content-Disposition'] = 'attachment; filename=complaints.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    return response

@app.route('/track', methods=['GET', 'POST'])
def track():
    complaints = None
    email = None

    if request.method == 'POST':
        email = request.form['email']
        conn = connect_db()
        complaints = conn.execute(
            'SELECT * FROM complaints WHERE email = ?', (email,)
        ).fetchall()
        conn.close()

    return render_template('track.html', complaints=complaints, email=email)

if __name__ == '__main__':
    app.run(debug=True)