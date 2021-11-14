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

from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from datetime import date


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

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
    return render_template("index.html")


#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#

@app.route('/residentHome')
def residents():
    today = str(date.today())
    context = dict(todays_date=today)
    return render_template("residentHome.html", **context)

@app.route('/raiseFinanceRequest')
def raiseFinanceRequest():
    return render_template("raiseFinanceRequest.html")

@app.route('/newFinanceRequest', methods=['POST'])
def add_new_FinanceRequest():
    residentID = request.form['residentID']
    requestID = request.form['requestID']
    description = request.form['financeCategory']

    request_priority = 1
    request_status = 'Pending'
    amount = request.form['amount']

    today = str(date.today())
    print(today)
    raisedon = today
    args = (requestID, description, request_priority, request_status)
    g.conn.execute(
        "INSERT INTO Requests(requestid,request_description, request_priority, request_status) VALUES (%s, %s, %s, %s)",
        args)
    args = (requestID, amount)
    g.conn.execute("INSERT INTO Finance_Requests(requestid,amount) VALUES (%s, %s)", args)
    args = (residentID, requestID, raisedon)
    g.conn.execute("INSERT INTO Raises(residentid ,requestid, raisedon ) VALUES (%s, %s, %s)", args)
    deptid = 4001
    cursor = g.conn.execute('select empid from employees where deptid=%s', deptid)
    empid = []
    for row in cursor:
        empid.append(row[0])
    employee_id = random.choice(empid)
    args = (requestID, deptid, employee_id)
    g.conn.execute('INSERT INTO Managed_By(requestid,deptid,empid) VALUES (%s, %s, %s)', args)

    return render_template("index.html")


@app.route('/raiseTaskRequest')
def raiseTaskRequest():
    today = str(date.today())
    context = dict(todays_date=today)
    return render_template("raiseTaskRequest.html", **context)



@app.route('/newTaskRequest', methods=['POST'])
def add_new_TaskRequest():
    residentID = request.form['residentID']
    requestID = request.form['requestID']
    description = request.form['description']
    category = request.form['category']
    request_priority = 1
    request_status = 'Pending'

    today = str(date.today())
    print(today)
    raisedon = today
    args = (requestID ,description , request_priority, request_status)
    g.conn.execute("INSERT INTO Requests(requestid,request_description, request_priority, request_status) VALUES (%s, %s, %s, %s)",args)
    args = (requestID, category)
    g.conn.execute("INSERT INTO Task_Requests(requestid,category) VALUES (%s, %s)", args)
    args=(residentID,requestID,raisedon)
    g.conn.execute("INSERT INTO Raises(residentid ,requestid, raisedon ) VALUES (%s, %s, %s)", args)
    deptid = 4002
    cursor = g.conn.execute('select empid from employees where deptid=%s',deptid)
    empid = []
    for row in cursor:
        empid.append(row[0])
    employee_id = random.choice(empid)
    args = (requestID, deptid,employee_id)
    g.conn.execute('INSERT INTO Managed_By(requestid,deptid,empid) VALUES (%s, %s, %s)',args)

    return render_template("index.html")

@app.route('/getTaskRequest')
def getTaskRequest():
    cursor = g.conn.execute("SELECT R1.requestid, R1.request_description, R1.request_priority, R1.request_status FROM Requests R1, Raises R2 where R1.requestid=R2.requestid and residentid=%s and R1.requestid in (select requestid from task_requests)",'1002')
    requests = []
    for result in cursor:
        print(result)
        requests.append(result)
    context = dict(requests=requests)
    return render_template("getTasksRequests.html", **context)

@app.route('/getFinanceRequest')
def getFinanceRequest():
    cursor = g.conn.execute("SELECT R1.requestid, R1.request_description, R1.request_priority, R1.request_status FROM Requests R1, Raises R2 where R1.requestid=R2.requestid and residentid=%s and R1.requestid in (select requestid from finance_requests)",'1002')
    requests = []
    for result in cursor:
        print(result)
        requests.append(result)
    context = dict(requests=requests)
    return render_template("getFinanceRequests.html", **context)



@app.route('/applicants')
def applicants():
    today = str(date.today())
    print(today)
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
    args: Tuple[str, str, str, str, str, str, str, str, str, str, str, Any] = (name, citizenship, passport_number, date_of_birth, gender, room_preference, start_date, end_date, processed_on, requested_on, approval_status, deptid)
    print(args)
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


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


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
