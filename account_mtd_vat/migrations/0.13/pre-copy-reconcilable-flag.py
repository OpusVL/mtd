def migrate(cr, installed_version):
    cr.execute("""
        select exists (
            SELECT 1
            FROM information_schema.columns
            WHERE
                table_schema='public'
                AND table_name='account_account'
                AND column_name='non_mtd_reconcilable'
        )
    """)
    (column_already_exists,) = cr.fetchone()
    if not column_already_exists:
        cr.execute("""
        ALTER TABLE account_account
        ADD COLUMN non_mtd_reconcilable BOOLEAN 
    """)
    cr.execute("""
        UPDATE account_account
            SET non_mtd_reconcilable = reconcile
    """)
