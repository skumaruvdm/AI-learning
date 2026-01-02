import psycopg2
from psycopg2 import sql

def create_schema():
    """Connects to the PostgreSQL database and creates the 'order to cash' schema."""
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
        print("Please ensure the PostgreSQL container is running.")
        return

    conn.autocommit = True
    cur = conn.cursor()

    # Drop existing tables to start fresh
    cur.execute("""
        DROP TABLE IF EXISTS payments;
        DROP TABLE IF EXISTS invoices;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
    """)


    # Create Customers table
    cur.execute("""
        CREATE TABLE customers (
            customer_id SERIAL PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Table 'customers' created.")

    # Create Products table
    cur.execute("""
        CREATE TABLE products (
            product_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price NUMERIC(10, 2) NOT NULL,
            stock INTEGER NOT NULL
        );
    """)
    print("Table 'products' created.")

    # Create Orders table
    cur.execute("""
        CREATE TABLE orders (
            order_id SERIAL PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(customer_id),
            order_date DATE NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Table 'orders' created.")

    # Create Order Items table
    cur.execute("""
        CREATE TABLE order_items (
            order_item_id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(order_id),
            product_id INTEGER REFERENCES products(product_id),
            quantity INTEGER NOT NULL,
            price NUMERIC(10, 2) NOT NULL
        );
    """)
    print("Table 'order_items' created.")

    # Create Invoices table
    cur.execute("""
        CREATE TABLE invoices (
            invoice_id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(order_id),
            invoice_date DATE NOT NULL,
            due_date DATE NOT NULL,
            total_amount NUMERIC(10, 2) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'unpaid'
        );
    """)
    print("Table 'invoices' created.")

    # Create Payments table
    cur.execute("""
        CREATE TABLE payments (
            payment_id SERIAL PRIMARY KEY,
            invoice_id INTEGER REFERENCES invoices(invoice_id),
            payment_date DATE NOT NULL,
            amount NUMERIC(10, 2) NOT NULL,
            payment_method VARCHAR(50)
        );
    """)
    print("Table 'payments' created.")


    cur.close()
    conn.close()
    print("\nSchema for 'order to cash' application created successfully.")

if __name__ == "__main__":
    create_schema()
