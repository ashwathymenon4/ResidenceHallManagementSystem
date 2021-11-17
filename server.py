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
import datetime
from typing import Any, Tuple
from sqlalchemy import exc
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
    try:
        if session["id"] is not None:
            if session["type"] == "resident":
                return render_template("residentHome.html")
            else:
                if session["deptid"] == 4000:
                    return redirect("/admissions")
                elif session["deptid"] == 4001:
                    return redirect("/finance")
                else:
                    return redirect("/facilities")
        else:
            return render_template("index.html")
    except:
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

@app.route('/getPaymentSummary')
@nocache
def getPaymentSummary():
    try:
        if (session["id"] is None):
            return redirect('/')
        cursor = g.conn.execute('select outstanding_rent, dining_hall_credit  from residents where residentid=%s',
                                session['id'])
        residentCurrentAmount = []
        for row in cursor:
            residentCurrentAmount.append(row)
        cursor = g.conn.execute(
            "select R1.request_description, R2.amount, R3.raisedon from requests R1, Finance_Requests "
            "R2,Raises R3 where R1.requestid=R2.requestid and R1.requestid=R3.requestid and "
            "R3.residentid=%s and (R1.request_description = 'Rent Payment' or "
            "R1.request_description='Dining Fees') and R1.request_status='Approved'", session['id'])
        financeReq = []
        for row in cursor:
            financeReq.append(row)
        context = dict(residentCurrentAmount=residentCurrentAmount, financeReq=financeReq)
        return render_template('paymentSummary.html', **context)
    except:
        return redirect('/errorHandler')


@app.route('/errorHandler')
def errorHandler():
    try:
        return render_template("errorHandler.html")
    except:
        return redirect('/errorHandler')


@app.route('/orderFood')
@nocache
def orderFood():
    try:
        if (session["id"] is None):
            return redirect('/')
        return render_template("orderFood.html")
    except:
        return redirect('/errorHandler')


@app.route('/getItalian')
@nocache
def getItalian():
    try:
        if (session["id"] is None):
            return redirect('/')
        cursor = g.conn.execute('select dining_hall_credit from residents where residentid=%s', session['id'])
        dining_credit = 0
        for row in cursor:
            dining_credit = int(row[0])
        if dining_credit < 15:
            return render_template("noDiningFunds.html")
        item_name = 'Italian Meal'
        bill_amount = 15
        category = 'Vegetarian'
        order_on = str(date.today())
        residentid = session['id']
        args = (item_name, bill_amount, category, order_on, residentid)
        g.conn.execute(
            "INSERT INTO Dining_Hall_Orders(item_name, bill_amount, category, order_on, residentid) VALUES ( %s, %s, %s, %s, %s)",
            args)
        dining_credit = dining_credit - 15
        g.conn.execute(
            "Update Residents SET dining_hall_credit=%s WHERE residentid = %s",
            (dining_credit, session['id']))
        return render_template('yesDiningFunds.html')
    except:
        return redirect('/errorHandler')


@app.route('/getSnacks')
@nocache
def getSnacks():
    try:
        if (session["id"] is None):
            return redirect('/')
        cursor = g.conn.execute('select dining_hall_credit from residents where residentid=%s', session['id'])
        dining_credit = 0
        for row in cursor:
            dining_credit = int(row[0])
        if dining_credit < 9:
            return render_template("noDiningFunds.html")
        item_name = 'Snacks'
        bill_amount = 9
        category = 'Vegetarian'
        order_on = str(date.today())
        residentid = session['id']
        args = (item_name, bill_amount, category, order_on, residentid)
        g.conn.execute(
            "INSERT INTO Dining_Hall_Orders(item_name, bill_amount , category, order_on, residentid ) VALUES ( %s, %s, %s, %s, %s)",
            args)
        dining_credit = dining_credit - 9
        g.conn.execute(
            "Update Residents SET dining_hall_credit=%s WHERE residentid = %s",
            (dining_credit, session['id']))
        return render_template('yesDiningFunds.html')
    except:
        return redirect('/errorHandler')


