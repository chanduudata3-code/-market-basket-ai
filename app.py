import json
import logging
import os
import secrets

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, Response
from werkzeug.utils import secure_filename

from utils.analyzer import analyze_dataset
from utils.ai_advisor import generate_ai_advice
from utils.predicter import predict_trend
from utils.suggestions import generate_suggestions
from utils.summary import generate_summary

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(24),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true',
)

UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads')
ALLOWED_EXTENSIONS = {'csv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_upload():
    old_file = session.pop('data_file', None)
    if old_file:
        old_path = os.path.join(UPLOAD_FOLDER, os.path.basename(old_file))
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError as exc:
                logger.warning('Could not remove old upload %s: %s', old_path, exc)


def load_dataset():
    file_name = session.get('data_file')
    if not file_name:
        return None

    file_path = os.path.join(UPLOAD_FOLDER, os.path.basename(file_name))
    if not os.path.exists(file_path):
        logger.warning('Expected upload not found: %s', file_path)
        return None

    try:
        return pd.read_csv(file_path)
    except Exception as exc:
        logger.error('Unable to load dataset from %s: %s', file_path, exc)
        return None


def sanitize_numeric_columns(df):
    numeric_columns = df.select_dtypes(include=['number']).columns
    for column in numeric_columns:
        if df[column].isna().all():
            df[column] = df[column].fillna(0)
        else:
            df[column] = df[column].fillna(df[column].median())
    return df


def build_analysis(df, selected_column=None):
    df = df.copy()
    df = sanitize_numeric_columns(df)

    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    selected_column = (
        selected_column if selected_column in numeric_columns else (numeric_columns[0] if numeric_columns else None)
    )

    charts = analyze_dataset(df, selected_column)
    prediction = predict_trend(df, selected_column)
    summary = generate_summary(prediction)

    return {
        'filename': session.get('filename'),
        'selected_column': selected_column,
        'numeric_columns': numeric_columns,
        'columns': df.columns.tolist(),
        'preview': df.head(5).fillna('').to_dict(orient='records'),
        'row_count': len(df),
        'column_count': len(df.columns),
        'charts': charts,
        'prediction': prediction,
        'summary': summary,
    }


@app.route('/', methods=['GET'])
def upload_page():
    error = session.pop('error', None)
    return render_template('upload.html', error=error, active_page='upload')


@app.errorhandler(413)
def upload_too_large(error):
    return render_template(
        'upload.html', error='Upload must be smaller than 16 MB.', active_page='upload'
    ), 413


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        session['error'] = 'No file uploaded.'
        return redirect(url_for('upload_page'))

    file = request.files['file']
    if file.filename == '':
        session['error'] = 'Please select a CSV file.'
        return redirect(url_for('upload_page'))

    if not allowed_file(file.filename):
        session['error'] = 'Only CSV files are supported.'
        return redirect(url_for('upload_page'))

    try:
        df = pd.read_csv(file)
    except Exception as exc:
        logger.error('CSV parsing failed: %s', exc)
        session['error'] = 'Unable to read CSV file. Please verify the file format and try again.'
        return redirect(url_for('upload_page'))

    if df.empty:
        session['error'] = 'Uploaded file is empty.'
        return redirect(url_for('upload_page'))

    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    if not numeric_columns:
        session['error'] = 'No numeric columns found. Upload a CSV with numeric data.'
        return redirect(url_for('upload_page'))

    cleanup_old_upload()
    filename = secure_filename(file.filename)
    tokenized_filename = f'{secrets.token_hex(8)}_{filename}'
    file_path = os.path.join(UPLOAD_FOLDER, tokenized_filename)

    file.stream.seek(0)
    file.save(file_path)

    session['data_file'] = tokenized_filename
    session['filename'] = filename
    session['selected_column'] = numeric_columns[0]

    logger.info('Uploaded file %s and selected initial column %s', filename, numeric_columns[0])
    return redirect(url_for('dashboard'))


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    df = load_dataset()
    if df is None:
        session['error'] = 'No uploaded dataset found. Please upload a CSV file.'
        return redirect(url_for('upload_page'))

    if request.method == 'POST':
        selected_column = request.form.get('selected_column')
        session['selected_column'] = selected_column
        logger.info('Selected column set to %s', selected_column)
        return redirect(url_for('dashboard'))

    analysis = build_analysis(df, session.get('selected_column'))
    return render_template('dashboard.html', analysis=analysis, active_page='dashboard')


@app.route('/suggestions', methods=['GET', 'POST'])
def suggestions():
    df = load_dataset()
    if df is None:
        session['error'] = 'No uploaded dataset found. Please upload a CSV file.'
        return redirect(url_for('upload_page'))

    question = request.form.get('question', '') if request.method == 'POST' else ''
    ai_advice = generate_ai_advice(df, question)
    return render_template(
        'suggestions.html',
        insights=generate_suggestions(df),
        ai_advice=ai_advice,
        question=question,
        active_page='suggestions',
    )


@app.route('/report', methods=['GET'])
def download_report():
    df = load_dataset()
    if df is None:
        session['error'] = 'No uploaded dataset found. Please upload a CSV file.'
        return redirect(url_for('upload_page'))

    analysis = build_analysis(df, session.get('selected_column'))
    report = {
        'file': analysis['filename'],
        'selected_column': analysis['selected_column'],
        'rows': analysis['row_count'],
        'columns': analysis['column_count'],
        'preview': analysis['preview'],
        'prediction': analysis['prediction'],
        'summary': analysis['summary'],
        'charts': analysis['charts'],
        'suggestions': generate_suggestions(df),
        'ai_advice': generate_ai_advice(df),
    }
    body = json.dumps(report, indent=2)
    return Response(
        body,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=report.json'},
    )


if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() in {'true', '1'})
