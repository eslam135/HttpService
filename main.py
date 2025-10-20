from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()
current_color = {"r": 1.0, "g": 1.0, "b": 1.0}
websockets = set()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def get_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Cube Color Controller</title>
        <style>
            body {
                font-family: "Segoe UI", sans-serif;
                background: linear-gradient(135deg, #141E30, #243B55);
                color: white;
                text-align: center;
                margin: 0;
                padding: 0;
            }
            h2 {
                margin-top: 2rem;
            }
            .container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 80vh;
            }
            .color-box {
                width: 150px;
                height: 150px;
                border-radius: 15px;
                margin: 1rem;
                border: 2px solid white;
                box-shadow: 0 0 20px rgba(255, 255, 255, 0.2);
            }
            input[type="color"] {
                width: 100px;
                height: 100px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                margin-top: 1rem;
            }
            .sliders {
                width: 80%;
                max-width: 400px;
                text-align: left;
                margin-top: 1.5rem;
            }
            .slider {
                width: 100%;
            }
            .slider-label {
                display: flex;
                justify-content: space-between;
                margin: 0.3rem 0;
            }
            .send-btn {
                background-color: #00bcd4;
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 10px;
                font-size: 1rem;
                cursor: pointer;
                margin-top: 1rem;
                transition: background-color 0.2s;
            }
            .send-btn:hover {
                background-color: #0097a7;
            }
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #00bcd4;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);
                opacity: 0;
                transition: opacity 0.5s, transform 0.5s;
                transform: translateY(-10px);
                z-index: 9999;
            }
            .toast.show {
                opacity: 1;
                transform: translateY(0);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Cube Color Controller</h2>

            <div class="color-box" id="preview"></div>
            <input type="color" id="colorPicker" value="#ffffff">

            <div class="sliders">
                <div class="slider-label"><span>Red</span><span id="rVal">1.0</span></div>
                <input type="range" id="r" min="0" max="1" step="0.01" value="1" class="slider" oninput="updateFromSliders()">
                <div class="slider-label"><span>Green</span><span id="gVal">1.0</span></div>
                <input type="range" id="g" min="0" max="1" step="0.01" value="1" class="slider" oninput="updateFromSliders()">
                <div class="slider-label"><span>Blue</span><span id="bVal">1.0</span></div>
                <input type="range" id="b" min="0" max="1" step="0.01" value="1" class="slider" oninput="updateFromSliders()">
            </div>

            <button class="send-btn" onclick="sendColor()">Send to Cube</button>
        </div>

        <div id="toast" class="toast">Color set successfully!</div>

        <script>
        const picker = document.getElementById('colorPicker');
        const preview = document.getElementById('preview');
        const toast = document.getElementById('toast');

        const ws = new WebSocket('wss://changerapi.azurewebsites.net/ws');

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === "color") {
                const c = msg.data;
                updatePreview(c.r, c.g, c.b, false);
            }
        };

        function showToast() {
            toast.classList.add("show");
            setTimeout(() => toast.classList.remove("show"), 1500);
        }

        function rgbToHex(r, g, b) {
            return "#" + [r, g, b].map(x => {
                const hex = Math.round(x * 255).toString(16).padStart(2, '0');
                return hex;
            }).join('');
        }

        function hexToRgb(hex) {
            return {
                r: parseInt(hex.substr(1, 2), 16) / 255,
                g: parseInt(hex.substr(3, 2), 16) / 255,
                b: parseInt(hex.substr(5, 2), 16) / 255
            };
        }

        function updatePreview(r, g, b, updateSliders = true) {
            const hex = rgbToHex(r, g, b);
            preview.style.background = hex;
            picker.value = hex;
            if (updateSliders) {
                document.getElementById('r').value = r;
                document.getElementById('g').value = g;
                document.getElementById('b').value = b;
            }
            document.getElementById('rVal').textContent = r.toFixed(2);
            document.getElementById('gVal').textContent = g.toFixed(2);
            document.getElementById('bVal').textContent = b.toFixed(2);
        }

        function updateFromSliders() {
            const r = parseFloat(document.getElementById('r').value);
            const g = parseFloat(document.getElementById('g').value);
            const b = parseFloat(document.getElementById('b').value);
            updatePreview(r, g, b, false);
            sendColorDebounced(r, g, b);
        }

        let sendTimeout;
        function sendColorDebounced(r, g, b) {
            clearTimeout(sendTimeout);
            sendTimeout = setTimeout(() => sendColor(r, g, b), 100);
        }

        async function sendColor(r, g, b) {
            if (r === undefined) {
                const rgb = hexToRgb(picker.value);
                r = rgb.r; g = rgb.g; b = rgb.b;
            }
            await fetch('/set_color', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({r, g, b})
            });
            showToast();
        }

        picker.addEventListener('input', () => {
            const rgb = hexToRgb(picker.value);
            updatePreview(rgb.r, rgb.g, rgb.b);
            sendColorDebounced(rgb.r, rgb.g, rgb.b);
        });

        updatePreview(1, 1, 1);
        </script>
    </body>
    </html>
    """


@app.get("/color")
def get_color():
    return current_color

@app.post("/set_color")
async def set_color(new_color: dict):
    global current_color
    current_color = new_color

    # Broadcast to all connected WebSockets
    msg = json.dumps({"type": "color", "data": new_color})
    for ws in list(websockets):
        await ws.send_text(msg)

    return {"status": "ok", "color": current_color}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    websockets.add(ws)

    # Send initial color
    await ws.send_text(json.dumps({"type": "color", "data": current_color}))

    try:
        while True:
            await ws.receive_text()
    except:
        websockets.remove(ws)