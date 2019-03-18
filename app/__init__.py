import os

from flask import Flask, render_template
from flask_caching import Cache
from bs4 import BeautifulSoup
import requests


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        CACHE_TYPE="simple",  # Flask-Caching related configs
        CACHE_DEFAULT_TIMEOUT=3600,
    )
    cache = Cache(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/')
    @cache.cached()
    def index():
        def list_of_assessments():
            query_url = "https://www.gov.uk/api/search.json?filter_content_store_document_type=" \
                        "service_standard_report&order=-public_timestamp&count=1000"
            return requests.get(query_url).json()['results']

        def assessment_urls():
            return {assessment.get('title'): assessment.get('link') for assessment in list_of_assessments()}

        def assessment_content():
            print('Not cached!')
            base_url = "https://www.gov.uk/api/content"
            return {title: requests.get(base_url + link).json()['details']['body']
                    for title, link in assessment_urls().items()}

        def assessment_summary():
            return {title: BeautifulSoup(content, 'html.parser').table for title, content in assessment_content().items()}

        return render_template('index.html', content_items=assessment_summary())
    return app