@app.route('/getIndianMeal')
@nocache
def getIndianMeal():
    try:
        if (session["id"] is None):
            return redirect('/')
        cursor = g.conn.execute('select dining_hall_credit from residents where residentid=%s', session['id'])
        dining_credit = 0
        for row in cursor:
            dining_credit = int(row[0])
        if dining_credit < 15:
            return render_template("noDiningFunds.html")
        item_name = 'Indian Meal'
        bill_amount = 15
        category = 'Vegetarian'
        order_on = str(date.today())
        residentid = session['id']
        args = (item_name, bill_amount, category, order_on, residentid)
        g.conn.execute(
            "INSERT INTO Dining_Hall_Orders(item_name, bill_amount , category, order_on, residentid ) VALUES ( %s, %s, %s, %s, %s)",
            args)
        dining_credit = dining_credit - 15
        g.conn.execute(
            "Update Residents SET dining_hall_credit=%s WHERE residentid = %s",
            (dining_credit, session['id']))
        return render_template('yesDiningFunds.html')
    except:
        return redirect('/errorHandler')


@app.route('/getChicken')
@nocache
def getChicken():
    try:
        if (session["id"] is None):
            return redirect('/')
        cursor = g.conn.execute('select dining_hall_credit from residents where residentid=%s', session['id'])
        dining_credit = 0
        for row in cursor:
            dining_credit = int(row[0])
        if dining_credit < 15:
            return render_template("noDiningFunds.html")
        item_name = 'Chicken Sandwich'
        bill_amount = 15
        category = 'Vegetarian'
        order_on = str(date.today())
        residentid = session['id']
        args = (item_name, bill_amount, category, order_on, residentid)
        g.conn.execute(
            "INSERT INTO Dining_Hall_Orders(item_name, bill_amount , category, order_on, residentid ) VALUES ( %s, %s, %s, %s, %s)",
            args)
        dining_credit = dining_credit - 15
        g.conn.execute(
            "Update Residents SET dining_hall_credit=%s WHERE residentid = %s",
            (dining_credit, session['id']))
        return render_template('yesDiningFunds.html')
    except:
        return redirect('/errorHandler')


@app.route('/raiseFinanceRequest')
@nocache
def raiseFinanceRequest():
    try:
        if (session["id"] is None):
            return redirect('/')
        return render_template("raiseFinanceRequest.html")
    except:
        return redirect('/errorHandler')


@app.route('/newFinanceRequest', methods=['POST'])
@nocache
def add_new_FinanceRequest():
    try:
        if (session["id"] is None):
            return redirect('/')
        residentID = session["id"]
        requestID = 0
        description = request.form['financeCategory']
        request_priority = 1
        amount = 0
        today = str(date.today())
        raisedon = today
        outstanding = 0
        request_status = 'Pending'
        if description == 'Rent Payment':
            print('Room Rent')
            cursor = g.conn.execute('select outstanding_rent from residents where residentid=%s', session['id'])
            for row in cursor:
                outstanding = int(row[0])
            print(outstanding)
            if outstanding == 0:
                request_status = 'Rejected'
            else:
                args = (0, session['id'])
                g.conn.execute('update residents set outstanding_rent=%s where residentid=%s', args)
                request_status = 'Approved'

        if description == 'Rent Payment':
            amount = outstanding

        if description == 'Dining Fees':
            amount = 100
            dining_hall = 0
            cursor = g.conn.execute('select dining_hall_credit from residents where residentid=%s', session['id'])
            for row in cursor:
                dining_hall = row[0]
            dining_hall = amount + dining_hall
            args = (dining_hall, session['id'])
            g.conn.execute('update residents set dining_hall_credit=%s where residentid=%s', args)
            request_status = 'Approved'

        today = str(date.today())
        print(today)
        raisedon = today

        args = (description, request_priority, request_status)
        g.conn.execute(
            "INSERT INTO Requests(request_description, request_priority, request_status) VALUES ( %s, %s, %s)",
            args)
        cursor = g.conn.execute('select requestid from requests order by requestid DESC limit 1')
        for row in cursor:
            requestID = int(row[0])
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

        return redirect("/getFinanceRequest")
    except:
        return redirect('/errorHandler')


@app.route('/raiseTaskRequest')
@nocache
def raiseTaskRequest():
    try:
        if (session["id"] is None):
            return redirect('/')
        return render_template("raiseTaskRequest.html")
    except:
        return redirect('/errorHandler')


