from fastapi import FastAPI
import platform
from subprocess import run, PIPE

app = FastAPI()

SERVER_IP = '100.77.2.1'

@app.get('/health')
def health_check():
    param = '-c'

    try:
        result = run(['ping', param, '3', SERVER_IP], stdout=PIPE, text=True, timeout=5)
        return {
            'ip': SERVER_IP,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except Exception as e:
        return {'error': str(e)}