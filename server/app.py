import os
from flask import send_from_directory
from scripts.image_processing.process import process_image
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

current_directory = os.path.dirname(os.path.realpath(__file__))

UPLOAD_FOLDER = (os.getenv('UPLOAD_FOLDER') or '').replace('{PATH}', current_directory)
PROCESSED_FOLDER = (os.getenv('PROCESSED_FOLDER') or '').replace('{PATH}', current_directory)

try:
    os.mkdir(UPLOAD_FOLDER)
except FileExistsError:
    pass

try:
    os.mkdir(PROCESSED_FOLDER)
except FileExistsError:
    pass

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.secret_key = 'the random string'


@app.route("/")
def hello_world():
    return "<form action='/images' method='POST' enctype=multipart/form-data><input type='file' name='file'/><input type='submit' name='password'/></form>"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/images", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect('/')
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect('/')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(full_file_path)

            images = process_image(file_name=full_file_path, output_dir=app.config['PROCESSED_FOLDER'])
            download_url = url_for('download_file', name=filename)
            download_urls = [url_for('download_processed_file', name=filename) for filename in images] + [download_url]

            return "" \
                   + "<html>" \
                     "    <head>" \
                     "        <style>img {display:inline;}</style>" \
                     "    </head>" \
                   + "<body>" \
                     "".join(["<img height=300 src=\'{0}\' />".format(url) for url in download_urls]) \
                   + "</body>" \
                     "</html>"
    return 'boon'


app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)


@app.route('/generated/<name>')
def download_processed_file(name):
    return send_from_directory(app.config["PROCESSED_FOLDER"], name)


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3565)