@app.route('/newTaskRequest', methods=['POST'])
@nocache
def add_new_TaskRequest():
    try:
        if (session["id"] is None):
            return redirect('/')
        requestID = 0
        residentID = session['id']

        description = request.form['description']
        category = request.form['taskCategory']
        request_priority = 1
        request_status = 'Pending'

        today = str(date.today())
        raisedon = today

        args = (description, request_priority, request_status)
        g.conn.execute(
            "INSERT INTO Requests(request_description, request_priority, request_status) VALUES ( %s, %s, %s)",
            args)
        cursor = g.conn.execute('select requestid from requests order by requestid DESC limit 1')

        for row in cursor:
            requestID = int(row[0])

        args = (requestID, category)
        g.conn.execute("INSERT INTO Task_Requests(requestid,category) VALUES (%s, %s)", args)
        args = (residentID, requestID, raisedon)
        g.conn.execute("INSERT INTO Raises(residentid ,requestid, raisedon ) VALUES (%s, %s, %s)", args)
        deptid = 4002
        cursor = g.conn.execute('select empid from employees where deptid=%s', deptid)
        empid = []
        for row in cursor:
            empid.append(row[0])
        employee_id = random.choice(empid)
        args = (requestID, deptid, employee_id)
        g.conn.execute('INSERT INTO Managed_By(requestid,deptid,empid) VALUES (%s, %s, %s)', args)

        return redirect('/getTaskRequest')
    except:
        return redirect('/errorHandler')


@app.route('/getTaskRequest')
@nocache
def getTaskRequest():
    try:
        if (session["id"] is None):
            return redirect('/')

        cursor = g.conn.execute(
            "SELECT R1.requestid, R1.request_description, R1.request_priority, R1.request_status, R2.raisedon FROM Requests R1, Raises R2 where R1.requestid=R2.requestid and residentid=%s and R1.requestid in (select requestid from task_requests)",
            session["id"])

        requests = []
        for result in cursor:
            print(result)
            requests.append(result)
        context = dict(requests=requests)
        return render_template("getTasksRequests.html", **context)
    except:
        return redirect('/errorHandler')


@app.route('/getFinanceRequest')
@nocache
def getFinanceRequest():
    try:
        if (session["id"] is None):
            return redirect('/')

        cursor = g.conn.execute(
            "SELECT R1.requestid, R1.request_description, R1.request_priority, R1.request_status, R2.raisedon FROM Requests R1, Raises R2 where R1.requestid=R2.requestid and residentid=%s and R1.requestid in (select requestid from finance_requests)",
            session["id"])

        requests = []
        for result in cursor:
            print(result)
            requests.append(result)
        context = dict(requests=requests)
        return render_template("getFinanceRequests.html", **context)
    except:
        return redirect('/errorHandler')


@app.route('/applicants')
def applicants():
    try:
        today = str(date.today())
        context = dict(todays_date=today)
        return render_template("applicants.html", **context)
    except:
        return redirect('/errorHandler')


# Example of adding new data to the database
@app.route('/add_new_applicants', methods=['POST'])
def add():
    try:
        name = request.form['name']
        citizenship = request.form['citizenship']
        passport_number = request.form['passport_number']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        room_preference = request.form['room_preference']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        deptid = 4000
        print(start_date)
        print(end_date)
        print(start_date > end_date)
        requested_on = str(date.today())
        processed_on = None
        args = (
            name, citizenship, passport_number, date_of_birth, gender, room_preference, start_date, end_date,
            processed_on,
            requested_on, deptid
        )
        try:
            g.conn.execute(
                'INSERT INTO Applicants_ApprovedBy(name, citizenship, passport_number, date_of_birth, gender, '
                'room_preference, start_date, end_date, processed_on, requested_on, '
                'deptid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
                , args)
        except:
            today = str(date.today())
            context = dict(todays_date=today)
            error = "Please check your input and remember that end date should be greater than start date."
            return render_template("applicants.html", **context, error=error)
        args1 = (citizenship, passport_number)
        cursor = g.conn.execute("SELECT * FROM Applicants_ApprovedBy WHERE citizenship=%s AND "
                                "passport_number=%s", args1)
        application_id = []
        for result in cursor:
            application_id.append(result['applicationid'])
        context = dict(application_id=application_id)
        return render_template("application_successful.html", **context)
    except:
        return redirect('/errorHandler')


