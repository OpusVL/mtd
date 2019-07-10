# Test reconcile flag migration

The migration in question is `migrations/0.13`

Here's an example run for how I test it.  Set `DBNAME` in first line to whatever version you had.

Set `YOURBRANCH` to the name of the branch you are currently working on.

```
$ DBNAME=mtd-vat
$ YOURBRANCH=mtd-vat-11.0-O2010-w1
```

Now get the version of the modules before the migration we want to run, stashing any uncommitted changes.

```
$ git fetch --tags
$ git stash    # NOTE WHETHER IT STASHED ANYTHING FOR LATER
$ git checkout mtd-vat-11.0   # 0.12 never happened by the looks of it
Note: checking out 'mtd-vat11.0'.

You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by performing another checkout.

If you want to create a new branch to retain commits you create, you may
do so (now or later) by using -b with the checkout command again. Example:

  git checkout -b <new-branch-name>

HEAD is now at eaa5c26... Merge pull request #46 from OpusVL/mtd-vat-8.0-O1832-w2
```

* Make extra sure mtd-vat-11.0 checks out OK (albeit with warning about a detached head)
  * If not, you should find another earlier tag or explicit commit number to check out.

In the following SQL run we do the backwards migration so we have a fair test.  If this one fails saying that the `non_mtd_reconcilable` column does not exist, that's fine for now.

Simply downgrading will lose the data we currently have in `is_reconcilable_by_user` and
all `reconcile` flags will end up False, which we don't want as it will mess up your
database and make our test more likely to pass falsely.

``` 
$ docker-compose exec postgresql psql -U odoo "$DBNAME"
mtd-vat=# ALTER TABLE account_account RENAME COLUMN is_reconcilable_by_user TO reconcile;
mtd-vat=# \q
```

Now downgrade the database, and check we don't have our custom column any more, but that the `reconcile` column has both values.
```
$ docker-compose run --rm odoo \
    -d "$DBNAME" -u account_mtd,account_mtd_vat \
    --max-cron-threads=0 --stop-after-init
$ docker-compose exec postgresql psql -U odoo "$DBNAME"
mtd-vat=# select distinct reconcile, is_reconcilable_by_user from account_account;
ERROR:  column "is_reconcilable_by_user" does not exist
LINE 1: select distinct reconcile, is_reconcilable_by_user from account...
mtd-vat=# select distinct reconcile from account_account;
 reconcile 
-----------
 f
 t
(2 rows)

mtd-vat=# \q
```

* Test Precondition:
  * `select distinct reconcile from account_account` above should have two rows: `t` and `f`
    * If not, then this test is meaningless because you have already somehow lost information in that column.  I suggest you manually arrange things so that there are records with both values of this flag before continuing.
    * This failing is also an indication you may have somehow messed up your database.
  * Note if there were also any NULL (blank) rows for later.

Now upgrade the database to latest version, and check you get the output specified.

```
$ git checkout "$YOURBRANCH"
$ git stash pop   # IF AND ONLY IF ANYTHING WAS STASHED ORIGINALLY
$ docker-compose run --rm --service-ports odoo \
    -d "$DBNAME" -u account_mtd,account_mtd_vat \
    --max-cron-threads=0 --stop-after-init
$ docker-compose exec postgresql psql -U odoo "$DBNAME"
mtd-vat=# select distinct is_reconcilable_by_user from account_account;
 is_reconcilable_by_user 
-------------------------
 f
 t
(2 rows)

mtd-vat=# \q
```

* Test conditions
  * There should be two distinct rows in the final SQL output - `t` and `f`:
    * FAIL if the table is empty
    * FAIL If there is only one of the two rows `t` and `f`.
    * It's OK to have NULLs if there were NULLS in the earlier precondition check.
