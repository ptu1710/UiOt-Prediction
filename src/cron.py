from datetime import datetime
from crontab import CronTab
from flask import Flask
import threading
import time
import subprocess
from flask import jsonify

app = Flask(__name__)

@app.route('/health')
def health_check():
    return 'OK'

@app.route('/do-prediction', methods=['POST'])
def run_job():
    try:
        # Run the prediction script
        result = subprocess.run(['python3', './src/prediction.py'], capture_output=True, text=True)
        
        # Log the time the job was run
        log_message = f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Job run\n"
        with open('./logs/cron.log', 'a') as log_file:
            log_file.write(log_message)
            log_file.write(result.stdout + '\n')
            log_file.write(result.stderr + '\n')
        
        return jsonify({"status": "success", "output": result.stdout, "error": result.stderr}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def run_cron_scheduler():
    tab = CronTab(user='root', tabfile='./crontab/crontab.tab')
    for result in tab.run_scheduler():
        print(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

def start_flask_app():
    print(
        "\n===>>> STARTING SERVICE AT: "
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S\n")
    )
    app.run(host="0.0.0.0", port=6000)

def main():
    cron_thread = threading.Thread(target=run_cron_scheduler)
    flask_thread = threading.Thread(target=start_flask_app)
    
    cron_thread.start()
    flask_thread.start()
    
    cron_thread.join()
    flask_thread.join()

if __name__ == "__main__":
    main()