@app.route('/resident_login_page')
def render_resident_login_page():
    return render_template("resident_login.html")


@app.route('/residentHome', methods=["POST", "GET"])
@nocache
def resident_login():
    try:
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
            if cursor.rowcount == 0:
                error = 'Invalid username or password. Please try again!'
                return render_template('resident_login.html', error=error)
            passport_number = []
            for result in cursor:
                passport_number.append(result)
            if passport_number[0][0] == password:
                session["id"] = resident_id
            else:
                error = 'Invalid username or password. Please try again!'
                return render_template('resident_login.html', error=error)
            return redirect("/")
            # redirect to the main page
        elif request.method == "GET":
            return redirect("/")
    except:
        return redirect('/errorHandler')


@app.route('/employee_login_page')
def render_employee_login_page():
    return render_template("employee_login.html")


@app.route('/employeeHome', methods=["POST", "GET"])
def employee_login():
    try:
        session["type"] = "employee"
        if request.method == "POST":
            employee_id = request.form.get("employee_id")
            password = request.form.get("password")
            all_employee_id = g.conn.execute("SELECT empid FROM Employees")
            employee_id_list = []
            for result in all_employee_id:
                employee_id_list.append(int(result[0]))
            # record the user name
            cursor = g.conn.execute("SELECT ssn FROM Employees WHERE empid=%s", employee_id)
            if cursor.rowcount == 0:
                error = 'Invalid username or password. Please try again!'
                return render_template('employee_login.html', error=error)
            ssn = []
            for result in cursor:
                ssn.append(result)
            print(ssn)
            cursor1 = g.conn.execute("SELECT deptid FROM Employees WHERE empid=%s", employee_id)
            deptid = []
            for result in cursor1:
                deptid.append(result)
            session["deptid"] = deptid[0][0]
            if (ssn[0][0] == password) and (deptid[0][0] in [4000, 4001, 4002]):
                session["id"] = employee_id
            else:
                error = 'Invalid username or password. Please try again!'
                return render_template('employee_login.html', error=error)
            cursor1 = g.conn.execute("SELECT deptid FROM Employees WHERE empid=%s", employee_id)
            deptid = []
            for result in cursor1:
                deptid.append(result)
            session["deptid"] = deptid[0][0]
            return redirect("/")
            # redirect to the main page
        elif request.method == "GET":
            return redirect("/")
    except:
        return redirect('/errorHandler')


@app.route('/logout', methods=["GET"])
def logout():
    try:
        session["id"] = None
        return redirect("/")
    except:
        return redirect('/errorHandler')


@app.route('/admissions')
@nocache
def admissions_employee():
    # try:
    if (session["id"] is None):
        return redirect('/')
    status_needed = "Pending"
    cursor = g.conn.execute("SELECT * FROM Applicants_ApprovedBy WHERE approval_status=%s", status_needed)
    pending_applications = []
    for result in cursor:
        pending_applications.append(result)
    cursor_vacant_rooms = g.conn.execute("SELECT r.room_number, COALESCE(r1.to_date, CURRENT_DATE)"
                                         ", r.room_type FROM Rooms r LEFT JOIN Residents r1 ON "
                                         "r.room_number=r1.room_number")
    rooms = []
    for result in cursor_vacant_rooms:
        rooms.append(result)
    context = dict(pending_applications=pending_applications, rooms=rooms)
    return render_template("employeeHome_admissions.html", **context)


# except:
#     return redirect('/errorHandler')


@app.route('/finance')
@nocache
def finance_employee():
    try:
        if (session["id"] is None):
            return redirect('/')
        status_needed = "Pending"
        args = (status_needed, session["id"])
        cursor = g.conn.execute(
            "SELECT r.requestid, r1.residentid, r.request_description, r1.raisedon "
            "FROM requests r "
            "JOIN raises r1 "
            "ON r.requestid=r1.requestid "
            "JOIN finance_requests fr "
            "ON r.requestid=fr.requestid "
            "JOIN managed_by m "
            "ON m.requestid=r.requestid "
            "WHERE r.request_status=%s AND m.empid=%s", args)
        pending_finance_requests = []
        for result in cursor:
            pending_finance_requests.append(result)
        context = dict(pending_finance_requests=pending_finance_requests)
        return render_template("employeeHome_finance.html", **context)
    except:
        return redirect('/errorHandler')


