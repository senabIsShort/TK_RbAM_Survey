import csv
import uuid
import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

# This secret key is used by Flask for session management and should be kept secret in production.
# Use an environment variable in production for better security.
app.secret_key= os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY environment variable is not set. Please set it to a secure random value.")

if not os.path.exists(os.path.join(os.getcwd(), 'responses')):
    os.makedirs(os.path.join(os.getcwd(), 'responses'))

argument_pairs = pd.read_csv('selected_training_dataset-filtered.csv').sample(frac=1).reset_index(drop=True)
original_pairs = argument_pairs.copy()
original_pairs['show_reasoning'] = False
duplicate_pairs = argument_pairs.copy()
duplicate_pairs['show_reasoning'] = True
argument_pairs = pd.concat([original_pairs, duplicate_pairs], ignore_index=True)
argument_pairs['id'] = argument_pairs.index
argument_pairs = argument_pairs.to_dict(orient='records')

@app.route('/')
def index():
    session.permanent = True  # Session expires after 31 days by default and refreshes on each request
    session['nb_pairs'] = len(argument_pairs) - 1
    return render_template("index.html")

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
    else:
        pair =  argument_pairs[pair_id]
        show_reasoning = pair['show_reasoning']
    return render_template("pair.html", pair=pair, show_reasoning=show_reasoning)

@app.route('/submit', methods=['POST'])
def submit():
    predictedRelation = request.form['predictedRelation']
    trueRelation = request.form['trueRelation']
    comment = request.form['comment']
    arg_id = request.form['arg_id']
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
            writer.writerow(['arg_id', 'argSrc', 'argTrg', 'trueRelation', 'predictedRelation', 'reasoning_shown', 'reasoning', 'clarity', 'helpfulness', 'comment'])
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([arg_id, argSrc, argTrg, trueRelation, predictedRelation, reasoning_shown, reasoning, clarity, helpfulness, comment])

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

@app.route('/about', methods=['GET'])
def about():
    return render_template("about.html")

if __name__ == '__main__':
    app.run(debug=True)
