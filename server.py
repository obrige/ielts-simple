#!/usr/bin/env python3
"""IELTS Training System - offline server with answer scoring."""
import os,json,uuid,sqlite3,base64,csv,io
from flask import Flask,request,jsonify,render_template,redirect,session,send_from_directory

app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY','ielts-training-2024')
BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(BASE,'ielts.db')
ANSWERS_FILE=os.path.join(BASE,'correct_answers.json')
SK=app.secret_key[:64]

def gdb():
    db=sqlite3.connect(DB,timeout=10);db.row_factory=sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL");db.execute("PRAGMA foreign_keys=ON")
    return db

def load_answers():
    if not os.path.exists(ANSWERS_FILE): return {}
    with open(ANSWERS_FILE,'r') as f:
        data=json.load(f)
    ans={}
    for a in data:
        tid=str(a.get('test_id',''))
        qid=str(a.get('question_id',''))
        aid=str(a.get('answer_id',''))
        val=str(a.get('value','')).strip().lower()
        mt=a.get('match_type','exact')
        if tid not in ans: ans[tid]={}
        if qid not in ans[tid]: ans[tid][qid]={}
        ans[tid][qid][aid]={'value':val,'match_type':mt}
    return ans

def score_answers(sid):
    answers=load_answers()
    if not answers: return {'r':0,'l':0}
    db=gdb()
    scores={'l':0,'r':0}
    for tid,key in [('1','l'),('2','r')]:
        if tid not in answers: continue
        total=len(answers[tid])
        if total==0: continue
        correct=0
        user_ans=db.execute("SELECT question_id,answer_id,value FROM answers WHERE session_id=? AND test_id=?",(sid,int(tid))).fetchall()
        seen=set()
        for ua in user_ans:
            qid=str(ua['question_id'])
            aid=str(ua['answer_id'])
            uval=ua['value'].strip().lower()
            if qid in seen: continue
            if qid in answers[tid] and aid in answers[tid][qid]:
                ref=answers[tid][qid][aid]
                if ref['match_type']=='contains':
                    if ref['value'] in uval: correct+=1; seen.add(qid)
                elif ref['match_type']=='exact':
                    if uval==ref['value']: correct+=1; seen.add(qid)
                else:
                    if uval==ref['value']: correct+=1; seen.add(qid)
        scores[key]=round((correct/total)*100) if total>0 else 0
    db.close()
    return scores