@app.route('/facilities')
@nocache
def facilities_employee():
    try:
        if (session["id"] is None):
            return redirect('/')

        status_not_wanted = "Complete"
        args = (status_not_wanted, session["id"])

        cursor = g.conn.execute(
            "SELECT r.requestid, r1.residentid, r.request_description, r.request_priority, r.request_status, tr.category, "
            "r1.raisedon FROM requests r "
            "JOIN raises r1 "
            "ON r.requestid=r1.requestid "
            "JOIN task_requests tr "
            "ON r.requestid=tr.requestid "
            "JOIN managed_by m "
            "ON m.requestid=r.requestid "
            "WHERE r.request_status <> %s AND m.empid=%s", args)
        task_requests = []
        for result in cursor:
            task_requests.append(result)
        context = dict(task_requests=task_requests)
        return render_template("employeeHome_facilities.html", **context)
    except:
        return redirect('/errorHandler')


@app.route('/admissions/approved', methods=["POST"])
@nocache
def admission_approved():
    try:
        if (session["id"] is None):
            return redirect('/')
        application_id = request.form.get("application_id")
        room_number = request.form.get("room_number")
        new_status = 'Approved'
        old_status = 'Pending'
        all_application_id = g.conn.execute("SELECT applicationid FROM Applicants_ApprovedBy WHERE approval_status=%s",
                                            old_status)
        all_room_number = g.conn.execute("SELECT r.room_number, COALESCE(r1.to_date, CURRENT_DATE)"
                                         ", r.room_type FROM Rooms r LEFT JOIN Residents r1 ON "
                                         "r.room_number=r1.room_number WHERE (r1.to_date<=CURRENT_DATE OR "
                                         "r1.to_date IS NULL)")
        application_id_list = []
        room_number_list = []
        for result in all_application_id:
            application_id_list.append(int(result[0]))
        for result in all_room_number:
            room_number_list.append(int(result[0]))
        cursor = g.conn.execute("SELECT * FROM Applicants_ApprovedBy WHERE approval_status=%s", old_status)
        pending_applications = []
        for result in cursor:
            pending_applications.append(result)
        cursor_vacant_rooms = g.conn.execute("SELECT r.room_number, COALESCE(r1.to_date, CURRENT_DATE)"
                                             ", r.room_type FROM Rooms r LEFT JOIN Residents r1 ON "
                                             "r.room_number=r1.room_number")
        rooms = []
        for result in cursor_vacant_rooms:
            rooms.append(result)
        context = dict(pending_applications=pending_applications, rooms=rooms)
        print(application_id)
        print(application_id_list)
        if (int(application_id) not in application_id_list) or (int(room_number) not in room_number_list):
            error = "Please verify the details you have entered and check that the room is vacant as of the today"
            return render_template("employeeHome_admissions.html", **context, error=error)
        date_vacant_of_entered_room = g.conn.execute("SELECT COALESCE(r1.to_date, CURRENT_DATE) "
                                                     "FROM Rooms r LEFT JOIN Residents r1 ON "
                                                     "r.room_number=r1.room_number WHERE r.room_number=%s", room_number)
        from_date_of_application_id = g.conn.execute("SELECT start_date FROM Applicants_ApprovedBy "
                                                     "WHERE applicationid=%s", application_id)
        date_room_vacant = ''
        from_date_applicant = ''
        for result in date_vacant_of_entered_room:
            print(result)
            date_room_vacant = result[0].strftime("%Y-%m-%d")
        for result in from_date_of_application_id:
            print(result)
            from_date_applicant = result[0].strftime("%Y-%m-%d")
        print(date_room_vacant)
        print(from_date_applicant)
        print(date_room_vacant > from_date_applicant)
        if date_room_vacant > from_date_applicant:
            error = "Please verify the details you have entered and check that the room in vacant currently " \
                    "moves in"
            return render_template("employeeHome_admissions.html", **context, error=error)
        g.conn.execute("UPDATE Applicants_ApprovedBy SET approval_status=%s, processed_on=CURRENT_DATE "
                       "WHERE applicationid=%s", (new_status, application_id))
        cursor = g.conn.execute("SELECT applicationid, name, citizenship, passport_number, date_of_birth, gender, "
                                "start_date, end_date FROM Applicants_ApprovedBy WHERE applicationid=%s",
                                application_id)
        fields = []
        for result in cursor:
            fields.append(result)

        room_rent_cursor = g.conn.execute("SELECT room_cost FROM rooms WHERE room_number=%s", room_number)
        room_rent = []
        for result in room_rent_cursor:
            room_rent.append(result)

        outstanding_rent = int(room_rent[0][0])

        args = (
            fields[0][0], fields[0][1], fields[0][2], fields[0][3], fields[0][4], fields[0][5], 500, fields[0][6],
            fields[0][7], room_number, outstanding_rent)
        g.conn.execute("INSERT INTO Residents (residentid, name, citizenship, passport_number, date_of_birth, gender, "
                       "dining_hall_credit, from_date, to_date, room_number, outstanding_rent) VALUES (%s, %s, %s, %s, "
                       "%s, %s, %s, %s, %s, %s, %s)", args)
        return redirect("/admissions")
    except:
        return redirect('/errorHandler')


