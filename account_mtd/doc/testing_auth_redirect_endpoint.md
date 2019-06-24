# Testing /auth-redirect

## Case where no trackers are there

Use the sandbox.

Run SQL:

```sql
DELETE FROM mtd_api_request_tracker;
```

When logged into the same Odoo database through web UI, visit (assuming running locally on port 8069):

http://localhost:8069/auth-redirect?code=42

Expected outcome:
* You should see an error message telling you there is no active token.
* There should be instructions for how to get back to a point where the user can try again.

## Case where there are more than one tracker

Use the sandbox.

Run SQL:

```sql
DELETE FROM mtd_api_request_tracker;
delete from mtd_api_tokens;
```

Find a page where you can submit something to HMRC, e.g.
Retrieve VAT Periods (in account_mtd_vat), with a brand new test VAT number in the sandbox,
and click the action button.

This should redirect you onto HMRC's site.  Don't proceed or log in yet!

Follow this example for how to duplicate the tracker record in the database:

```
mtd-vat=# select * from mtd_api_request_tracker;
 id | menu_id | create_uid | request_sent | endpoint_id | api_id | write_uid |        create_date         | closed |      module_name      | action | user_id |         write_date         | company_id 
----+---------+------------+--------------+-------------+--------+-----------+----------------------------+--------+-----------------------+--------+---------+----------------------------+------------
 79 | 247     |          1 | t            | 1           |      2 |         1 | 2019-06-21 12:11:14.896257 |        | mtd_vat.vat_endpoints | 289    |       1 | 2019-06-21 12:11:14.896257 | 1
(1 row)

mtd-vat=# insert into mtd_api_request_tracker (menu_id,  create_uid, request_sent,  endpoint_id,  api_id,  write_uid, closed, module_name, action, user_id,  company_id) values (247, 1, true, 1, 2, 1, NULL, 'mtd_vat.vat_endpoints', 289, 1, 1);
INSERT 0 1

mtd-vat=# select * from mtd_api_request_tracker;
 id | menu_id | create_uid | request_sent | endpoint_id | api_id | write_uid |        create_date         | closed |      module_name      | action | user_id |         write_date         | company_id 
----+---------+------------+--------------+-------------+--------+-----------+----------------------------+--------+-----------------------+--------+---------+----------------------------+------------
 79 | 247     |          1 | t            | 1           |      2 |         1 | 2019-06-21 12:11:14.896257 |        | mtd_vat.vat_endpoints | 289    |       1 | 2019-06-21 12:11:14.896257 | 1
 80 | 247     |          1 | t            | 1           |      2 |         1 |                            |        | mtd_vat.vat_endpoints | 289    |       1 |                            | 1
(2 rows)

```


Now continue through the HMRC's authentication process in the browser.


Expected outcome:
* When you've authorised the app, you should be redirected back to an error message page.
* The message should tell you that more than one authentication request was in progress.
* Check that the instructions given to you can take you back to the point where you can try again,
  and that trying again (without other users attempting to do an auth at the same time) works this time.
