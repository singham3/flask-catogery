from flask import Flask, jsonify, request, Response
import pymysql
from datetime import datetime
from flask_paginate import Pagination, get_page_args

app = Flask(__name__)
conn = pymysql.connect(host="localhost", user="root", password="root", db="category", port=3306)
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS category
                 (id  INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                 parent_id  INT DEFAULT NULL,
                 category_name   CHAR(50) NOT NULL,
                 created_at       DATE,
                 updated_at         DATE);''')
cur.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                 category_id     INT,
                 product_name   CHAR(50) NOT NULL,
                 product_price   INT NOT NULL,
                 created_at       DATE,
                 updated_at         DATE);''')
conn.commit()


@app.route('/category/', methods=['GET', 'POST'])
def category():
    if request.method == 'POST':
        parent_id = request.form.get('parent_id') if request.form.get('parent_id') else 0
        category_name = request.form.get('category_name')

        cur.execute('INSERT INTO category (parent_id, category_name, created_at, updated_at) VALUES (%s,%s,%s,%s)',
                    (parent_id, category_name, str(datetime.now()), str(datetime.now())))
        conn.commit()

    def total_items(parent, price_list, item_list, c=0):
        cur.execute(f'''SELECT id,category_name,parent_id FROM category 
                                        WHERE parent_id = '{parent}' ORDER BY id ASC''')
        parent_data = cur.fetchall()
        if parent_data or c:
            for row in parent_data:
                cur.execute(f'''select prod.product_price from category.products as prod
                                inner join category.category as cat on
                                cat.id = prod.category_id
                                where prod.category_id={row[0]};''')
                products_data = cur.fetchall()
                item_list.append(len(products_data))
                product_price = 0
                for price in products_data:
                    product_price += price[0]
                price_list.append(product_price)
                c += 1
                total_items(row[0], price_list, item_list, c)
        else:
            cur.execute(f'''select prod.product_price from category.products as prod
                                            inner join category.category as cat on
                                            cat.id = prod.category_id
                                            where prod.category_id={parent};''')
            products_data = cur.fetchall()
            item_list.append(len(products_data))
            product_price = 0
            for price in products_data:
                product_price += price[0]
            price_list.append(product_price)
        return sum(item_list), sum(price_list)

    def fetch_category_tree(user_tree_array, parent=0, spacing=''):

        cur.execute(f'''SELECT id,category_name,parent_id FROM category 
                                WHERE parent_id = '{parent}' ORDER BY id ASC''')
        query = cur.fetchall()
        for row in query:
            total_products_item, total_product_price = total_items(row[0], [], [])
            user_tree_array.append({'id': row[0], 'name': spacing + str(row[1]), 'parent': parent,
                                    'total_products_item': total_products_item,
                                    'total_product_price': total_product_price})

            user_tree_array = fetch_category_tree(user_tree_array, row[0], spacing+'  ')
        return user_tree_array
    d = fetch_category_tree([])
    return jsonify({'msg': d})


@app.route('/product/', methods=['GET', 'POST'])
def products():
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        product_name = request.form.get('product_name')
        product_price = request.form.get('product_price')
        cur.execute('INSERT INTO products (category_id, product_name, product_price, created_at, updated_at) VALUES '
                    '(%s,%s,%s,%s,%s)', (category_id, product_name, product_price, str(datetime.now()),
                                         str(datetime.now())))
        conn.commit()
        cur.execute('SELECT * FROM products')
        d = cur.fetchall()
        return jsonify({'f': d})


@app.route('/filter/category/total-count/', methods=['GET', 'POST'])
def filter_category_total_count():
    category_list = tuple(request.args.get('list').split(','))
    cur.execute(f'''select prod.id, prod.product_name, cat.category_name, prod.product_price
                        from category.products as prod
                        inner join category.category as cat
                        on cat.id = prod.category_id
                        where cat.id in {category_list};''')
    data = cur.fetchall()
    return jsonify({'msg': f'total number of filtered products is {len(data)}'})


@app.route('/filter/category/total-price/', methods=['GET', 'POST'])
def filter_category_total_price():
    category_list = tuple(request.args.get('list').split(','))
    cur.execute(f'''select sum(prod.product_price)
                        from category.products as prod
                        inner join category.category as cat
                        on cat.id = prod.category_id
                        where cat.id in {category_list};''')
    data = float(cur.fetchone()[0])
    return jsonify({'msg': f'total price of filtered products is {data}'})


@app.route('/filter/category/average-price/', methods=['GET', 'POST'])
def filter_category_average_price():
    category_list = tuple(request.args.get('list').split(','))
    cur.execute(f'''select AVG(prod.product_price)
                        from category.products as prod
                        inner join category.category as cat
                        on cat.id = prod.category_id
                        where cat.id in {category_list};''')
    data = cur.fetchone()[0]
    return jsonify({'msg': f'average price of filtered products is {data}'})


@app.route('/filter/category/', methods=['GET', 'POST'])
def filter_category():
    category_list = tuple(request.args.get('list').split(','))
    user_tree_array = []
    cur.execute(f'''select prod.id, prod.product_name, cat.category_name, prod.product_price
                    from category.products as prod
                    inner join category.category as cat
                    on cat.id = prod.category_id
                    where cat.id in {category_list} limit ;''')
    data = cur.fetchall()
    for row in data:
        user_tree_array.append({'id': row[0], 'name': row[1], 'category_name': row[2],
                                'products_price': row[3]})
    return jsonify({'msg': user_tree_array})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