def init_db():
    db=gdb()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT NOT NULL UNIQUE,country TEXT DEFAULT 'CN',is_admin INTEGER DEFAULT 0,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,user_id INTEGER NOT NULL,test_type TEXT DEFAULT 'academic',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS test_states(id INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT NOT NULL,test_id INTEGER NOT NULL,confirmed INTEGER DEFAULT 0,completed INTEGER DEFAULT 0,FOREIGN KEY(session_id) REFERENCES sessions(id),UNIQUE(session_id,test_id));
        CREATE TABLE IF NOT EXISTS answers(id INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT NOT NULL,test_id INTEGER NOT NULL,question_id TEXT NOT NULL,answer_id TEXT NOT NULL,value TEXT NOT NULL,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(session_id) REFERENCES sessions(id),UNIQUE(session_id,test_id,question_id,answer_id));
        CREATE TABLE IF NOT EXISTS custom_tests(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,slug TEXT NOT NULL UNIQUE,test_type TEXT DEFAULT 'listening',duration_minutes INTEGER DEFAULT 30,has_audio INTEGER DEFAULT 0,audio_src TEXT DEFAULT '',instructions_top TEXT DEFAULT '',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS custom_questions(id INTEGER PRIMARY KEY AUTOINCREMENT,test_id INTEGER NOT NULL,question_number TEXT NOT NULL,question_text TEXT,question_type TEXT DEFAULT 'multiple_choice',options_json TEXT DEFAULT '[]',correct_answer TEXT NOT NULL,match_type TEXT DEFAULT 'exact',FOREIGN KEY(test_id) REFERENCES custom_tests(id) ON DELETE CASCADE);
    ''')
    db.commit();db.close()
    db=gdb()
    try:
        db.execute("ALTER TABLE custom_tests ADD COLUMN duration_minutes INTEGER DEFAULT 30")
        db.execute("ALTER TABLE custom_tests ADD COLUMN has_audio INTEGER DEFAULT 0")
        db.execute("ALTER TABLE custom_tests ADD COLUMN audio_src TEXT DEFAULT ''")
        db.execute("ALTER TABLE custom_tests ADD COLUMN instructions_top TEXT DEFAULT ''")
    except: pass
    db.execute("INSERT OR IGNORE INTO users(name,email,is_admin) VALUES('Admin','admin@ielts.local',1)")
    db.execute("INSERT OR IGNORE INTO custom_tests(id,title,slug,test_type,duration_minutes) VALUES(1,'Listening','listening','listening',30)")
    db.execute("INSERT OR IGNORE INTO custom_tests(id,title,slug,test_type,duration_minutes) VALUES(2,'Reading','reading','reading',60)")
    db.execute("INSERT OR IGNORE INTO custom_tests(id,title,slug,test_type,duration_minutes) VALUES(3,'Writing','writing','writing',60)")
    db.commit();db.close()

@app.route('/css/<path:p>')
def css(p):return send_from_directory('static/css',p)
@app.route('/js/<path:p>')
def js(p):return send_from_directory('static/js',p)
@app.route('/img/<path:p>')
def img(p):return send_from_directory('static/img',p)
@app.route('/audio/<path:p>')
def audio(p):return send_from_directory('static/audio',p)
@app.route('/video/<path:p>')
def video(p):return send_from_directory('static/video',p)
@app.route('/fonts/<path:p>')
def fonts(p):return send_from_directory('static/fonts',p)
@app.route('/favicon.ico')
def favicon():return send_from_directory('static/img','favicon.ico')

@app.route('/')
def index():return redirect('/login')

@app.route('/register')
def reg_page():
    return render_template('register.html',csrfToken=SK,error='')

@app.route('/register',methods=['POST'])
def do_reg():
    name=request.form.get('name','').strip()
    email=request.form.get('email','').strip()
    country=request.form.get('country','')
    if not name or not email:return redirect('/register')
    db=gdb()
    u=db.execute("SELECT id,is_admin FROM users WHERE email=?",(email,)).fetchone()
    if u:
        uid=u['id'];session['is_admin']=bool(u['is_admin'])
    else:
        cur=db.execute("INSERT INTO users(name,email,country) VALUES(?,?,?)",(name,email,country))
        uid=cur.lastrowid
    db.commit();db.close()
    session['user_id']=uid;session['email']=email
    return render_template('register.html',csrfToken=SK,registered_id=uid,name=name)

@app.route('/login')
def login_page():
    return render_template('login.html',error='')

@app.route('/login',methods=['POST'])
def do_login():
    uid=request.form.get('user_id','').strip()
    if not uid: return render_template('login.html',error='Please enter your User ID')
    db=gdb()
    u=db.execute("SELECT * FROM users WHERE id=?",(int(uid),)).fetchone()
    db.close()
    if u:
        session['user_id']=u['id'];session['email']=u['email']
        session['is_admin']=bool(u['is_admin'])
        return redirect('/board')
    return render_template('login.html',error='User ID not found. Please register first.')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/board')
def board_page():
    uid=session.get('user_id')
    if not uid: return redirect('/login')
    db=gdb()
    sessions=db.execute("SELECT s.*,(SELECT COUNT(*) FROM test_states WHERE session_id=s.id AND completed=1) as done FROM sessions s WHERE s.user_id=? ORDER BY s.created_at DESC LIMIT 10",(uid,)).fetchall()
    db.close()
    return render_template('board.html',user_id=uid,email=session.get('email',''),recent_sessions=sessions)

@app.route('/results/history')
def results_history():
    uid=session.get('user_id')
    if not uid: return redirect('/login')
    db=gdb()
    sessions=db.execute("SELECT * FROM sessions WHERE user_id=? ORDER BY created_at DESC",(uid,)).fetchall()
    session_data=[]
    for s in sessions:
        scores=score_answers(s['id'])
        done=db.execute("SELECT COUNT(*) as c FROM test_states WHERE session_id=? AND completed=1",(s['id'],)).fetchone()['c']
        total=db.execute("SELECT COUNT(*) as c FROM test_states WHERE session_id=?",(s['id'],)).fetchone()['c']
        session_data.append({'session':s,'scores':scores,'done':done,'total':total})
    db.close()
    return render_template('results_history.html',user_id=uid,session_data=session_data)

@app.route('/tests/dashboard')
def dash_page():
    sid=session.get('session_id','')
    uid=session.get('user_id','')
    if not uid: return redirect('/login')
    states={}
    db=gdb()
    if sid:
        rows=db.execute("SELECT test_id,confirmed,completed FROM test_states WHERE session_id=? ORDER BY test_id",(sid,)).fetchall()
        for r in rows:
            states[r['test_id']]={'confirmed':r['confirmed'],'completed':r['completed']}
    tests=db.execute("SELECT * FROM custom_tests ORDER BY id").fetchall()
    db.close()
    return render_template('dashboard.html',session_id=sid,test_states=states,tests=tests,user_id=uid,csrf_token=SK)

@app.route('/tests/view/1')
def test1():
    return render_template('test_listening.html',session_id=session.get('session_id',''),csrfToken=SK,user_id=session.get('user_id',''))
@app.route('/tests/view/2')
def test2():
    return render_template('test_reading.html',session_id=session.get('session_id',''),csrfToken=SK,user_id=session.get('user_id',''))
@app.route('/tests/view/3')
def test3():
    return render_template('test_writing.html',session_id=session.get('session_id',''),csrfToken=SK,user_id=session.get('user_id',''))

@app.route('/tests/start/<tt>')
def start_test(tt):
    uid=session.get('user_id')
    if not uid:return redirect('/login')
    sid=str(uuid.uuid4()).replace('-','')[:26]
    db=gdb()
    db.execute("INSERT INTO sessions(id,user_id,test_type) VALUES(?,?,?)",(sid,uid,tt))
    tests=db.execute("SELECT id FROM custom_tests ORDER BY id").fetchall()
    for t in tests:db.execute("INSERT OR IGNORE INTO test_states(session_id,test_id) VALUES(?,?)",(sid,t['id']))
    db.commit();db.close()
    session['session_id']=sid;session['test_type']=tt
    return redirect('/tests/dashboard')

@app.route('/confirm',methods=['POST'])
def confirm():
    d=request.get_json()
    db=gdb()
    db.execute("UPDATE test_states SET confirmed=1 WHERE session_id=? AND test_id=?",(d.get('session_id'),d.get('test_id')))
    db.commit();db.close()
    return '1'

@app.route('/save',methods=['POST'])
def save():
    d=request.get_json();sid=d.get('session_id');tid=d.get('test_id')
    db=gdb()
    for a in d.get('answers',[]):
        db.execute("INSERT OR REPLACE INTO answers(session_id,test_id,question_id,answer_id,value) VALUES(?,?,?,?,?)",(sid,tid,a['question_id'],a['answer_id'],a['value']))
    db.commit();db.close()
    return '1'

@app.route('/next')
def nxt():
    sid=session.get('session_id','')
    if not sid:return redirect('/tests/dashboard')
    db=gdb()
    try:
        cur=db.execute("SELECT test_id FROM test_states WHERE session_id=? AND completed=0 ORDER BY test_id LIMIT 1",(sid,)).fetchone()
        if cur:
            db.execute("UPDATE test_states SET completed=1 WHERE session_id=? AND test_id=?",(sid,cur['test_id']))
            db.commit()
            nxt_cur=db.execute("SELECT test_id FROM test_states WHERE session_id=? AND completed=0 ORDER BY test_id LIMIT 1",(sid,)).fetchone()
            if nxt_cur:
                db.close()
                return redirect('/tests/dashboard')
        db.close()
    except Exception as e:
        db.close()
        raise e
    scores=score_answers(sid)
    token=base64.b64encode(json.dumps(scores).encode()).decode()
    return redirect(f'/results?token={token}')

@app.route('/results')
def results_page():
    token=request.args.get('token','')
    uid=session.get('user_id','')
    return render_template('results.html',token=token,user_id=uid)

@app.route('/state')
def get_state():
    sid=request.args.get('session_id',session.get('session_id',''))
    if not sid:return jsonify({})
    db=gdb()
    rows=db.execute("SELECT test_id,confirmed,completed FROM test_states WHERE session_id=? ORDER BY test_id",(sid,)).fetchall()
    db.close()
    states={}
    for r in rows:
        states[str(r['test_id'])]={'confirmed':r['confirmed'],'completed':r['completed']}
    return jsonify(states)

@app.route('/notice',methods=['POST'])
def notice():return jsonify({'success':True})

@app.route('/pages/<page>')
def pages(page):
    m={'terms':'terms.html','privacy':'privacy.html','accessibility':'accessibility.html','contact':'contact.html'}
    return render_template(m.get(page,'terms.html'))

# ============================================================
# ADMIN ROUTES
# ============================================================

def admin_check():
    if not session.get('is_admin'): return False
    return True

@app.route('/admin')
def admin_dashboard():
    if not admin_check(): return 'Access denied',403
    db=gdb()
    total_users=db.execute("SELECT COUNT(*) as c FROM users").fetchone()['c']
    total_sessions=db.execute("SELECT COUNT(*) as c FROM sessions").fetchone()['c']
    total_tests=db.execute("SELECT COUNT(*) as c FROM custom_tests").fetchone()['c']
    total_questions=db.execute("SELECT COUNT(*) as c FROM custom_questions").fetchone()['c']
    total_answers=db.execute("SELECT COUNT(*) as c FROM answers").fetchone()['c']
    recent_sessions=db.execute("SELECT s.id,s.user_id,u.name,s.test_type,s.created_at FROM sessions s JOIN users u ON s.user_id=u.id ORDER BY s.created_at DESC LIMIT 5").fetchall()
    db.close()
    return render_template('admin/dashboard.html',
        total_users=total_users,total_sessions=total_sessions,
        total_tests=total_tests,total_questions=total_questions,
        total_answers=total_answers,recent_sessions=recent_sessions)

@app.route('/admin/tests')
def admin_tests():
    if not admin_check(): return 'Access denied',403
    db=gdb()
    tests=db.execute("SELECT t.*,(SELECT COUNT(*) FROM custom_questions WHERE test_id=t.id) as qcount FROM custom_tests t ORDER BY t.id").fetchall()
    db.close()
    return render_template('admin/tests.html',tests=tests)

@app.route('/admin/tests/create',methods=['GET','POST'])
def admin_create_test():
    if not admin_check(): return 'Access denied',403
    if request.method=='POST':
        db=gdb()
        db.execute("INSERT INTO custom_tests(title,slug,test_type,duration_minutes,has_audio,audio_src,instructions_top) VALUES(?,?,?,?,?,?,?)",
            (request.form.get('title',''),request.form.get('slug',''),request.form.get('test_type','listening'),
             int(request.form.get('duration_minutes',30)),int(request.form.get('has_audio',0)),
             request.form.get('audio_src',''),request.form.get('instructions_top','')))
        db.commit();db.close()
        return redirect('/admin/tests')
    return render_template('admin/test_form.html',test=None)

@app.route('/admin/tests/<int:tid>/edit',methods=['GET','POST'])
def admin_edit_test(tid):
    if not admin_check(): return 'Access denied',403
    db=gdb()
    if request.method=='POST':
        db.execute("UPDATE custom_tests SET title=?,slug=?,test_type=?,duration_minutes=?,has_audio=?,audio_src=?,instructions_top=? WHERE id=?",
            (request.form.get('title',''),request.form.get('slug',''),request.form.get('test_type','listening'),
             int(request.form.get('duration_minutes',30)),int(request.form.get('has_audio',0)),
             request.form.get('audio_src',''),request.form.get('instructions_top',''),tid))
        db.commit();db.close()
        return redirect('/admin/tests')
    test=db.execute("SELECT * FROM custom_tests WHERE id=?",(tid,)).fetchone()
    db.close()
    if not test: return 'Not found',404
    return render_template('admin/test_form.html',test=test)

@app.route('/admin/tests/<int:tid>/delete',methods=['POST'])
def admin_del(tid):
    if not admin_check(): return 'Access denied',403
    db=gdb()
    db.execute("DELETE FROM custom_tests WHERE id=?",(tid,))
    db.commit();db.close()
    return redirect('/admin/tests')

@app.route('/admin/tests/<int:tid>/questions')
def admin_qs(tid):
    if not admin_check(): return 'Access denied',403
    db=gdb()
    test=db.execute("SELECT * FROM custom_tests WHERE id=?",(tid,)).fetchone()
    qs=db.execute("SELECT * FROM custom_questions WHERE test_id=? ORDER BY id",(tid,)).fetchall()
    db.close()
    if not test: return 'Not found',404
    return render_template('admin/questions.html',test=test,questions=qs)

@app.route('/admin/tests/<int:tid>/questions/add',methods=['POST'])
def admin_add_q(tid):
    if not admin_check(): return 'Access denied',403
    db=gdb()
    db.execute("INSERT INTO custom_questions(test_id,question_number,question_text,question_type,options_json,correct_answer,match_type) VALUES(?,?,?,?,?,?,?)",
        (tid,request.form.get('question_number',''),request.form.get('question_text',''),
         request.form.get('question_type','multiple_choice'),request.form.get('options_json','[]'),
         request.form.get('correct_answer',''),request.form.get('match_type','exact')))
    db.commit();db.close()
    return redirect(f'/admin/tests/{tid}/questions')

@app.route('/admin/tests/<int:tid>/questions/<int:qid>/edit',methods=['POST'])
def admin_edit_q(tid,qid):
    if not admin_check(): return 'Access denied',403
    db=gdb()
    db.execute("UPDATE custom_questions SET question_number=?,question_text=?,question_type=?,options_json=?,correct_answer=?,match_type=? WHERE id=? AND test_id=?",
        (request.form.get('question_number',''),request.form.get('question_text',''),
         request.form.get('question_type','multiple_choice'),request.form.get('options_json','[]'),
         request.form.get('correct_answer',''),request.form.get('match_type','exact'),qid,tid))
    db.commit();db.close()
    return redirect(f'/admin/tests/{tid}/questions')

@app.route('/admin/tests/<int:tid>/questions/<int:qid>/delete',methods=['POST'])
def admin_del_q(tid,qid):
    if not admin_check(): return 'Access denied',403
    db=gdb()
    db.execute("DELETE FROM custom_questions WHERE id=? AND test_id=?",(qid,tid))
    db.commit();db.close()
    return redirect(f'/admin/tests/{tid}/questions')

@app.route('/admin/tests/<int:tid>/questions/import',methods=['POST'])
def admin_import_csv(tid):
    if not admin_check(): return 'Access denied',403
    f=request.files.get('csvfile')
    if not f: return redirect(f'/admin/tests/{tid}/questions')
    content=f.read().decode('utf-8')
    reader=csv.DictReader(io.StringIO(content))
    db=gdb()
    for row in reader:
        db.execute("INSERT INTO custom_questions(test_id,question_number,question_text,question_type,options_json,correct_answer,match_type) VALUES(?,?,?,?,?,?,?)",
            (tid,row.get('question_number',''),row.get('question_text',''),row.get('question_type','multiple_choice'),
             row.get('options_json','[]'),row.get('correct_answer',''),row.get('match_type','exact')))
    db.commit();db.close()
    return redirect(f'/admin/tests/{tid}/questions')

@app.route('/admin/answers')
def admin_answers():
    if not admin_check(): return 'Access denied',403
    raw=''
    if os.path.exists(ANSWERS_FILE):
        with open(ANSWERS_FILE,'r') as f: raw=f.read()
    return render_template('admin/answers.html',answers_raw=raw)

@app.route('/admin/answers/save',methods=['POST'])
def admin_save_answers():
    if not admin_check(): return 'Access denied',403
    raw=request.form.get('answers_json','')
    try:
        data=json.loads(raw)
        with open(ANSWERS_FILE,'w') as f: json.dump(data,f,indent=2,ensure_ascii=False)
        return render_template('admin/answers.html',answers_raw=raw,msg='Saved OK')
    except Exception as e:
        return render_template('admin/answers.html',answers_raw=raw,error=str(e))

@app.route('/admin/users')
def admin_users():
    if not admin_check(): return 'Access denied',403
    db=gdb()
    users=db.execute('''
        SELECT u.id,u.name,u.email,u.country,u.created_at,
               COUNT(DISTINCT s.id) as session_count,
               COUNT(DISTINCT a.test_id) as tests_taken
        FROM users u
        LEFT JOIN sessions s ON s.user_id=u.id
        LEFT JOIN answers a ON a.session_id=s.id
        GROUP BY u.id ORDER BY u.created_at DESC
    ''').fetchall()
    db.close()
    return render_template('admin/users.html',users=users)

@app.route('/admin/users/<int:uid>')
def admin_user_detail(uid):
    if not admin_check(): return 'Access denied',403
    db=gdb()
    user=db.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    if not user: db.close(); return 'Not found',404
    sessions=db.execute('''
        SELECT s.*,
               (SELECT COUNT(*) FROM test_states WHERE session_id=s.id AND completed=1) as completed_tests,
               (SELECT COUNT(*) FROM test_states WHERE session_id=s.id) as total_tests
        FROM sessions s WHERE s.user_id=? ORDER BY s.created_at DESC
    ''',(uid,)).fetchall()
    session_data=[]
    for sess in sessions:
        scores=score_answers(sess['id'])
        session_data.append({'session':sess,'scores':scores})
    db.close()
    return render_template('admin/user_detail.html',user=user,session_data=session_data)

@app.route('/admin/export')
def admin_export():
    if not admin_check(): return 'Access denied',403
    db=gdb()
    tests=db.execute("SELECT * FROM custom_tests").fetchall()
    r=[]
    for t in tests:
        qs=db.execute("SELECT * FROM custom_questions WHERE test_id=?",(t['id'],)).fetchall()
        r.append({'test':dict(t),'questions':[dict(q) for q in qs]})
    db.close()
    return jsonify(r)

@app.route('/admin/import',methods=['POST'])
def admin_import():
    if not admin_check(): return 'Access denied',403
    data=request.get_json()
    if not data:return jsonify({'error':'No data'}),400
    db=gdb()
    for item in data:
        t=item.get('test',{})
        cur=db.execute("INSERT INTO custom_tests(title,slug,test_type,duration_minutes,has_audio,audio_src,instructions_top) VALUES(?,?,?,?,?,?,?)",
            (t.get('title',''),t.get('slug',''),t.get('test_type','listening'),
             t.get('duration_minutes',30),t.get('has_audio',0),
             t.get('audio_src',''),t.get('instructions_top','')))
        tid=cur.lastrowid
        for q in item.get('questions',[]):
            db.execute("INSERT INTO custom_questions(test_id,question_number,question_text,question_type,options_json,correct_answer,match_type) VALUES(?,?,?,?,?,?,?)",
                (tid,q.get('question_number',''),q.get('question_text',''),q.get('question_type','multiple_choice'),
                 q.get('options_json','[]'),q.get('correct_answer',''),q.get('match_type','exact')))
    db.commit();db.close()
    return jsonify({'status':'ok'})

if __name__=='__main__':
    init_db()
    ans=load_answers()
    print(f'IELTS Training -> http://localhost:5000')
    print(f'Correct answers loaded: {sum(len(v) for v in ans.values())} questions')
    print(f'Admin: admin@ielts.local -> /admin')
    app.run(debug=True,port=5000,host='0.0.0.0')
