import atexit
import logging

from qtpy import QtWidgets

import qtpynodeeditor
from qtpynodeeditor import (NodeData, NodeDataModel, NodeDataType, PortType, StyleCollection)


output = open("nameTransation.txt", mode='w', encoding='utf-8')

ObfModels = []
CleanModels = []

@atexit.register
def atexit_fun():
    output.close()

def outdata(self, port):
    return [self.name,port]

def indata(self, node_data, port):
    if not node_data == None:
        print(node_data[0] + "[" + str(node_data[1]) +"]" + " -> " + self.name + "[" + str(getattr(port,"index")) +"]")
        output.write(node_data[0] + "[" + str(node_data[1]) +"]" + " -> " + self.name + "[" + str(getattr(port,"index")) +"]\r\n")

class MsgData(NodeData):
    data_type = NodeDataType(id='ProtoData', name='Field')

def addModel(msg, fields, isobf):
    if isobf:
        msg = msg + "-obf"
    else:
        msg = msg + "-clean"
    num_ports = {
        'input': len(fields) if isobf else 0,
        'output': len(fields) if not isobf else 0,
    }
    port_caption = {
        'input':fields if isobf else 0,
        'output':fields if not isobf else 0
    }
    Base = type(msg, (NodeDataModel, object), {'num_ports':num_ports,'port_caption_visible':True,'data_type':MsgData})
    return type(msg + "_model", (Base, object), {'name':msg,'port_caption':port_caption,'data_type':MsgData,'out_data':outdata,'set_in_data':indata})

def splitProto(proto, callback):

    fields = dict()

    file = ""
    stop = 0
    enum = False
    mark = False

    for line in proto:
        data = line.strip()
        if data == "":
            continue
        if data.startswith("//"):
            continue
        if mark:
            if not enum:
                array = data.split(" ")
                if not array[0].lower() == "" and not array[0].lower() == "}" and not array[0].lower() == "enum" and not array[0].lower() == "message" and not array[0].lower() == "oneof":
                    temp = data.split("//")[0].strip()
                    temp = temp.split(" ")
                    fields[len(fields)] = temp[len(temp) - 3]
        if data.startswith("enum"):
            enum = True
        if data.endswith("{"):
            if not mark:
                file = data.split(" ")[1] + ".proto"
            mark = True
            stop = stop + 1
        if data.startswith("}"):
            stop = stop - 1
            if enum:
                enum = False
            if stop == 0:
                callback(file, fields)
                fields = dict()
                file = ""
                mark = False

def loadObf(file, fields):
    ObfModels.append(addModel(file, fields, True))

def loadClean(file, fields):
    CleanModels.append(addModel(file, fields, False))

def main(app):

    splitProto(open('obf.proto', 'r').read().split('\n'), loadObf)
    print("已加载" + str(len(ObfModels)) + "个混淆Message")
    splitProto(open('clean.proto', 'r').read().split('\n'), loadClean)
    print("已加载" + str(len(CleanModels)) + "个未混淆Message")

    registry = qtpynodeeditor.DataModelRegistry()
    for Model in ObfModels:
        registry.register_model(Model, category='Obf')
    for Model in CleanModels:
        registry.register_model(Model, category='Clean')
    scene = qtpynodeeditor.FlowScene(registry=registry)

    view = qtpynodeeditor.FlowView(scene)
    view.setWindowTitle("Proto反混淆器")
    view.resize(1000, 700)
    
    scene.create_node(ObfModels[0])
    scene.create_node(CleanModels[0])

    return scene, view


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    app = QtWidgets.QApplication([])
    scene, view = main(app)
    view.show()
    app.exec_()
