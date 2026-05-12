from flask import Flask, render_template, request, jsonify
from modbus import *

app = Flask(__name__)

@app.route('/home')
def index():
    return render_template('index.html')

@app.route('/Modbus')
def Modbus():
    typ = request.args.get('typ')
    val = request.args.get('val')
    client = connectMod()
    regist = readRegister(client)
    dig = createDig(regist)
    out = createList()
    ltyp = [typ]
    handle(dig, ltyp, val, out)
    write(client,out)
    disconnectMod(client)
    return 'done'    

@app.route('/Read')
def getStatus():
    client = connectMod()
    data = readRegister(client)
    disconnectMod(client)
    return jsonify(result=data)

if __name__ == "__main__":
    ##app.run(debug=True)
    app.run(host="192.168.2.165", port=5000, debug=True)
    