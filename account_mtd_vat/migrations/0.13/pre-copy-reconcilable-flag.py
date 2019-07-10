def migrate(cr, installed_version):
    if not column_exists(cr, schema='public', table='account_account',
            column='not_reconcilable_by_user'):
        cr.execute("""
            ALTER TABLE account_account
            RENAME COLUMN reconcile TO not_reconcilable_by_user 
        """)


def column_exists(cr, schema, table, column):
    sql = """
        select exists (
            SELECT 1
            FROM information_schema.columns
            WHERE
                table_schema=%s
                AND table_name=%s
                AND column_name=%s
        )
    """
    cr.execute(sql, (schema, table, column,))
    (exists,) = cr.fetchone()
    return exists