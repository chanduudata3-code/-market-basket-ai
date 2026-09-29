"""Production entry point: python serve.py."""

import os


def main():
    if not os.environ.get('SECRET_KEY'):
        raise RuntimeError('Set a persistent random SECRET_KEY before starting the server.')

    from waitress import serve
    from app import app

    serve(app, host='0.0.0.0', port=int(os.getenv('PORT', '8000')))


if __name__ == '__main__':
    main()
