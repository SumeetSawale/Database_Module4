from flask import Blueprint, request, jsonify, Response
from database.db_manager import DatabaseManager

api = Blueprint('api', __name__)
db_manager = DatabaseManager()

@api.route('/databases', methods=['GET'])
def get_databases():
    try:
        databases = db_manager.list_databases()
        return jsonify({"databases": databases, "count": len(databases)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases', methods=['POST'])
def create_database():
    data = request.json
    if not data or 'name' not in data:
        return jsonify({"error": "Database name is required"}), 400
    
    try:
        db_manager.create_database(data['name'])
        return jsonify({"message": f"Database '{data['name']}' created successfully."}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases/<db_name>', methods=['DELETE'])
def delete_database(db_name):
    try:
        db_manager.delete_database(db_name)
        return jsonify({"message": f"Database '{db_name}' deleted successfully."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases/<db_name>/tables', methods=['GET'])
def get_tables(db_name):
    try:
        tables = db_manager.list_tables(db_name)
        return jsonify({"tables": tables, "count": len(tables)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases/<db_name>/tables', methods=['POST'])
def create_table(db_name):
    data = request.json
    if not data or 'name' not in data or 'schema' not in data:
        return jsonify({"error": "Table name and schema are required"}), 400
    
    try:
        order = data.get('order', 8)
        search_key = data.get('search_key')
        for i in data['schema']:
            if data['schema'][i] == "str":
                data['schema'][i] = str
            elif data['schema'][i] == "int":
                data['schema'][i] = int
            elif data['schema'][i] == "float":
                data['schema'][i] = float
            elif data['schema'][i] == "bool":
                data['schema'][i] = bool

        db_manager.create_table(db_name, data['name'], data['schema'], order, search_key)
        return jsonify({"message": f"Table '{data['name']}' created successfully in database '{db_name}'."}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases/<db_name>/tables/<table_name>', methods=['DELETE'])
def delete_table(db_name, table_name):
    try:
        db_manager.delete_table(db_name, table_name)
        return jsonify({"message": f"Table '{table_name}' deleted successfully from database '{db_name}'."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases/<db_name>/tables/<table_name>/records/<record_id>', methods=['GET'])
def get_records(db_name, table_name, record_id):
    try:
        table = db_manager.get_table(db_name, table_name)
        
        if record_id == "all":
            records = table.get_all()
            formatted_records = [{"id": i, "data": record} for i, record in enumerate(records)]
            return jsonify({"records": formatted_records, "count": len(formatted_records)})
        
        record_id = int(record_id)
        records = table.get_all()
        for i in records:
            if i[table.search_key] == record_id:
                return jsonify({"record": i}), 200
        return jsonify({"error": "Record not found"}), 404
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases/<db_name>/tables/<table_name>/records', methods=['POST'])
def create_record(db_name, table_name):
    data = request.json
    if not data:
        return jsonify({"error": "Record data is required"}), 400
    
    try:
        table = db_manager.get_table(db_name, table_name)
        table.insert(data)
        return jsonify({"message": "Record created successfully"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/databases/<db_name>/tables/<table_name>/records/<record_id>', methods=['PUT'])
def update_record(db_name, table_name, record_id):
    data = request.json
    if not data:
        return jsonify({"error": "Record data is required"}), 400
    
    table = None  # Initialize table to None
    try:
        table = db_manager.get_table(db_name, table_name)
        record_id = int(record_id)
        records = table.get_all()
        for i in records:
            if i[table.search_key] == record_id:
                table.update(i[table.search_key], data)
                return jsonify({"message": "Record updated successfully"}), 200
        return jsonify({"error": "Record not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases/<db_name>/tables/<table_name>/records/<record_id>', methods=['DELETE'])
def delete_record(db_name, table_name, record_id):
    table = None # Initialize table to None
    try:
        table = db_manager.get_table(db_name, table_name)
        record_id = int(record_id)
        records = table.get_all()
        for i in records :
            if i[table.search_key] == record_id:
                table.delete(i[table.search_key])
                return jsonify({"message": "Record deleted successfully"}), 200
        # If the record is not found in the loop, return an error message
        return jsonify({"error": "Record not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases/<db_name>/tables/<table_name>/search', methods=['POST'])
def search_records(db_name, table_name):
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "Search query is required"}), 400

    try:
        table = db_manager.get_table(db_name, table_name)
        results = table.search(data['query'])
        formatted_results = [{"id": i, "data": record} for i, record in enumerate(results)]
        return jsonify({"results": formatted_results, "count": len(results)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases/<db_name>/tables/<table_name>/range', methods=['POST'])
def range_query(db_name, table_name):
    data = request.json
    if not data or 'start' not in data or 'end' not in data:
        return jsonify({"error": "Start, end, and field are required for range query"}), 400

    try:
        table = db_manager.get_table(db_name, table_name)
        start = data['start']
        end = data['end']
        results = table.range_query(int(start), int(end))
        formatted_results = [{"id": i, "data": record} for i, record in enumerate(results)]
        return jsonify({"results": formatted_results, "count": len(results)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/databases/<db_name>/tables/<table_name>/visualize', methods=['GET'])
def visualize_tree(db_name, table_name):
    try:
        table = db_manager.get_table(db_name, table_name)
        dot = table.data.visualize_tree()
        svg_data = dot.pipe(format='svg').decode('utf-8')
        return Response(svg_data, mimetype='image/svg+xml')
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500