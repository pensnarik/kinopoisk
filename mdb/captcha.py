import requests
import config
import base64
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class CaptchaSolver():

    def __init__(self, filename):
        with open(filename, 'rb') as f:
            self.data = base64.b64encode(f.read())

    def CreateTask(self):
        data = {'clientKey': config.anticaptcha['key'], 'languagePool': 'rn',
                'task': {'type': 'ImageToTextTask', 'body': self.data}}

        r = requests.post('%s/createTask' % config.anticaptcha['url'], json=data)
        if r.status_code != 200:
            raise Exception('Error in CreateTask(), status_code = %s', r.status_code)

        result = r.json()
        logger.info(result)

        if result['errorId'] != 0:
            return None
        return result['taskId']

    def GetTaskResult_(self, task_id):
        data = {'clientKey': config.anticaptcha['key'], 'taskId': task_id}
        r = requests.post('%s/getTaskResult' % config.anticaptcha['url'], json=data)
        data = r.json()
        logger.info(data)
        return data

    def GetTaskResult(self, task_id):

        solution = None

        while True:
            data = self.GetTaskResult_(task_id)

            if data['status'] == 'ready':
                solution = data['solution']['text']
                break
            elif data['status'] == 'processing':
                time.sleep(10)
            else:
                logger.error(data)
                break

        return solution