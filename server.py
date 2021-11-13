"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
# accessible as a variable in index.html:
import random
from typing import Any, Tuple
from nocache import nocache

from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, flash
from datetime import date
from flask_session import Session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.74.246.148/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.74.246.148/proj1part2"
#
DATABASEURI = "postgresql://sr3846:5390@34.74.246.148/proj1part2"

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)


#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#

# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
    """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback;
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/2.0.x/quickstart/?highlight=routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/2.0.x/api/?highlight=incoming%20request%20data

  """

    # DEBUG: this is debugging code to see what request looks like
    # print(request.args)

    #
    # example of a database query
    #
    # cursor = g.conn.execute("SELECT name FROM test")
    # names = []
    # for result in cursor:
    #   names.append(result['name'])  # can also be accessed using result[0]
    # cursor.close()

    #
    # Flask uses Jinja templates, which is an extension to HTML where you can
    # pass data to a template and dynamically generate HTML based on the data
    # (you can think of it as simple PHP)
    # documentation: https://realpython.com/primer-on-jinja-templating/
    #
    # You can see an example template in templates/index.html
    #
    # context are the variables that are passed to the template.
    # for example, "data" key in the context variable defined below will be
    # accessible as a variable in index.html:
    #
    #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
    #     <div>{{data}}</div>
    #
    #     # creates a <div> tag for each element in data
    #     # will print:
    #     #
    #     #   <div>grace hopper</div>
    #     #   <div>alan turing</div>
    #     #   <div>ada lovelace</div>
    #     #
    #     {% for n in data %}
    #     <div>{{n}}</div>
    #     {% endfor %}
    #
    # context = dict(data = names)

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    if session["id"] is not None:
        if session["type"] == "resident":
            return render_template("residentHome.html")
        else:
            if session["deptid"] == 4000:
                return render_template("employeeHome_admissions.html")
            elif session["deptid"] == 4001:
                return render_template("employeeHome_finance.html")
            else:
                return render_template("employeeHome_facilities.html")
    else:
        return render_template("index.html")


#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#

# @app.route('/residentHome')
# def residents():
#     print(session["id"])
#     if session["id"] is not None:
#         today = str(date.today())
#         context = dict(todays_date=today)
#         return render_template("residentHome.html", **context)
#     else:
#         return render_template("index.html")


@app.route('/raiseTaskRequest')
def raiseTaskRequest():
    today = str(date.today())
    context = dict(todays_date=today)
    return render_template("raiseTaskRequest.html", **context)


@app.route('/newTaskRequest', methods=['POST'])
def add_new_TaskRequest():
    residentID = session['id']
    requestID = request.form['requestID']
    description = request.form['description']
    category = request.form['category']
    request_priority = 1
    request_status = 'Pending'

    today = str(date.today())
    raisedon = today
    args = (requestID, description, request_priority, request_status)
    g.conn.execute(
        "INSERT INTO Requests (requestid, request_description, request_priority, request_status) VALUES (%s, %s, %s, "
        "%s)",
        args)
    args = (requestID, category)
    g.conn.execute("INSERT INTO Task_Requests (requestid, category) VALUES (%s, %s)", args)
    args = (residentID, requestID, raisedon)
    g.conn.execute("INSERT INTO Raises (residentid, requestid, raisedon) VALUES (%s, %s, %s)", args)
    return render_template("residentHome.html")


@app.route('/applicants')
def applicants():
    today = str(date.today())
    context = dict(todays_date=today)
    return render_template("applicants.html", **context)


# Example of adding new data to the database
@app.route('/add_new_applicants', methods=['POST'])
def add():
    name = request.form['name']
    citizenship = request.form['citizenship']
    passport_number = request.form['passport_number']
    date_of_birth = request.form['date_of_birth']
    gender = request.form['gender']
    room_preference = request.form['room_preference']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    deptid = random.randint(4000, 4001)
    requested_on = str(date.today())
    processed_on = None
    approval_status = None
    args: Tuple[str, str, str, str, str, str, str, str, str, str, str, Any] = (
        name, citizenship, passport_number, date_of_birth, gender, room_preference, start_date, end_date, processed_on,
        requested_on, approval_status, deptid)
    g.conn.execute('INSERT INTO Applicants_ApprovedBy(name, citizenship, passport_number, date_of_birth, gender, '
                   'room_preference, start_date, end_date, processed_on, requested_on, approval_status, '
                   'deptid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
                   , args)
    args1 = (citizenship, passport_number)
    cursor = g.conn.execute("SELECT * FROM Applicants_ApprovedBy WHERE citizenship=%s AND "
                            "passport_number=%s", args1)
    application_id = []
    for result in cursor:
        application_id.append(result['applicationid'])
    context = dict(application_id=application_id)
    return render_template("application_successful.html", **context)


@app.route('/resident_login_page')
def render_resident_login_page():
    return render_template("resident_login.html")


@app.route('/residentHome', methods=["POST", "GET"])
@nocache
def resident_login():
    session["type"] = "resident"
    if request.method == "POST":
        resident_id = request.form.get("resident_id")
        password = request.form.get("password")
        all_resident_id = g.conn.execute("SELECT residentid FROM Residents")
        resident_id_list = []
        for result in all_resident_id:
            resident_id_list.append(int(result[0]))
        # record the user name
        cursor = g.conn.execute("SELECT passport_number FROM Residents WHERE residentid=%s", resident_id)
        passport_number = []
        for result in cursor:
            passport_number.append(result)
        if len(passport_number) != 0:
            if passport_number[0][0] == password and (int(resident_id) in resident_id_list):
                session["id"] = resident_id
            else:
                error = 'Invalid username or password. Please try again!'
                return render_template('resident_login.html', error=error)
        else:
            error = 'Invalid username or password. Please try again!'
            return render_template('resident_login.html', error=error)
        return redirect("/")
        # redirect to the main page
    elif request.method == "GET":
        return redirect("/")


@app.route('/employee_login_page')
def render_employee_login_page():
    return render_template("employee_login.html")


@app.route('/employeeHome', methods=["POST", "GET"])
def employee_login():
    session["type"] = "employee"
    if request.method == "POST":
        employee_id = request.form.get("employee_id")
        password = request.form.get("password")
        all_employee_id = g.conn.execute("SELECT employeeid FROM Employees")
        employee_id_list = []
        for result in all_employee_id:
            employee_id_list.append(int(result[0]))
        # record the user name
        cursor = g.conn.execute("SELECT ssn FROM Employees WHERE employeeid=%s", employee_id)
        ssn = []
        for result in cursor:
            ssn.append(result)
        if len(ssn) != 0:
            if ssn[0][0] == password and (int(employee_id) in employee_id_list):
                session["id"] = employee_id
            else:
                error = 'Invalid username or password. Please try again!'
                return render_template('employee_login.html', error=error)
        else:
            error = 'Invalid username or password. Please try again!'
            return render_template('employee_login.html', error=error)
        cursor1 = g.conn.execute("SELECT deptid FROM Employees WHERE employeeid=%s", employee_id)
        deptid = []
        for result in cursor1:
            deptid.append(result)
        session["deptid"] = deptid[0]
        return redirect("/")
        # redirect to the main page
    elif request.method == "GET":
        return redirect("/")


@app.route('/logout', methods=["GET"])
def logout():
    session["id"] = None
    return redirect("/")


if __name__ == "__main__":
    import click


    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
    This function handles command line parameters.
    Run the server using:

        python3 server.py

    Show the help text using:

        python3 server.py --help

    """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=True, threaded=threaded)


    run()
