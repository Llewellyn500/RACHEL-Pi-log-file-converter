from flask import Flask, render_template, request as flask_request, Response, flash, redirect, url_for, session
import csv
import re
from urllib.parse import unquote
from user_agents import parse
from io import StringIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

log_data = []  # Initialize log_data at the top-level scope

@app.route('/', methods=['GET', 'POST'])
def index():
    global log_data  # Use the global log_data

    if flask_request.method == 'POST':
        uploaded_file = flask_request.files['file']

        if uploaded_file.filename != '':
            input_filename = uploaded_file.filename  # Get the input file name
            lines = uploaded_file.read().decode('utf-8').splitlines()
            log_data = []  # Reset log_data for each conversion

            for line in lines:
                match = re.match(r'^(.*?) - - \[(.*?)\] "(.*?)" (\d+) (\d+) "(.*?)" "(.*?)"$', line)
                if match:
                    ip_address, timestamp, request, status_code, response_size, _, user_agent_string = match.groups()

                    # Parse the timestamp into the desired format
                    timestamp = datetime.strptime(timestamp, "%d/%b/%Y:%H:%M:%S %z").strftime("%Y-%m-%d %H:%M")

                    path_to_modules = re.sub(r'^GET (.*) HTTP/1.1$', r'\1', request)
                    decoded_path = unquote(path_to_modules)
                    cleaned_path = decoded_path.replace('%', '')

                    # Extract the module name from the path
                    module_name_match = re.search(r'/modules/([^/]+)/', cleaned_path)
                    if module_name_match:
                        module_name = module_name_match.group(1)
                    else:
                        module_name = '-'

                    user_agent = parse(user_agent_string)

                    if user_agent.os.family == 'Linux':
                        device_type = 'Linux'
                    elif user_agent.os.family == 'Windows':
                        device_type = 'Windows'
                    elif user_agent.os.family == 'Android':
                        device_type = 'Android'
                    elif user_agent.os.family == 'iOS':
                        device_type = 'iOS'
                    elif user_agent.os.family == 'Chrome OS':
                        device_type = 'Chrome OS'
                    else:
                        device_type = '-'

                    browser_name = user_agent.browser.family if user_agent.browser.family else '-'

                    log_data.append([ip_address, timestamp, module_name, status_code, response_size, device_type, browser_name])

            output_csv = StringIO()
            csv_writer = csv.writer(output_csv)
            csv_writer.writerow(['IP Address', 'Timestamp (DD/MM/YYYY HH:MM)', 'Module Viewed', 'Status Code', 'Viewed Module Data Size (Byte)', 'Device Used', 'Browser Used'])
            csv_writer.writerows(log_data)

            output_csv.seek(0)
            flash('File converted successfully!', 'success')

            # Store the input filename in the session
            session['input_filename'] = input_filename

            return redirect(url_for('complete'))

    return render_template('index.html')

@app.route('/complete')
def complete():
    # Retrieve the input filename from the session
    input_filename = session.get('input_filename', 'unknown_filename')
    return render_template('complete.html', input_filename=input_filename)

@app.route('/download_csv')
def download_csv():
    global log_data  # Use the global log_data
    
    # Retrieve the input filename from the session
    input_filename = session.get('input_filename', 'unknown_filename')

    output_csv = StringIO()
    csv_writer = csv.writer(output_csv)
    csv_writer.writerow(['IP Address', 'Timestamp (DD/MM/YYYY HH:MM)', 'Module Viewed', 'Status Code', 'Viewed Module Data Size (Byte)', 'Device Used', 'Browser Used'])
    csv_writer.writerows(log_data)  # Make sure log_data is available here

    output_csv.seek(0)
    return Response(
        output_csv.getvalue(),
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename={input_filename}.csv'}  # Use input filename for output
    )

if __name__ == '__main__':
    app.run(debug=True)
