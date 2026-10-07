import mysql.connector

from config import Config


def get_db_connection():
    """Open and return a new MySQL connection using config values."""
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        autocommit=False
    )
    return conn

def log_action(user_id, action_description):
    """Write an audit record without letting failures interrupt the main action.

    Audit logging should never stop the main operation from completing because
    audit failures are secondary to application functionality.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, action_timestamp)
            VALUES (%s, %s, NOW())
            """,
            (user_id, action_description),
        )
        conn.commit()
    except Exception as exc:
        print(f"Audit logging failed: {exc}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
