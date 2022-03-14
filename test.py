from fastapi.testclient import TestClient
from ops.common.common import EmailSchema
from main import app
import time
import pdb
import json
client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello Bigger Applications!"}


def test_post_mail():
    data = {"email": ['pengtao@kingsome.cn'], "body": 'test message!',
            "subject": 'ttt {}'.format(time.time())}
    response = client.post("/common/email", headers={"X-Token": "fake-super-scret-token", "accept": "application/json", "Content-Type": "application/json"},
                           data=json.dumps(data),
                           )
    # data=EmailSchema(**data).json()
    print(response)
    # pdb.set_trace()
    assert response.status_code == 200
    assert response.json() == {"message": "email has been sent"}


if __name__ == "__main__":
    test_post_mail()
