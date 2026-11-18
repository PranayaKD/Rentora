import asyncio
import json
import websockets

async def click_pay_now():
    uri = 'ws://localhost:9222/devtools/page/2497'
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
        
        js_code = """
        (function() {
            const cb = document.getElementById('tnc-checkbox');
            if (cb) cb.checked = true;
            handlePaymentSubmit();
            return { checked: cb ? cb.checked : false };
        })()
        """
        
        await ws.send(json.dumps({
            'id': 2,
            'method': 'Runtime.evaluate',
            'params': {
                'expression': js_code,
                'returnByValue': True
            }
        }))
        
        while True:
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(msg)
            if data.get('id') == 2:
                print('Payment submitted:', data['result']['result']['value'])
                break

if __name__ == '__main__':
    asyncio.run(click_pay_now())
