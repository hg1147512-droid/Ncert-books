from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import socketio

# SOCKET.IO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)

app = FastAPI()

socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app
)

# STORE MESSAGES
messages = []

# HTML
html = """

<!DOCTYPE html>
<html>

<head>

<title>Private Chat</title>

<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>

<style>

body{
    margin:0;
    background:#0f0f0f;
    color:white;
    font-family:Arial;
    height:100vh;
    display:flex;
    flex-direction:column;
}

.topbar{
    background:#1c1c1c;
    padding:15px;
    font-size:25px;
    font-weight:bold;
}

#status{
    padding:8px 15px;
    color:lightgreen;
    font-size:14px;
    background:#161616;
}

#typing{
    padding-left:15px;
    color:#aaa;
    font-size:13px;
    height:20px;
}

#chat{
    flex:1;
    overflow-y:auto;
    padding:15px;
    display:flex;
    flex-direction:column;
}

.msg{
    padding:10px;
    border-radius:12px;
    margin:5px 0;
    width:fit-content;
    max-width:70%;
    word-wrap:break-word;
}

.mymsg{
    background:#0084ff;
    margin-left:auto;
}

.othermsg{
    background:#2a2a2a;
    margin-right:auto;
}

.msg img{
    max-width:250px;
    border-radius:10px;
}

.tick{
    font-size:12px;
    margin-top:5px;
    opacity:0.7;
    text-align:right;
}

.bottom{
    background:#1c1c1c;
    padding:10px;
    display:flex;
    gap:10px;
    align-items:center;
}

#msg{
    flex:1;
    padding:12px;
    border:none;
    border-radius:20px;
    background:#2a2a2a;
    color:white;
    outline:none;
}

button{
    padding:12px 18px;
    border:none;
    border-radius:20px;
    background:#0084ff;
    color:white;
    cursor:pointer;
}

</style>

</head>

<body>

<div class="topbar">
Private Chat
</div>

<div id="status">
Online 🟢
</div>

<div id="typing"></div>

<div id="chat"></div>

<div class="bottom">

<input type="file" id="imageInput" accept="image/*">

<input
id="msg"
placeholder="Type message"
oninput="typing()"
>

<button onclick="sendMsg()">Send</button>

<button onclick="sendImage()">📷</button>

</div>

<script>

const socket = io();

const chat = document.getElementById("chat");


// USERNAME
let username =
    sessionStorage.getItem("username");

if(!username){

    username = prompt("Enter your name");

    if(!username){
        username = "Anonymous";
    }

    sessionStorage.setItem(
        "username",
        username
    );
}

socket.emit("join", username);


// OLD MESSAGES
socket.on("old_messages", (msgs) => {

    msgs.forEach(item => {

        if(item.type === "text"){
            addText(item);
        }

        if(item.type === "image"){
            addImage(item);
        }

    });

});


// RECEIVE MESSAGE
socket.on("message", (data) => {

    addText(data);

});


// RECEIVE IMAGE
socket.on("image", (data) => {

    addImage(data);

});


// STATUS
socket.on("status", (msg) => {

    document.getElementById("status")
        .innerText = msg;

});


// TYPING
socket.on("typing", (name) => {

    if(name !== username){

        document.getElementById("typing")
            .innerText =
            name + " is typing...";

        setTimeout(() => {

            document.getElementById("typing")
                .innerText = "";

        }, 1000);

    }

});


// SEEN
socket.on("seen", (id) => {

    let tick =
        document.getElementById(id);

    if(tick){

        tick.innerText = "✓✓ Seen";

    }

});


// ADD TEXT
function addText(data){

    let div = document.createElement("div");

    div.className = "msg";

    if(data.user === username){

        div.classList.add("mymsg");

    }else{

        div.classList.add("othermsg");

        socket.emit("seen", data.id);

    }

    div.innerHTML =
        "<b>" + data.user + "</b><br>" +
        data.msg;

    let tick = document.createElement("div");

    tick.className = "tick";

    tick.id = data.id;

    if(data.user === username){

        tick.innerText = "✓ Sent";

    }

    div.appendChild(tick);

    chat.appendChild(div);

    chat.scrollTop = chat.scrollHeight;
}


// ADD IMAGE
function addImage(data){

    let div = document.createElement("div");

    div.className = "msg";

    if(data.user === username){

        div.classList.add("mymsg");

    }else{

        div.classList.add("othermsg");

        socket.emit("seen", data.id);

    }

    let name = document.createElement("b");

    name.innerText = data.user;

    let br = document.createElement("br");

    let img = document.createElement("img");

    img.src = data.image;

    div.appendChild(name);

    div.appendChild(br);

    div.appendChild(img);

    let tick = document.createElement("div");

    tick.className = "tick";

    tick.id = data.id;

    if(data.user === username){

        tick.innerText = "✓ Sent";

    }

    div.appendChild(tick);

    chat.appendChild(div);

    chat.scrollTop = chat.scrollHeight;
}


// SEND TEXT
function sendMsg(){

    let input =
        document.getElementById("msg");

    if(input.value.trim() !== ""){

        socket.emit("message", {

            id: crypto.randomUUID(),

            user: username,

            msg: input.value

        });

        input.value = "";
    }
}


// SEND IMAGE
function sendImage(){

    let fileInput =
        document.getElementById("imageInput");

    let file = fileInput.files[0];

    if(!file){

        alert("Choose image first");

        return;
    }

    let reader = new FileReader();

    reader.onload = function(e){

        socket.emit("image", {

            id: crypto.randomUUID(),

            user: username,

            image: e.target.result

        });

    };

    reader.readAsDataURL(file);

    fileInput.value = "";
}


// TYPING
function typing(){

    socket.emit("typing", username);

}

</script>

</body>
</html>

"""

# HOME
@app.get("/")
async def home():
    return HTMLResponse(html)


# CONNECT
@sio.event
async def connect(sid, environ):

    await sio.emit(
        "old_messages",
        messages,
        room=sid
    )


# JOIN
@sio.event
async def join(sid, username):

    await sio.emit(
        "status",
        f"{username} is online 🟢"
    )


# MESSAGE
@sio.event
async def message(sid, data):

    data["type"] = "text"

    messages.append(data)

    await sio.emit(
        "message",
        data
    )


# IMAGE
@sio.event
async def image(sid, data):

    data["type"] = "image"

    messages.append(data)

    await sio.emit(
        "image",
        data
    )


# TYPING
@sio.event
async def typing(sid, username):

    await sio.emit(
        "typing",
        username
    )


# SEEN
@sio.event
async def seen(sid, message_id):

    await sio.emit(
        "seen",
        message_id
    )