@app.route('/admissions/rejected', methods=['POST'])
@nocache
def admission_rejected():
    try:
        if (session["id"] is None):
            return redirect('/')
        application_id = request.form.get("application_id")
        old_status = "Pending"
        all_application_id = g.conn.execute("SELECT applicationid FROM Applicants_ApprovedBy WHERE approval_status=%s",
                                            old_status)
        new_status = "Rejected"
        application_id_list = []
        cursor = g.conn.execute("SELECT * FROM Applicants_ApprovedBy WHERE approval_status=%s", old_status)
        pending_applications = []
        for result in cursor:
            pending_applications.append(result)
        cursor_vacant_rooms = g.conn.execute("SELECT r.room_number, COALESCE(r1.to_date, CURRENT_DATE), r.room_type "
                                             "FROM Rooms r LEFT JOIN Residents r1 ON "
                                             "r.room_number=r1.room_number")
        rooms = []
        for result in cursor_vacant_rooms:
            rooms.append(result)
        context = dict(pending_applications=pending_applications, rooms=rooms)
        for result in all_application_id:
            application_id_list.append(int(result[0]))
        print(application_id)
        print(application_id_list)
        if int(application_id) not in application_id_list:
            error1 = "Please verify the details you have entered"
            return render_template("employeeHome_admissions.html", **context, error1=error1)
        g.conn.execute("UPDATE Applicants_ApprovedBy SET approval_status=%s, processed_on=CURRENT_DATE "
                       "WHERE applicationid=%s", (new_status, application_id))
        return redirect("/admissions")
    except:
        return redirect('/errorHandler')


@app.route("/finance/approved", methods=["POST"])
@nocache
def finance_approved():
    try:
        if (session["id"] is None):
            return redirect('/')
        request_id = request.form.get("request_id")
        amount = request.form.get("amount")
        new_status = "Approved"
        result = g.conn.execute("UPDATE Requests SET request_status=%s WHERE requestid=%s", (new_status, request_id))
        result = g.conn.execute("UPDATE Finance_Requests SET amount=%s WHERE requestid=%s", (amount, request_id))
        if result.rowcount == 0:
            status_needed = "Pending"
            args = (status_needed, session["id"])
            cursor = g.conn.execute(
                "SELECT r.requestid, r1.residentid, r.request_description, r1.raisedon "
                "FROM requests r "
                "JOIN raises r1 "
                "ON r.requestid=r1.requestid "
                "JOIN finance_requests fr "
                "ON r.requestid=fr.requestid "
                "JOIN managed_by m "
                "ON m.requestid=r.requestid "
                "WHERE r.request_status=%s AND m.empid=%s", args)
            pending_finance_requests = []
            for result in cursor:
                pending_finance_requests.append(result)
            context = dict(pending_finance_requests=pending_finance_requests)
            error = "Please check the Request ID"
            return render_template("employeeHome_finance.html", **context, error=error)
        else:
            return redirect("/finance")
    except:
        return redirect('/errorHandler')


