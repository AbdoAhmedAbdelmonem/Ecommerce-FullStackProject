from datetime import datetime
from dbm import sqlite3

import pyodbc
from flask import Flask, request, redirect, url_for, jsonify, render_template

app = Flask(__name__)

DB_CONNECTION_STRING = (
    "Driver={SQL Server};"
    "Server=LEVI;"
    "Database=E_Commerce16;"
    "Trusted_Connection=yes;"
)

FN = LN = ID = PH = EM = BD = AD = None

def get_db_connection():
    return pyodbc.connect(DB_CONNECTION_STRING)

@app.route('/check_login', methods=['POST'])
def check_login():
    global FN, LN, ID, PH, BD, EM ,AD
    user_id = request.form.get('customer_id')
    firstname = request.form.get('firstname')

    user = check_user_in_database(user_id, firstname)

    if user:
        FN, LN, ID, PH, BD, EM ,AD = user
        return redirect(url_for('success'))
    else:
        return render_template('not found.html'), 404


def check_user_in_database(user_id, firstname):
    try:
        connection = pyodbc.connect(DB_CONNECTION_STRING)
        cursor_x = connection.cursor()
        cursor_x.execute(
            "SELECT first_name, last_name, id, phone_number, birth_date, email ,C_address FROM Customers WHERE id = ? AND first_name = ?",
            (user_id, firstname)
        )
        data_x = cursor_x.fetchone()

        cursor_x.close()
        connection.close()

        if data_x:
            return data_x
        else:
            return None
    except Exception as e:
        return None

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit_acc', methods=['POST'])
def submit():
    global FN, LN, ID, PH ,BD,EM,AD

    firstname = request.form['firstname']
    lastname = request.form['lastname']
    customer_id = request.form['customer_id']
    phone = request.form['customer_phone']
    birth_date = request.form['customer_birth_date']
    email = request.form['User_Email']
    address = request.form['User_Address']

    FN = firstname
    LN = lastname
    ID = customer_id
    PH = phone
    BD = birth_date
    EM = email
    AD = address
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Customers (first_name, last_name, id, phone_number, birth_date,email,C_address) VALUES (?,?,?,?,?,?,?)
            ''', (firstname, lastname, customer_id, phone, birth_date, email, address))
            conn.commit()
            # Success popup message
            return redirect(url_for('success'))
    except pyodbc.IntegrityError:
        return render_template('foundAlready.html',firstname=firstname, id=customer_id)
    except Exception as e:
        return f"<script>showPopup('Error: {str(e)}'); window.location='/';</script>"


@app.route('/success')
def success():
    return render_template('SuperMarket.html',firstname=FN,lastname=LN)

@app.route('/submit', methods=['POST'])
def submit_product():
    try:
        data = request.get_json()
        product_name = data['product_name']
        product_id = data['product_id']
        valid_date = data['valid_date']
        price = data['price']
        payment_method = data['payment_method']
        country = data['product_Country']
        quantity = data['quantity']
        total_price = data['total']


        # Connect to SQL Server
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor2 = conn.cursor()
        CR7 = conn.cursor()


        query = """
            INSERT INTO Orders_Details 
            (C_ID, product_id, quantity, product_name, product_price, Total_Spend, product_country) 
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        data = (ID, product_id, quantity, product_name, price, total_price, country)
        cursor.execute(query, data)

        queryC = """ SELECT MAX(order_id) FROM Orders_Details; """
        CR7.execute(queryC)
        order_id = CR7.fetchone()[0]

        query = """
        INSERT INTO Payments (C_ID,order_id,payment_method,payment_date,payment_status)VALUES (?,?,?,?,?)
        """
        cursor2.execute(query, (ID,order_id,payment_method,datetime.now(),"Pending"))
        conn.commit()

        return jsonify({'message': 'Product added to cart successfully!'})

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()



@app.route('/tables')
def table():
    try:
        with get_db_connection() as conn:
            cursor1 = conn.cursor()
            cursor2 = conn.cursor()
            cursor3 = conn.cursor()
            cursor4 = conn.cursor()

            cursor1.execute("SELECT id, first_name, last_name, birth_date,C_address,phone_number FROM Customers")
            data = cursor1.fetchall()  # Retrieve all rows
            cursor2.execute("SELECT id, P_name, price, supplier_id, brand, P_description,Category_ID,Product_Country FROM Products")
            data2 = cursor2.fetchall()
            cursor3.execute("""SELECT 
            Orders_Details.order_id,
            Orders_Details.C_ID,
            Orders_Details.product_id,
            Orders_Details.quantity,
            Orders_Details.product_name,
            Orders_Details.product_price,
            Orders_Details.Total_Spend,
            Orders_Details.product_country,
            Payments.payment_method,
            Payments.payment_date,
            Payments.payment_status,
            Suppliers.first_name,
            Suppliers.id
        FROM 
            Orders_Details
        INNER JOIN 
            Payments ON Orders_Details.order_id = Payments.order_id
                     AND Orders_Details.C_ID = Payments.C_ID
        INNER JOIN 
            Products ON Orders_Details.product_id = Products.id
        INNER JOIN 
            Suppliers ON Products.supplier_id = Suppliers.id;
            """)
            data3 = cursor3.fetchall()
            cursor4.execute("""SELECT id,first_name,last_name,email,phone_number,S_address FROM Suppliers""")
            data4 = cursor4.fetchall()


    except Exception as e:
        return f"Error: {str(e)}"

    return render_template('System Data.html', data=data ,data2=data2 ,data3=data3,data4=data4)


@app.route('/profile')
def customer_profile():
    global FN, LN, ID, PH, BD,EM,AD

    customer={
        'first_name': FN,
        'last_name': LN,
        'customer_id': ID,
        'phone': PH,
        'birth_date': BD,
        'Email': EM,
        'Address': AD
    }
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            Orders_Details.order_id,
            Orders_Details.C_ID,
            Orders_Details.product_id,
            Orders_Details.quantity,
            Orders_Details.product_name,
            Orders_Details.product_price,
            Orders_Details.Total_Spend,
            Orders_Details.product_country,
            Payments.payment_method,
            Payments.payment_date,
            Payments.payment_status,
            Suppliers.first_name
        FROM 
            Orders_Details
        INNER JOIN 
            Payments ON Orders_Details.order_id = Payments.order_id
                     AND Orders_Details.C_ID = Payments.C_ID
        INNER JOIN 
            Products ON Orders_Details.product_id = Products.id
        INNER JOIN 
            Suppliers ON Products.supplier_id = Suppliers.id
        WHERE 
            Orders_Details.C_ID = ?; 
        """
    cursor.execute(query, ID)
    transactions = cursor.fetchall()

    cursor2 = conn.cursor()
    query2 = """SELECT COUNT(*) AS TransCount FROM Orders_Details WHERE C_ID = ?"""
    cursor2.execute(query2, (ID,))
    TransCount = cursor2.fetchone()[0]

    cursor3 = conn.cursor()
    query3 = """SELECT SUM(Total_Spend) AS TotalSpending FROM Orders_Details WHERE C_ID = ?"""
    cursor3.execute(query3, (ID,))
    TotalSpending = cursor3.fetchone()[0]

    return render_template(
        'customer_profile.html',
        customer=customer,
        transactions=transactions,
        TransCount=TransCount or 0,
        TotalSpending=TotalSpending or 0
    )

@app.route('/cancel_transaction', methods=['POST'])
def cancel_transaction():
    data = request.get_json()
    transaction_id = data.get('transaction_id')

    if not transaction_id:
        return jsonify({'success': False, 'error': 'Transaction ID not provided'}), 400

    try:
        connecter = get_db_connection()

        cursordeletingpayment = connecter.cursor()
        query2 = '''DELETE FROM Payments WHERE order_id = ?;'''
        cursordeletingpayment.execute(query2, (transaction_id,))

        cursordeletingtrans = connecter.cursor()
        query = '''DELETE FROM Orders_Details WHERE order_id = ?;'''
        cursordeletingtrans.execute(query, (transaction_id,))

        connecter.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/delete_account', methods=['POST'])
def delete_account():
    data = request.json
    customer_id = data.get('customer_id')

    try:
        connecterx = get_db_connection()
        cursorx_1 = connecterx.cursor()

        cursorx_1.execute('''
            DELETE FROM Orders_Details WHERE C_ID = ?;
        ''', (customer_id,))

        cursorx_1.execute('''
            DELETE FROM Payments WHERE C_ID = ?;
        ''', (customer_id,))

        cursorx_1.execute('''
            DELETE FROM Customers WHERE C_ID = ?;
        ''', (customer_id,))

        connecterx.commit()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

transdata = {}

@app.route('/track_order', methods=['POST'])
def track_order():
    try:
        # Declare transactions as global
        global transdata

        conn = get_db_connection()
        cursor = conn.cursor()

        data = request.get_json()
        order_id = data['order_id']

        if not order_id:
            return jsonify({"success": False, "message": "Order ID is required"}), 400

        query = '''SELECT 
                        c.id AS customer_id,
                        c.C_address AS customer_address,
                        o.order_id,
                        o.Total_Spend,
                        s.first_name AS supplier_first_name,
                        s.last_name AS supplier_last_name,
                        s.S_address AS supplier_address,
                        s.id AS supplier_id
                    FROM 
                        Customers c
                    INNER JOIN 
                        Orders_Details o ON c.id = o.C_ID
                    INNER JOIN 
                        Products p ON o.product_id = p.id
                    INNER JOIN 
                        Suppliers s ON p.supplier_id = s.id
                    WHERE 
                        o.order_id = ?;  -- Use parameterized query
        '''
        cursor.execute(query, (order_id,))
        transactionsdata = cursor.fetchone()  # Use fetchone() since you expect a single result

        if not transactionsdata:
            return jsonify({"success": False, "message": "No transactions found for the provided order ID"}), 404

        # Map the fetched tuple to a dictionary using column names
        columns = [column[0] for column in cursor.description]
        transdata = dict(zip(columns, transactionsdata))

        # Redirect to the track page with the order ID as a query parameter
        return redirect(url_for('track', transactions=transdata))

    except pyodbc.Error as e:
        return jsonify({"success": False, "message": f"Database error occurred: {str(e)}"}), 500

@app.route('/track')
def track():
    global transdata
    # You can fetch the tracking information based on the order_id here if needed
    return render_template('track.html', transaction=transdata)

def edit_profile():
    data = request.json
    customer_id = data.get('customer_id')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone = data.get('phone')

    try:
        connected_api = get_db_connection()
        cursor_api = connected_api.cursor()
        query = '''UPDATE Customers SET first_name = ?, last_name = ?, phone_number = ? WHERE id = ?'''
        cursor_api.execute(query,first_name, last_name, phone, customer_id)
        connected_api.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500





# products = [
#     {"name": "Product 1", "price": 20.00, "quantity": 1},
#     {"name": "Product 2", "price": 30.00, "quantity": 1},
# ]
#
# @app.route('/cart')
# def cart():
#     # Render the cart page with products data
#     return render_template('order.html', products=products)
#
# @app.route('/confirm_order', methods=['POST'])
# def confirm_order():
#     # This would typically handle the backend logic of confirming an order (saving to a database, etc.)
#     # For now, we return a simple response
#     return jsonify({"message": "Order confirmed!", "status": "success"})


if __name__ == '__main__':
    app.run(debug=True)