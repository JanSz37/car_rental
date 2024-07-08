from flask import Flask, render_template, request, make_response, session
import sqlite3
import pandas as pd
from datetime import date,datetime, timedelta

#replace this with the path to your database
path_var = 'C:/Users/yayec/Documents/python_finished/projdb.sqlite'

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'my_key'
conn = sqlite3.connect(path_var) 
print(pd.read_sql_query('SELECT * FROM rented_cars', conn))
conn.close()
import sqlite3
import pandas as pd

#verifying user login 
def user_verification(user):
    conn = sqlite3.connect(path_var)
    query = "SELECT client_id, client_password, client_name FROM clients WHERE client_id = " + str(user[0]) + ''
    user_data = pd.read_sql_query(query, conn)
    user_string = 'Welcome user: ' + user_data.iloc[0, 2]
    if int(user[0]) == int(user_data.iloc[0, 0]) and str(user[1]) == str(user_data.iloc[0, 1]):
        return int(1), user_string
    else:
        return int(0), user_string

#function for checking the id of the added car against the database
def check_cars_id(id):
    conn = sqlite3.connect(path_var)
    query = "SELECT id FROM cars_prices WHERE id = ?"
    c = conn.cursor()
    c.execute(query, (id,))
    ids = c.fetchall()
    conn.close()
    print(ids)
    if ids:
        return int(1)
    else:
        return int(0)

#getting av cars
def get_available_cars():
    try:
        conn = sqlite3.connect(path_var)
        query = "SELECT id, model, price FROM cars_prices WHERE id IN (SELECT id FROM availability WHERE avail = 1)"
        cars_data = pd.read_sql_query(query, conn)
        #cars_data1 = cars_data.to_html()
        return cars_data
    except Exception as e:
        print(f"Error fetching available cars: {e}")
    finally:
        if conn:
            conn.close()

#getting all cars
def get_all_cars():
    try:
        conn = sqlite3.connect(path_var)
        query = "SELECT id, model, price FROM cars_prices"
        cars_data = pd.read_sql_query(query, conn)
        #cars_data1 = cars_data.to_html()
        return cars_data
    except Exception as e:
        print(f"Error fetching available cars: {e}")
    finally:
        if conn:
            conn.close()

#renting a car
def rent_a_car(rental):
    conn = sqlite3.connect(path_var)
    c = conn.cursor()
    #todaysDate = date.today()
    daysBorrowed = (datetime.strptime(rental[2], '%Y-%m-%d').date() - datetime.strptime(rental[1], '%Y-%m-%d').date()).days
    read1 = pd.read_sql_query('SELECT price FROM cars_prices WHERE id =' + str(rental[0]) + '', conn)
    read2 = pd.read_sql_query('SELECT model FROM cars_prices WHERE id =' + str(rental[0]) + '', conn)
    moneyDue = daysBorrowed * int(read1.iloc[0, 0])
    print('You are renting: ' + read2.iloc[0, 0])
    print('Your total will be: ' + str(moneyDue) + ' PLN')
    #rental.append(str(todaysDate))
    rental.insert(3 ,str(moneyDue)) 
    print(rental)
    write1 = '''INSERT INTO rented_cars(id, return_date, borrowed_date, money_due, client_id) VALUES (?, ?, ?, ?, ?)'''
    write2 = '''UPDATE availability SET avail = 0 WHERE id = (?)'''
    conn.execute(write1, rental)
    conn.execute(write2, (rental[0],)) #turns out it has to be a TUPLE object
    conn.commit()
    #check = pd.read_sql_query('SELECT * FROM rented_cars', conn)
    conn.close()
    return(read2.iloc[0,0], moneyDue, daysBorrowed)
    #print(check)

#giving the table of cars rented by the customer
def return_a_car1(returnal_id):
        conn = sqlite3.connect(path_var)
        c = conn.cursor()
        read = pd.read_sql_query('SELECT rented_cars.id, cars_prices.model FROM rented_cars INNER JOIN cars_prices ON rented_cars.id = cars_prices.id WHERE rented_cars.client_id = ' + str(returnal_id) + '', conn)
        customers_cars = read
        return customers_cars

#changing the database upon returnal
def return_a_car2(returnal):
    conn = sqlite3.connect(path_var)
    c = conn.cursor()
    todaysDate = date.today()
    read1 = pd.read_sql_query('SELECT return_date FROM rented_cars WHERE id =' + str(returnal) + '', conn)
    read2 = pd.read_sql_query('SELECT model FROM cars_prices WHERE id =' + str(returnal) + '', conn)
    overDate = (datetime.strptime(read1.iloc[0, 0], '%Y-%m-%d').date() - todaysDate).days
    if overDate > 0:
        message = 'Time of return exceeded. Please contact customer support. Your account will be charged with additional fees.' #these 2 can be made into pages
    else: 
        message = 'Thank you for riding with us.' #and this one
    write1 = '''DELETE FROM rented_cars WHERE id = (?)'''
    write2 = '''UPDATE availability SET avail = 1 WHERE id = (?)'''
    conn.execute(write1, str(returnal[0]))
    conn.execute(write2, str(returnal[0]))
    conn.commit()
    #check = pd.read_sql_query('SELECT * FROM rented_cars', conn)
    conn.close()
    return(message)
    #print(check)
    
