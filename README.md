vulekamali Data Manager
=============

This app provides Single Sign-on (SSO) and support for maintaining correct and consistent data for the vulekamali Budget Data Portal by the National Treasury of South Africa.

Setting up Development environment
-----------------------

```
docker-compose up db
```

Add the dokku remote to you local clone

```
git remote add dokku@treasury1.openup.org.za:budgetportal
```

Setup the database - either by running migrations against a new database, or by
loading a dump from elsewhere:

If you're setting up a new database:

```
docker-compose run --rm app python manage.py migrate
docker-compose run --rm app python manage.py loaddata fixtures/development-first-user
```

Then run the server

```
docker-compose up
```

Now you can login with initial the *development superuser*:

Username: `admin@localhost`
Password: `password`

A fixture is needed to set this up instead of `createsuperuser` because Django Allauth is configured to require verified email addresses.

### Load data

Load an initial set of financial years, spheres and governments. You might need to add more recent ones manually in the admin interface.

```
docker-compose run --rm app python manage.py loaddata fixtures/development-first-user
docker-compose run --rm app python manage.py load_departments 2019-20 national /code/departments-2019-20.csv
```

### Development best practises

* Put javascript into ``budgetportal/static/javascript/app.js``
* Put SCSS stylesheets into ``budgetportal/static/stylesheets/app.scss``
* Install new asset packs with Bower: ``bower install -Sp package-to-install``
* Get better debugging with ``python manage.py runserver_plus``

### Single Sign-on (SSO)

To use the Single Sign-on functionality in local development, make sure you set the relevant environment variables to match your local setup, e.g.

```
HTTP_PROTOCOL=http \
DISCOURSE_SSO_SECRET=... \
CKAN_SSO_URL=http://localhost/user/login \
EMAIL_HOST=localhost \
EMAIL_PORT=2525 \
EMAIL_USE_TLS= \
python manage.py runserver
```

Logout from ckan might not send you to the right URL to logout from DataManager. You can manually go to logout from this app at http://localhost:8000/accounts/logout/.

### Additional environment variables somtimes needing customisation for development

| Environment variable | Description |
| -------------------- | ------------|
| `DEBUG_CACHE`          | Enable the django app cache. Normally disabled by `DEBUG=True`, this enables it for development - see more in `settings.py`. |

Running tests
--------------

To be able to run tests, install test dependencies:

```bash
pip install -r requirements-test.txt
```

Install PhantomJS according to the right way for your operating system.

### Run the tests

```bash
python manage.py test
```

If any tests fail, the exit code will be non-zero and details will be printed to the console. Remember to scroll up a bit in the output to see stack traces corresponding server errors for HTTP-based tests.


Production deployment
---------------------

### Initial Deployment

You'll need:

* API key for a CKAN user who can modify datasets in the `national-treasury` organisation

Create and configure the app

```bash
dokku apps:create budgetportal
dokku config:set budgetportal DJANGO_DEBUG=false \
                              DISABLE_COLLECTSTATIC=1 \
                              DJANGO_SECRET_KEY=some-secret-key \
                              NEW_RELIC_APP_NAME=cool app name \
                              NEW_RELIC_LICENSE_KEY=new relic license key \
                              CKAN_API_KEY=... \
                              DATABASE_URL=postgresql://... \
                              EMAIL_HOST_PASSWORD=... \
                              DISCOURSE_SSO_SECRET=... \
                              RECAPTCHA_PRIVATE_KEY=...
git push dokku master
dokku run python manage.py migrate
dokku run python manage.py createsuperuser
dokku ps:scale budgetportal worker=1
```

Also use `dokku domains` to configure the hostnames that your app will serve.

### Authentication

Apart from the superuser, additional users authenticate using either username+password or OAuth with social media accounts, e.g. Google and Facebook.

To enable this, we use [django-allauth](django-allauth) add social media account providers which provide verified email addresses in Django Admin's Social Accounts section.

For Google, set up an OAuth Client ID in [Google API Console](https://console.developers.google.com/apis/credentials?project=vulekamali)


Loading departments in bulk
---------------------------

The departments and their metadata are loaded using the Django Manage Command `load_departments`.

The command can be called to update the production database using

```bash
DATABASE_URL=postgresql://...produser...:...prodpasswd...@proddbhost/budgetportal python manage.py load_departments 2018-19 national departments.csv
```

where

- `2018-19` is the financial year slug
- `national` is the sphere slug
- `departments.csv` is a CSV file as follows:

Required columns:

 - `government` - government name
 - `department_name`
 - `vote_number`

Optional columns:

 - `is_vote_primary` - TRUE or FALSE
 - `intro`
 - `website_url`

 [Markdown syntax](https://daringfireball.net/projects/markdown/syntax#header) must be used for formatting `intro`. e.g. 2 line breaks will result in new paragraphs. Use headings like `## Vote purpose`

 e.g. for national

 | government | department_name | vote_number | is_vote_primary | intro | website_url |
 |------------|-----------------|-------------|-----------------|-------|-------------|
| South Africa | The Presidency | 1 | TRUE | ## Vote purpose <br/><br/>Facilitate a common programme towards the ... <br/></br> ## Mandate <br/><br/>To serve the president in the execution of his ... | http://www.thepresidency.gov.za/ |
| South Africa | Centre for Public Service Innovation | 10 | FALSE | ## Vote purpose <br/><br/>Facilitate the unearthing, development and practical ...  <br/></br> ## Mandate <br/><br/> The responsibility for public sector innovation is vested in the Minister of Public Service... | www.cpsi.co.za |

e.g. for provincial

 | government | department_name | vote_number | is_vote_primary | intro | website_url |
 |------------|-----------------|-------------|-----------------|-------|-------------|
| Eastern Cape | Health | 3 | TRUE | ## Vision<br/><br/>A quality health service to the people of the ... <br/></br> ## Mission<br/><br/>To provide and ensure accessible comprehensive integrated ... <br/><br/> ## Core functions and responsibilities<br/><br/>The strategic objectives are in line with the implementation | |


License
-------

MIT License
