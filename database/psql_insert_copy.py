from io import StringIO
import csv

TEMP_TABLE = 'temp_table'

def psql_insert_copy(table, conn, keys, data_iter, on_conflict_ignore=False):
    # gets a DBAPI connection that can provide a cursor

    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)
        columns = ', '.join('"{}"'.format(k) for k in keys)
        if table.schema:
            table_name = f'{table.schema}.{table.name}'
        else:
            table_name = table.name

        if on_conflict_ignore:
            create_table = f"""CREATE TEMP TABLE {TEMP_TABLE} ON COMMIT DROP AS 
            SELECT * FROM {table_name} WITH NO DATA"""
            cur.execute(create_table)
            
            copy_sql = f'COPY {TEMP_TABLE} ({columns}) FROM STDIN WITH (FORMAT CSV)'
            cur.copy_expert(sql=copy_sql, file=s_buf)

            insert_sql = f"INSERT INTO {table_name} SELECT * FROM {TEMP_TABLE} ON CONFLICT DO NOTHING"
            cur.execute(insert_sql)
        else:
            sql = f'COPY {table_name} ({columns}) FROM STDIN WITH (FORMAT CSV)'
            cur.copy_expert(sql=sql, file=s_buf)