#adding a car
def register_car(car):
    conn = sqlite3.connect(path_var)
    c = conn.cursor()
    write = '''INSERT OR IGNORE INTO cars_prices(id, model, price) VALUES (?,?,?)'''
    idCheck = pd.read_sql_query('''SELECT id FROM cars_prices''', conn)
    c.execute(write, car)
    car_avail = [car[0], int(1)]
    c.execute('''INSERT OR IGNORE INTO availability(id, avail) VALUES (?, ?)''', car_avail)
    conn.commit()
    print(pd.read_sql_query('''SELECT * FROM cars_prices''', conn))
    conn.close()

#a function for user login upon rental(rent_car_init.html)
@app.route('/check_user1', methods = ['POST'])
def check_user1():
    textbox_value4 = request.form.get('textbox4')
    textbox_value5 = request.form.get('textbox5')
    list3 = []
    list3.append(textbox_value4)
    list3.append(textbox_value5)
    ver = user_verification(list3)
    print(ver)
    if ver[0] == 1:
        session['ID'] = textbox_value4
        cars= get_available_cars()
        return render_template('cars.html', message = ver[1], cars = cars)
    else:
        return make_response('<h1> Login unsuccessful</h1>')

# Route to rent_car_init - easier than to chage the layout
@app.route('/cars')  
def cars(): 
    return render_template('rent_car_init.html')

# getting the car id from the click and passing to dates processing
@app.route('/rent_car/<int:id>')  
def rent_car(id):  
    return render_template('rent_car.html', entry_id = id)

#dates input and processing
@app.route('/process_dates', methods=['POST'])
def process_dates():
    entry_id = request.form.get('entry_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    customer_id = session.get('ID')
    my_list = []
    my_list.append(str(entry_id))
    my_list.append(str(start_date))
    my_list.append(str(end_date))
    my_list.append(str(customer_id))
    list1 = rent_a_car(my_list)
    if float(list1[1]) < float(0):
        return make_response('<h1> Not today! </h1>')
    else:
        session.pop('ID')
        return render_template('successful.html', list1 = list1)

# if all goes well, this is the rental summary
@app.route('/successful')  
def successful():  
    return render_template('successful.html')

#login system for returning cars - we're doing it the easy way
@app.route('/check_user', methods = ['POST'])
def check_user():
    textbox_value2 = request.form.get('textbox2')
    textbox_value3 = request.form.get('textbox3')
    list2 = []
    list2.append(textbox_value2)
    list2.append(textbox_value3)
    ver = user_verification(list2)
    print(ver)
    table = return_a_car1(textbox_value2)
    if ver[0] == 1:
        return render_template('return_car2.html', table = table, message = ver[1])
    else:
        return make_response('<h1> Login unsuccessful</h1>')
    
# Route to return a rented car
@app.route('/return_car1')  
def return_car1():  
    return render_template('return_car1.html')


@app.route('/return_car3/<id>')  
def return_car3(id):  
    message = return_a_car2(id)
    return render_template('return_car3.html', message = message)


# Route to add cars to the inventory - admin login included
@app.route('/add_cars')  
def add_cars():  
    if request.authorization and request.authorization.username == 'user' and request.authorization.password == 'pass':
        cars1 = pd.DataFrame()
        cars1 = cars1.iloc[0:0]
        cars1 = get_all_cars()
        return render_template('add_cars.html', cars1 = cars1)
    return make_response('<h1> Acccess denied! </h1>', 401, {'WWW-Authenticate': 'Basic realm ="Login required" '})

#processing the added car (textbox)
@app.route('/process_added_cars', methods=['POST'])
def process_added_car():
    car_id = request.form.get('car_id')
    car_name = request.form.get('car_name')
    car_price = request.form.get('car_price')
    my_list = []
    my_list.append(str(car_id))
    my_list.append(str(car_name))
    my_list.append(str(car_price))
    idCheck = check_cars_id(my_list[0])
    if int(idCheck) == int(1):
        return make_response('<h1> Car already in database! </h1>')
    else:
        register_car(my_list)
        cars1 = get_all_cars()
        print(cars1)
        return render_template('add_cars.html', cars1 = cars1)

# Route for the root URL to redirect to the '/cars' route
@app.route('/')
def home():
    return "Welcome! <a href='/cars'>View Available Cars</a>"

if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Change the port number to 5000 or any other available port

