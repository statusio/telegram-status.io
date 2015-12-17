from flask import Flask, request
import json, ast, requests, os, requests
import logging, ConfigParser, os.path, sys

app = Flask(__name__)
app.debug = True
logging.basicConfig(filename='msg.log',level=logging.DEBUG, format='%(asctime)s %(message)s')

check = os.path.isfile(os.path.expanduser('~/.statusio.cfg'))
if cmp(check,False) == 0:
  print "~/.statusio.cfg is missing"
  sys.exit(2)

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/.statusio.cfg'))
api_key = config.get("telegram", "key", raw=True)
statuspage_id = config.get("statusio_auth", "page", raw=True)

def create_incident(incident):
    data = '''
    {
    "statuspage_id": "%s",
    "components": %s,
    "containers": %s,
    "incident_name": "%s",
    "incident_details": "%s",
    "notify_email": "0",
    "notify_sms": "0",
    "notify_webhook": "0",
    "social": "0",
    "irc": "0",
    "hipchat": "0",
    "slack": "0",
    "current_status": 300,
    "current_state": 100,
    "all_infrastructure_affected": "0"
    }
    '''
    data = data % (statuspage_id, incident[1], incident[0], incident[2], incident[3])
    data_json = json.loads(data.replace("['",'["').replace("']",'"]'))
    print data_json
    return send_statusio('create',data_json)

def resolve_incident(incident_id, incident_details):
    data = '''
    {
    "statuspage_id": "%s",
    "incident_id": "%s",
    "incident_details": "%s",
    "notify_email": "0",
    "notify_sms": "0",
    "notify_webhook": "0",
    "social": "0",
    "irc": "0",
    "hipchat": "0",
    "slack": "0"
    }
    '''
    data = data % (statuspage_id, incident_id, incident_details)
    data_json = json.loads(data.replace("['",'["').replace("']",'"]'))
    return send_statusio('resolve',data_json)

def send_statusio(action, data_json):
    headers = {'Content-Type':'application/json', 'x-api-id':config.get("statusio_auth", "id", raw=True), 'x-api-key':config.get("statusio_auth", "key", raw=True)}
    response = requests.post('https://api.status.io/v2/incident/%s' % (action, ), data = json.dumps(data_json), headers = headers)
    return json.loads(response.content)['result']

@app.route('/bot/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == "POST":
        incoming = request.get_data()
        logging.info(str(incoming))
        reply = 'BAD DATA'
        try:
            chat_id = ast.literal_eval(incoming)['message']['chat']['id']
            msg = ast.literal_eval(incoming)['message']['text'].strip().lower().split()
            if msg[1] == 'create':
                incident = " ".join(msg[2:]).split(';')
                containers = incident[0].split(',')
                components = incident[1].split(',')
                for i in range(len(containers)):
                    containers[i] = config.get("statusio_containers", containers[i], raw=True)
                for i in range(len(components)):
                    components[i] = config.get("statusio_components", components[i], raw=True)
                incident[0] = containers
                incident[1] = components
                reply = create_incident(incident)

            elif msg[1] == 'resolve':
                incident = " ".join(msg[2:]).split(';')
                reply = resolve_incident(incident[0],incident[1])

            else:
                reply = "What? I didn't get you."
        except Exception as e:
            print e

        requests.post('https://api.telegram.org/bot%s/sendMessage?chat_id=%s' % (api_key,str(chat_id)), data={'text':reply}) 
        return '{"status":"ok"}'
    if request.method == "GET":
        return '{"status":"ok"}'

if __name__ == '__main__':
    app.run(port=5001)