@app.route('/finance/rejected', methods=["POST"])
@nocache
def finance_rejected():
    try:
        if (session["id"] is None):
            return redirect('/')
        request_id = request.form.get("request_id")
        new_status = "Rejected"
        result = g.conn.execute("UPDATE Requests SET request_status=%s WHERE requestid=%s", (new_status, request_id))
        if result.rowcount != 0:
            return redirect("/finance")
        else:
            status_needed = "Pending"
            args = (status_needed, session["id"])
            cursor = g.conn.execute(
                "SELECT r.requestid, r1.residentid, r.request_description, r1.raisedon "
                "FROM requests r "
                "JOIN raises r1 "
                "ON r.requestid=r1.requestid "
                "JOIN finance_requests fr "
                "ON r.requestid=fr.requestid "
                "JOIN managed_by m "
                "ON m.requestid=r.requestid "
                "WHERE r.request_status=%s AND m.empid=%s", args)
            pending_finance_requests = []
            for result in cursor:
                pending_finance_requests.append(result)
            context = dict(pending_finance_requests=pending_finance_requests)
            error1 = "Please check the Request ID"
            return render_template("employeeHome_finance.html", **context, error1=error1)
    except:
        return redirect('/errorHandler')


@app.route('/facilities/status_update', methods=["POST"])
@nocache
def facilities_status_update():
    try:
        if (session["id"] is None):
            return redirect('/')
        request_id = request.form.get("request_id")
        new_status = request.form.get("current_status")
        result = g.conn.execute("UPDATE Requests SET request_status=%s WHERE requestid=%s", (new_status, request_id))
        if result.rowcount == 0:
            status_not_wanted = "Complete"
            args = (status_not_wanted, session["id"])
            cursor = g.conn.execute(
                "SELECT r.requestid, r1.residentid, r.request_description, r.request_priority, r.request_status, "
                "tr.category, r1.raisedon FROM requests r "
                "JOIN raises r1 "
                "ON r.requestid=r1.requestid "
                "JOIN task_requests tr "
                "ON r.requestid=tr.requestid "
                "JOIN managed_by m "
                "ON m.requestid=r.requestid "
                "WHERE r.request_status <> %s AND m.empid=%s", args)
            task_requests = []
            for result in cursor:
                task_requests.append(result)
            context = dict(task_requests=task_requests)
            error = "Please check the Request ID"
            return render_template("employeeHome_facilities.html", **context, error=error)
        else:
            return redirect("/facilities")
    except:
        return redirect('/errorHandler')


@app.route('/facilities/priority_update', methods=["POST"])
@nocache
def facilities_priority_update():
    try:
        if (session["id"] is None):
            return redirect('/')
        request_id = request.form.get("request_id")
        new_priority = request.form.get("current_priority")
        result = g.conn.execute("UPDATE Requests SET request_priority=%s WHERE requestid=%s",
                                (new_priority, request_id))
        if result.rowcount == 0:
            status_not_wanted = "Complete"
            args = (status_not_wanted, session["id"])
            cursor = g.conn.execute(
                "SELECT r.requestid, r1.residentid, r.request_description, r.request_priority, r.request_status, "
                "tr.category, r1.raisedon FROM requests r "
                "JOIN raises r1 "
                "ON r.requestid=r1.requestid "
                "JOIN task_requests tr "
                "ON r.requestid=tr.requestid "
                "JOIN managed_by m "
                "ON m.requestid=r.requestid "
                "WHERE r.request_status <> %s AND m.empid=%s", args)
            task_requests = []
            for result in cursor:
                task_requests.append(result)
            context = dict(task_requests=task_requests)
            error1 = "Please check the Request ID"
            return render_template("employeeHome_facilities.html", **context, error1=error1)
        else:
            return redirect("/facilities")
    except:
        return redirect('/errorHandler')


@app.route('/employeeDetails')
def employeeDetails():
    try:
        cursor = g.conn.execute("SELECT * FROM Employees E JOIN Departments D ON E.deptid=D.deptid WHERE E.empid=%s",
                                session["id"])
        data = []
        for result in cursor:
            data.append(result)
        context = dict(data=data)
        if session["deptid"] == 4000:
            return render_template('employeeDetails_admission.html', **context)
        elif session["deptid"] == 4001:
            return render_template('employeeDetails_finance.html', **context)
        else:
            return render_template('employeeDetails_facilities.html', **context)
    except:
        return redirect('/errorHandler')


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
        app.run(host=HOST, port=PORT, debug=False, threaded=threaded)


    run()
