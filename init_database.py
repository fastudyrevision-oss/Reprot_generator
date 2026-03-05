"""
Database initialization script
Creates database, tables, and inserts sample data
"""
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import random

# Database configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  # Update with your MySQL password if needed
    'database': 'gemini_reports'
}

def create_database_and_tables():
    """Create database and tables"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host=DATABASE_CONFIG['host'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password']
        )
        
        cursor = connection.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_CONFIG['database']}")
        print(f"✓ Database '{DATABASE_CONFIG['database']}' created/verified")
        
        # Select the database
        cursor.execute(f"USE {DATABASE_CONFIG['database']}")
        
        # Create tables
        
        # Customers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            phone VARCHAR(20),
            country VARCHAR(50),
            registration_date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'active'
        )
        """)
        print("✓ Customers table created")
        
        # Products table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            price DECIMAL(10, 2) NOT NULL,
            stock_quantity INT DEFAULT 0,
            created_date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'active'
        )
        """)
        print("✓ Products table created")
        
        # Sales table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INT PRIMARY KEY AUTO_INCREMENT,
            customer_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            total_amount DECIMAL(12, 2) NOT NULL,
            sale_date DATE NOT NULL,
            payment_status VARCHAR(20) DEFAULT 'completed',
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
        """)
        print("✓ Sales table created")
        
        # Inventory table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_logs (
            log_id INT PRIMARY KEY AUTO_INCREMENT,
            product_id INT NOT NULL,
            quantity_change INT NOT NULL,
            transaction_type VARCHAR(50),
            log_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
        """)
        print("✓ Inventory logs table created")
        
        # Reviews table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INT PRIMARY KEY AUTO_INCREMENT,
            customer_id INT NOT NULL,
            product_id INT NOT NULL,
            rating INT CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            review_date DATE NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
        """)
        print("✓ Reviews table created")
        
        connection.commit()
        cursor.close()
        connection.close()
        print("\n✓ Database and tables created successfully!")
        
        return True
        
    except Error as err:
        print(f"✗ Error: {err}")
        return False

