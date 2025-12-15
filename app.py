from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import os

# ================= API =================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")

client = Groq(api_key=GROQ_API_KEY)

app = Flask(__name__)
chat_memory = []

MAKER_QUESTIONS = [
    "who is your maker",
    "who made you",
    "who created you",
    "tumhara maker kaun hai"
]

INTENT_PROMPT = """
You are an intent detector.
Understand user intent and reply ONLY one word:

youtube
google
website
game
chat
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EHSAAN.BOT</title>

<style>
body{margin:0;background:#0f1724;color:white;font-family:system-ui}
header{text-align:center;padding:12px;background:#020617;font-weight:bold}
#chat{height:75vh;overflow-y:auto;padding:10px}
.bubble{max-width:85%;padding:10px;margin:8px;border-radius:12px}
.user{background:#2563eb;margin-left:auto}
.bot{background:#020617;border:1px solid #1e293b}
pre{background:black;padding:10px;border-radius:8px;position:relative}
.copy{position:absolute;top:5px;right:5px;background:#22c55e;border:none;padding:4px 6px}
#input{position:fixed;bottom:0;width:100%;display:flex;gap:6px;padding:8px;background:#020617}
input{flex:1;padding:10px;border-radius:8px;border:none}
button{padding:10px;border:none;border-radius:8px}
#mic{background:#ef4444;color:white}
#send{background:#22c55e;color:white}
</style>
</head>

<body>
<header>🤖 EHSAAN.BOT</header>
<div id="chat"></div>

<div id="input">
<button id="mic" onclick="mic()">🎤</button>
<input id="msg" placeholder="Type or speak...">
<button id="send" onclick="send()">➤</button>
</div>

<script>
let synth=speechSynthesis,rec,micState=0;

if('webkitSpeechRecognition'in window){
 rec=new webkitSpeechRecognition();
 rec.continuous=true;
 rec.onresult=e=>{
 document.getElementById("msg").value=
 e.results[e.results.length-1][0].transcript;
 };
}

function mic(){
 let m=document.getElementById("mic");
 if(micState==0){rec.start();m.innerText="🔴";micState=1;}
 else if(micState==1){rec.stop();m.innerText="🔇";micState=2;}
 else{synth.cancel();m.innerText="🎤";micState=0;}
}

function speak(t){
 synth.cancel();
 let u=new SpeechSynthesisUtterance(t);
 u.lang=/[\\u0900-\\u097F]/.test(t)?"hi-IN":"en-IN";
 synth.speak(u);
}

function copy(btn){
 navigator.clipboard.writeText(btn.nextElementSibling.innerText);
 btn.innerText="✅";
}

async function send(){
 let msg=document.getElementById("msg").value;
 if(!msg)return;
 chat.innerHTML+=`<div class="bubble user">${msg}</div>`;
 document.getElementById("msg").value="";
 let r=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg})});
 let j=await r.json();
 if(j.action=="open")window.open(j.url,"_blank");
 chat.innerHTML+=`<div class="bubble bot">${j.reply}</div>`;
 speak(j.reply.replace(/<[^>]+>/g,""));
 chat.scrollTop=chat.scrollHeight;
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    user = request.json["message"].lower()

    for q in MAKER_QUESTIONS:
        if q in user:
            return jsonify({"reply": "Ehsaan is my maker."})

    intent = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content":INTENT_PROMPT},
            {"role":"user","content":user}
        ]
    ).choices[0].message.content.strip().lower()

    if intent=="youtube":
        return jsonify({"reply":"Opening YouTube","action":"open","url":"https://youtube.com"})
    if intent=="google":
        return jsonify({"reply":"Opening Google","action":"open","url":"https://google.com"})
    if intent=="game":
        return jsonify({"reply":"Opening Game Zone","action":"open","url":"https://chromedino.com"})

    chat_memory.append({"role":"user","content":user})
    chat_memory[:] = chat_memory[-6:]

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"system","content":"You are EHSAAN.BOT. Your maker is Ehsaan."}]+chat_memory
    )

    reply = res.choices[0].message.content
    reply = reply.replace("```","<pre><button class='copy' onclick='copy(this)'>📋</button><code>").replace("\n","<br>")
    chat_memory.append({"role":"assistant","content":reply})

    return jsonify({"reply":reply})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)))
