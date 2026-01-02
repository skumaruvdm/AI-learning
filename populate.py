import psycopg2
import random
from faker import Faker
from datetime import datetime, timedelta

def execute_insert_query(cursor, query, params):
    """Executes an INSERT query and returns the new ID."""
    cursor.execute(query, params)
    return cursor.fetchone()[0]

def execute_query(cursor, query, params):
    """Executes a query with no return value."""
    cursor.execute(query, params)

def populate_data():
    """Connects to the PostgreSQL database and populates the tables with synthetic data."""
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
    except psycopg2.OperationalError as e:
        print(f"Could not connect to the database: {e}")
        print("Please ensure the PostgreSQL container is running and the schema is created.")
        return

    conn.autocommit = True
    cur = conn.cursor()
    fake = Faker()

    # Populate Customers
    customers = []
    for _ in range(100):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = fake.unique.email()
        customer_id = execute_insert_query(
            cur,
            "INSERT INTO customers (first_name, last_name, email) VALUES (%s, %s, %s) RETURNING customer_id;",
            (first_name, last_name, email)
        )
        customers.append(customer_id)
    print(f"Populated {len(customers)} customers.")

    # Populate Products
    products = []
    for _ in range(50):
        name = fake.bs().capitalize() + " " + fake.word()
        description = fake.text()
        price = round(random.uniform(10.0, 500.0), 2)
        stock = random.randint(0, 1000)
        cur.execute(
            "INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s) RETURNING product_id, price;",
            (name, description, price, stock)
        )
        products.append(cur.fetchone())
    print(f"Populated {len(products)} products.")

    # Populate Orders and Order Items
    orders = []
    order_items = []
    for _ in range(200):
        customer_id = random.choice(customers)
        order_date = fake.date_between(start_date="-2y", end_date="today")
        status = random.choice(['pending', 'shipped', 'delivered', 'cancelled'])
        order_id = execute_insert_query(
            cur,
            "INSERT INTO orders (customer_id, order_date, status) VALUES (%s, %s, %s) RETURNING order_id;",
            (customer_id, order_date, status)
        )
        orders.append((order_id, status))

        # Add order items for each order
        num_items = random.randint(1, 5)
        total_order_price = 0
        for _ in range(num_items):
            product_info = random.choice(products)
            product_id = product_info[0]
            price = product_info[1]
            quantity = random.randint(1, 10)
            total_order_price += float(price) * quantity
            execute_query(
                cur,
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s);",
                (order_id, product_id, quantity, price)
            )
        # Storing total price to use for invoice
        order_items.append({'order_id': order_id, 'total_price': total_order_price})

    print(f"Populated {len(orders)} orders and their items.")

    # Populate Invoices
    invoices = []
    for order in orders:
        order_id, order_status = order
        if order_status not in ['pending', 'cancelled']:
            invoice_date = fake.date_between(start_date="-1y", end_date="today")
            due_date = invoice_date + timedelta(days=30)
            total_amount_info = next((item for item in order_items if item['order_id'] == order_id), None)
            if total_amount_info:
                total_amount = total_amount_info['total_price']
                status = random.choice(['unpaid', 'paid', 'overdue'])
                cur.execute(
                    "INSERT INTO invoices (order_id, invoice_date, due_date, total_amount, status) VALUES (%s, %s, %s, %s, %s) RETURNING invoice_id, total_amount, status;",
                    (order_id, invoice_date, due_date, total_amount, status)
                )
                invoices.append(cur.fetchone())
    print(f"Populated {len(invoices)} invoices.")

    # Populate Payments
    payments = 0
    for invoice in invoices:
        invoice_id, total_amount, invoice_status = invoice
        if invoice_status == 'paid':
            # Full payment
            payment_date = fake.date_between(start_date="-1y", end_date="today")
            payment_method = random.choice(['Credit Card', 'PayPal', 'Bank Transfer'])
            execute_query(
                cur,
                "INSERT INTO payments (invoice_id, payment_date, amount, payment_method) VALUES (%s, %s, %s, %s);",
                (invoice_id, payment_date, total_amount, payment_method)
            )
            payments += 1
        elif invoice_status == 'unpaid' and random.random() > 0.5:
             # Partial payment
            payment_date = fake.date_between(start_date="-1y", end_date="today")
            amount = round(float(total_amount) * random.uniform(0.1, 0.9), 2)
            payment_method = random.choice(['Credit Card', 'PayPal', 'Bank Transfer'])
            execute_query(
                cur,
                "INSERT INTO payments (invoice_id, payment_date, amount, payment_method) VALUES (%s, %s, %s, %s);",
                (invoice_id, payment_date, amount, payment_method)
            )
            payments += 1


    print(f"Populated {payments} payments.")


    cur.close()
    conn.close()
    print("\nSynthetic data populated successfully.")

if __name__ == "__main__":
    populate_data()