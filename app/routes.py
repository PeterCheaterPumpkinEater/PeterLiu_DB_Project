from app import app, conn
from flask import Flask, render_template, request, session, url_for, redirect
from datetime import datetime
import hashlib

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #form request
    username = request.form['username']
    password = request.form['password']

    #hashing password
    hashword = hashlib.sha256(password.encode())
    newpassword = (hashword.hexdigest())
    
    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, newpassword))
    data = cursor.fetchone()
    cursor.close()
    error = None
    
    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        error = 'Invalid username or password'
        return render_template('login.html', error=error)

@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #form request
    username = request.form['username']
    password = request.form['password']
    firstName = request.form['First Name']
    lastName = request.form['Last Name']
    bio = request.form['Bio']

    #hashing password
    hashword = hashlib.sha256(password.encode())
    newpassword = (hashword.hexdigest())
    
    cursor = conn.cursor()
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, newpassword, firstName, lastName, bio))
        conn.commit()
        cursor.close()
        return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html', username = session['username'])

@app.route('/browsegroup')
def browsegroup():
    cursor = conn.cursor()
    query = 'SELECT groupName, groupOwner from Friendgroup'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_friendgroups.html', data = data)

@app.route('/joingroup')
def joingroup():
    return render_template('joingroup.html')

@app.route('/joingroupAuth', methods = ['GET','POST'])
def joingroupAuth():
    username = session['username']
    group = request.form['Friend Group']
    groupleader = request.form['Group Creator']
    cursor = conn.cursor()
    query = 'SELECT * FROM Friendgroup WHERE groupName = %s AND groupOwner = %s'
    cursor.execute(query, (group, groupleader))
    data = cursor.fetchone()
    error = None
    if(data):
        cursor.execute('SELECT * FROM BelongTo WHERE member_username = %s AND owner_username = %s AND groupName = %s',
                       (username, groupleader, group))
        data = cursor.fetchone()
        if(data):
            error = 'You already belong to this group.'
            return render_template('joingroup.html', error = error)
        else:
            cursor.execute('INSERT INTO BelongTo VALUES(%s,%s,%s)', (username, groupleader, group))
            conn.commit()
            cursor.close()
            return render_template('home.html', username = session['username'])
    else:
        error = 'Incorrect Group Name and/or Group Creator'
        return render_template('joingroup.html', error = error)

@app.route('/creategroup')
def creategroup():
    return render_template('creategroup.html')

@app.route('/creategroupAuth', methods = ['GET','POST'])
def creategroupAuth():
    groupName = request.form['groupName']
    description = request.form['description']
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT * from Friendgroup WHERE groupOwner = %s and groupName = %s'
    cursor.execute(query, (username,groupName))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "You already made this group."
        return render_template('creategroup.html', error = error)
    else:
        cursor.execute('INSERT INTO FriendGroup VALUES(%s,%s,%s)', (username,groupName,description))
        cursor.execute('INSERT INTO BelongTo VALUES(%s,%s,%s)',  (username,username,groupName))
        conn.commit()
        cursor.close()
        return render_template('home.html')
    
@app.route('/people')
def people():
    cursor = conn.cursor()
    query = 'SELECT username, firstName, lastName from person'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_people.html', data = data)

@app.route('/followperson')
def followperson():
    return render_template('followperson.html')

@app.route('/followpersonAuth', methods = ['GET','POST'])
def followpersonAuth():
    curruser = session['username']
    username = request.form['username']    
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Follow WHERE username_followed = %s AND username_follower = %s', (username, curruser))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "You already sent a follow request or are already following this person."
        return render_template('followperson.html', error = error)
    else:
        ins = 'INSERT INTO follow VALUES(%s, %s, %s)'
        cursor.execute(ins, (username, curruser, 0))
        conn.commit()
        cursor.close()
        return render_template('home.html', username = session['username'])