def insert_sample_data():
    """Insert sample data into tables"""
    try:
        connection = mysql.connector.connect(
            host=DATABASE_CONFIG['host'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            database=DATABASE_CONFIG['database']
        )
        
        cursor = connection.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM reviews")
        cursor.execute("DELETE FROM inventory_logs")
        cursor.execute("DELETE FROM sales")
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM customers")
        
        # Insert customers
        customers_data = [
            ('John Smith', 'john@example.com', '+1234567890', 'USA', '2024-01-15', 'active'),
            ('Sarah Johnson', 'sarah@example.com', '+1234567891', 'USA', '2024-01-20', 'active'),
            ('Maria Garcia', 'maria@example.com', '+1234567892', 'Spain', '2024-02-10', 'active'),
            ('Ahmed Hassan', 'ahmed@example.com', '+1234567893', 'Egypt', '2024-02-15', 'active'),
            ('Lisa Chen', 'lisa@example.com', '+1234567894', 'China', '2024-03-01', 'active'),
            ('Michael Brown', 'michael@example.com', '+1234567895', 'USA', '2024-03-05', 'inactive'),
            ('Emma Wilson', 'emma@example.com', '+1234567896', 'UK', '2024-03-10', 'active'),
            ('Carlos Rodriguez', 'carlos@example.com', '+1234567897', 'Mexico', '2024-03-15', 'active'),
            ('Yuki Tanaka', 'yuki@example.com', '+1234567898', 'Japan', '2024-03-20', 'active'),
            ('Sophia Russo', 'sophia@example.com', '+1234567899', 'Italy', '2024-03-25', 'active'),
        ]
        
        cursor.executemany(
            "INSERT INTO customers (name, email, phone, country, registration_date, status) VALUES (%s, %s, %s, %s, %s, %s)",
            customers_data
        )
        print(f"✓ Inserted {len(customers_data)} customers")
        
        # Insert products
        products_data = [
            ('Laptop Pro', 'Electronics', 1299.99, 25, '2024-01-01', 'active'),
            ('Wireless Mouse', 'Electronics', 29.99, 150, '2024-01-05', 'active'),
            ('USB-C Cable', 'Accessories', 12.99, 300, '2024-01-10', 'active'),
            ('Monitor 4K', 'Electronics', 499.99, 40, '2024-01-15', 'active'),
            ('Mechanical Keyboard', 'Electronics', 149.99, 80, '2024-02-01', 'active'),
            ('Laptop Stand', 'Accessories', 49.99, 120, '2024-02-05', 'active'),
            ('External SSD', 'Storage', 179.99, 60, '2024-02-10', 'active'),
            ('USB Hub', 'Accessories', 34.99, 200, '2024-02-15', 'active'),
            ('Screen Protector', 'Accessories', 9.99, 500, '2024-02-20', 'active'),
            ('Phone Mount', 'Accessories', 19.99, 250, '2024-03-01', 'active'),
        ]
        
        cursor.executemany(
            "INSERT INTO products (name, category, price, stock_quantity, created_date, status) VALUES (%s, %s, %s, %s, %s, %s)",
            products_data
        )
        print(f"✓ Inserted {len(products_data)} products")
        
        # Insert sales
        sales_data = []
        base_date = datetime(2024, 1, 1)
        
        for i in range(100):
            customer_id = random.randint(1, 10)
            product_id = random.randint(1, 10)
            quantity = random.randint(1, 5)
            unit_price = [1299.99, 29.99, 12.99, 499.99, 149.99, 49.99, 179.99, 34.99, 9.99, 19.99][product_id - 1]
            total_amount = quantity * unit_price
            sale_date = (base_date + timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
            payment_status = random.choice(['completed', 'pending', 'refunded'])
            
            sales_data.append((customer_id, product_id, quantity, unit_price, total_amount, sale_date, payment_status))
        
        cursor.executemany(
            "INSERT INTO sales (customer_id, product_id, quantity, unit_price, total_amount, sale_date, payment_status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            sales_data
        )
        print(f"✓ Inserted {len(sales_data)} sales records")
        
        # Insert inventory logs
        inventory_logs_data = []
        for sale in sales_data[:50]:
            product_id = sale[1]
            quantity_change = -sale[2]
            inventory_logs_data.append((product_id, quantity_change, 'Sale', datetime.now()))
        
        cursor.executemany(
            "INSERT INTO inventory_logs (product_id, quantity_change, transaction_type, log_date) VALUES (%s, %s, %s, %s)",
            inventory_logs_data
        )
        print(f"✓ Inserted {len(inventory_logs_data)} inventory logs")
        
        # Insert reviews
        reviews_data = []
        for i in range(30):
            customer_id = random.randint(1, 10)
            product_id = random.randint(1, 10)
            rating = random.randint(3, 5)
            review_texts = [
                'Great product, highly recommend!',
                'Good quality and fast delivery',
                'Excellent value for money',
                'Works as expected',
                'Very satisfied with the purchase',
                'Amazing quality!',
                'Good but could be better',
                'Worth the price',
                'Highly satisfied',
                'Best purchase ever'
            ]
            review_text = random.choice(review_texts)
            review_date = (base_date + timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
            
            reviews_data.append((customer_id, product_id, rating, review_text, review_date))
        
        cursor.executemany(
            "INSERT INTO reviews (customer_id, product_id, rating, review_text, review_date) VALUES (%s, %s, %s, %s, %s)",
            reviews_data
        )
        print(f"✓ Inserted {len(reviews_data)} reviews")
        
        connection.commit()
        cursor.close()
        connection.close()
        print("\n✓ Sample data inserted successfully!")
        
        return True
        
    except Error as err:
        print(f"✗ Error: {err}")
        return False

def verify_database():
    """Verify database and show sample data"""
    try:
        connection = mysql.connector.connect(
            host=DATABASE_CONFIG['host'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            database=DATABASE_CONFIG['database']
        )
        
        cursor = connection.cursor()
        
        tables = ['customers', 'products', 'sales', 'inventory_logs', 'reviews']
        
        print("\n" + "="*60)
        print("DATABASE VERIFICATION")
        print("="*60)
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✓ {table.capitalize()}: {count} records")
        
        print("\n" + "-"*60)
        print("SAMPLE DATA")
        print("-"*60)
        
        # Show sample customers
        cursor.execute("SELECT customer_id, name, country, status FROM customers LIMIT 3")
        print("\nCustomers (sample):")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]}) - {row[3]}")
        
        # Show sample products
        cursor.execute("SELECT product_id, name, category, price FROM products LIMIT 3")
        print("\nProducts (sample):")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]}) - ${row[3]}")
        
        # Show sales stats
        cursor.execute("SELECT SUM(total_amount), AVG(total_amount), COUNT(*) FROM sales")
        result = cursor.fetchone()
        if result[0]:
            print(f"\nSales Statistics:")
            print(f"  - Total Revenue: ${result[0]:,.2f}")
            print(f"  - Average Sale: ${result[1]:.2f}")
            print(f"  - Total Transactions: {result[2]}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as err:
        print(f"✗ Error verifying database: {err}")
        return False

if __name__ == '__main__':
    print("Initializing Gemini Reports Database...\n")
    
    if create_database_and_tables():
        if insert_sample_data():
            verify_database()
            print("\n" + "="*60)
            print("✓ DATABASE INITIALIZATION COMPLETE!")
            print("="*60)
            print("\nYou can now use the application to query the database.")
        else:
            print("\n✗ Failed to insert sample data")
    else:
        print("\n✗ Failed to create database and tables")
