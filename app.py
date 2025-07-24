import csv
import uuid
import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, send_file, abort
import zipfile
import tempfile
from example_pairs import example_pairs

app = Flask(__name__)

# This secret key is used by Flask for session management and should be kept secret in production.
# Use an environment variable in production for better security.
app.secret_key= os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY environment variable is not set. Please set it to a secure random value.")

if not os.path.exists(os.path.join(os.getcwd(), 'responses')):
    os.makedirs(os.path.join(os.getcwd(), 'responses'))

argument_pairs = pd.read_csv('selected_training_dataset-filtered-smaller.csv').sample(frac=1).reset_index(drop=True)

original_pairs = argument_pairs.copy()
original_pairs['show_reasoning'] = False
duplicate_pairs = argument_pairs.copy()
duplicate_pairs['show_reasoning'] = True
# Interleave original and duplicate pairs
interleaved_pairs = []
for i, row in original_pairs.iterrows():
    interleaved_pairs.append(row)
    interleaved_pairs.append(duplicate_pairs.iloc[i])
argument_pairs = pd.DataFrame(interleaved_pairs, index=None).reset_index(drop=True)
argument_pairs['id'] = argument_pairs.index
print(argument_pairs[['argSrc', 'show_reasoning']])

argument_pairs = argument_pairs.to_dict(orient='records')
@app.route('/')
def index():
    session.permanent = True  # Session expires after 31 days by default and refreshes on each request
    session['nb_pairs'] = len(argument_pairs) - 1
    return render_template("disclaimer.html")

@app.route('/examples', methods=['GET'])
def examples():
    return render_template("examples.html", pairs=example_pairs)

@app.route('/start', methods=['GET'])
def start():
    if 'uuid' in session and 'current_pair_id' in session:
        userid = session['uuid']
        pair_id = session['current_pair_id']
        done = session.get('finished', False)
        if done:
            return redirect('/thankyou')
    else:
        userid = str(uuid.uuid4())
        session['uuid'] = userid
        pair_id = 0
        session['current_pair_id'] = pair_id
        done = False
        session['finished'] = done
    return redirect(url_for('pair', pair_id=pair_id))

@app.route('/pair/<int:pair_id>', methods=['GET'])
def pair(pair_id : int):
    if 'uuid' not in session or 'current_pair_id' not in session:
        return redirect('/')
    
    is_done = session.get('finished', False)
    if is_done:
        return redirect('/thankyou')
    if pair_id!= session['current_pair_id']:
        return redirect(url_for('pair', pair_id=session['current_pair_id']))
    
    pair =  argument_pairs[pair_id]
    show_reasoning = pair['show_reasoning']
    return render_template("pair.html", pair=pair, show_reasoning=show_reasoning)

@app.route('/submit', methods=['POST'])
def submit():
    arg_id = request.form['arg_id']

    if int(arg_id) != session['current_pair_id']:
        return redirect(url_for('pair', pair_id=session['current_pair_id']))

    predictedRelation = request.form['predictedRelation']
    trueRelation = request.form['trueRelation']
    confidence = int(request.form['confidence'])
    comment = request.form['comment']
    argSrc = request.form['argSrc']
    argTrg = request.form['argTrg']
    reasoning_shown = request.form.get('reasoning_shown', 'False') == 'True'

    
    reasoning = request.form['reasoning'] if reasoning_shown else None
    clarity = int(request.form['clarity']) if reasoning_shown else None
    helpfulness = int(request.form['helpfulness']) if reasoning_shown else None

    # Save response to CSV
    output_path = os.path.join(os.getcwd(), 'responses', session['uuid']+'.csv')
    if not os.path.exists(output_path):
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['arg_id', 'argSrc', 'argTrg', 'trueRelation', 'predictedRelation', 'confidence', 'reasoning_shown', 'reasoning', 'clarity', 'helpfulness', 'comment'])
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([arg_id, argSrc, argTrg, trueRelation, predictedRelation, confidence, reasoning_shown, reasoning, clarity, helpfulness, comment])

    if arg_id == str(session.get('nb_pairs', 0)):
        session['finished'] = True
        return redirect('/thankyou')
    else:
        next_pair_id = int(arg_id) + 1
        session['current_pair_id'] = next_pair_id
        return redirect(url_for('pair', pair_id=next_pair_id))

@app.route('/thankyou', methods=['GET'])
def thankyou():
    return render_template("thankyou.html")

# @app.route('/about', methods=['GET'])
# def about():
#     return render_template("about.html")

@app.route('/download', methods=['GET'])
def download_page():
    return render_template("download.html")

@app.route("/download", methods=["POST"])
def download_file():
    # Get the password from the password form field
    provided_password = request.form.get("password")
    correct_password = os.getenv("DOWNLOAD_PASSWORD")

    if not correct_password:
        abort(500, "Server misconfigured: DOWNLOAD_PASSWORD is not set.")

    if provided_password != correct_password:
        abort(403, "Unauthorized: invalid password.")
    
    # Create a temporary zip file
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    responses_dir = os.path.join(os.getcwd(), 'responses')

    with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(responses_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, responses_dir)
                zipf.write(file_path, arcname)

    file_path = temp_zip.name
    if not os.path.exists(file_path):
        abort(404, "File not found.")

    return send_file(file_path, as_attachment=True)