@app.route('/notifications')
def notifications():
    username = session['username']
    cursor = conn.cursor()
    cursor.execute('SELECT username_follower FROM Follow WHERE username_followed = %s AND followstatus = 0', (username))
    data = cursor.fetchall()
    cursor.execute('SELECT photoID, photoPoster, filepath FROM Tagged NATURAL JOIN Photo WHERE username = %s AND tagstatus = 0', (username))
    tags = cursor.fetchall()
    cursor.close()
    return render_template('notifications.html', data = data, tags = tags)

@app.route('/notificationsAuth', methods = ['GET','POST'])
def notificationsAuth():
    username = session['username']
    cursor = conn.cursor()
    cursor.execute('SELECT username_follower FROM Follow WHERE username_followed = %s AND followstatus = 0', (username))
    data = cursor.fetchall()
    for line in data:
        follower = line.get('username_follower')
        if request.form[follower] == 'accept':
            cursor.execute('UPDATE Follow SET followstatus = 1 WHERE username_followed = %s AND username_follower = %s',
                           (username, follower))  
        elif request.form[follower] == 'deny':
            cursor.execute('DELETE FROM Follow WHERE username_followed = %s AND username_follower = %s',
                           (username, follower))
        else:
            pass
    cursor.execute('SELECT photoID FROM Tagged WHERE username = %s AND tagstatus = 0', (username))
    data = cursor.fetchall()
    for line in data:
        photoID = line.get('photoID')
        if request.form[str(photoID)] == 'accept':
            cursor.execute('UPDATE Tagged SET tagstatus = 1 WHERE username = %s AND photoID = %s',
                           (username, photoID))
        elif request.form[str(photoID)] == 'deny':
            cursor.execute('DELETE FROM Tagged WHERE username = %s AND photoID = %s',
                           (username, photoID))
        else:
            pass
    conn.commit()
    cursor.close()
    return render_template('home.html', username = session['username'])

@app.route('/post')
def post():
    cursor = conn.cursor()
    cursor.execute('SELECT groupName FROM BelongTo WHERE member_username = %s', (session['username']))
    data = cursor.fetchall()
    return render_template('post.html', data = data)

@app.route('/postAuth', methods = ['GET','POST'])
def postAuth():
    username = session['username']
    filepath = request.form['filepath']
    Followers = request.form['allFollowers']
    Tag = request.form['tag']
    time = datetime.now()
    if Followers == 'accept':
        allFollowers = 1
    else:
        allFollowers = 0
    caption = request.form['caption']
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Photo (postingDate, filepath, allFollowers, caption, photoPoster) VALUES(%s,%s,%s,%s,%s)',
                   (time, filepath, allFollowers, caption, username))
    cursor.execute('SELECT photoID FROM Photo WHERE photoID = (SELECT MAX(photoID) FROM Photo)')
    data = cursor.fetchone()
    photoID = data.get('photoID')
    cursor.execute('SELECT groupName, owner_username FROM BelongTo WHERE member_username = %s', (username))
    data = cursor.fetchall()
    for line in data:
        groupName = line.get('groupName')
        owner = line.get('owner_username')
        if request.form[groupName] == 'accept':
            cursor.execute('INSERT INTO SharedWith VALUES(%s,%s,%s)', (owner, groupName, photoID))
    if len(Tag) != 0:
        cursor.execute('SELECT * FROM Person WHERE username = %s', (Tag))
        user = cursor.fetchone()
        if not (user):
            error = 'This user doesn\'t exist.'
            return render_template('post.html', data = data, error = error)
        cursor.execute('INSERT INTO Tagged VALUES(%s,%s,%s)', (Tag, photoID, 0))
    conn.commit()
    cursor.close()
    return render_template('home.html')

@app.route('/view')
def view():
    username = session['username']
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT *
                      FROM photo
                      NATURAL JOIN ((
                           SELECT photoID
                           FROM SharedWith
                           JOIN BelongTo
                           ON member_username = %s)
                      UNION (
                           SELECT photoID
                           FROM Follow 
                           JOIN photo
                           ON username_follower = %s
                           AND username_followed = photoPoster
                           AND allFollowers = 1)) as m
                      LEFT JOIN (Tagged)
                      ON photo.photoID = Tagged.photoID
                      ORDER BY photo.photoID DESC''', (username, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('view.html', data = data)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
    

