from flask import Flask, render_template, request as flask_request, Response, flash, redirect, url_for, send_file
import csv
import re
from urllib.parse import unquote
from user_agents import parse
from io import StringIO, BytesIO

app = Flask(__name__)
app.secret_key = 'your_secret_key'

log_data = []  # Initialize log_data at the top-level scope

@app.route('/', methods=['GET', 'POST'])
def index():
    global log_data  # Use the global log_data

    if flask_request.method == 'POST':
        uploaded_file = flask_request.files['file']

        if uploaded_file.filename != '':
            lines = uploaded_file.read().decode('utf-8').splitlines()
            log_data = []  # Reset log_data for each conversion

            for line in lines:
                match = re.match(r'^(.*?) - - \[(.*?)\] "(.*?)" (\d+) (\d+) "(.*?)" "(.*?)"$', line)
                if match:
                    ip_address, timestamp, request, status_code, response_size, referrer, user_agent_string = match.groups()

                    path_to_modules = re.sub(r'^GET (.*) HTTP/1.1$', r'\1', request)
                    decoded_path = unquote(path_to_modules)
                    cleaned_path = decoded_path.replace('%', '')

                    user_agent = parse(user_agent_string)

                    if user_agent.os.family == 'Linux':
                        device_type = 'Linux'
                    elif user_agent.os.family == 'Windows':
                        device_type = 'Windows'
                    elif user_agent.os.family == 'Android':
                        device_type = 'Android'
                    elif user_agent.os.family == 'iOS':
                        device_type = 'iOS'
                    else:
                        device_type = 'Other'

                    browser_name = user_agent.browser.family

                    log_data.append([ip_address, timestamp, cleaned_path, status_code, response_size, referrer, device_type, browser_name])

            output_csv = StringIO()
            csv_writer = csv.writer(output_csv)
            csv_writer.writerow(['IP Address', 'Timestamp', 'Item Paths', 'Status Code', 'Response Size', 'Site Paths', 'Device Type', 'Browser'])
            csv_writer.writerows(log_data)

            output_csv.seek(0)
            flash('File converted successfully!', 'success')
            return redirect(url_for('complete'))

    return render_template('index.html')

@app.route('/complete')
def complete():
    return render_template('complete.html')

@app.route('/download_csv')
def download_csv():
    global log_data  # Use the global log_data

    output_csv = StringIO()
    csv_writer = csv.writer(output_csv)
    csv_writer.writerow(['IP Address', 'Timestamp', 'Path to Item Viewed', 'Status Code', 'Item Size (Byte)', 'Path to Site Visited', 'Device Used', 'Browser Used'])
    csv_writer.writerows(log_data)  # Make sure log_data is available here

    output_csv.seek(0)
    return Response(
        output_csv.getvalue(),
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=Rachel_log.csv'}
    )

if __name__ == '__main__':
    app.run(debug=True)
