import sys
import socket
import threading

from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QWidget,
    QComboBox,
    QGridLayout,
    QMessageBox,
)
power = False
retour=""
clients=[]

def print(txt):
    global retour
    global window
    retour=f"{retour} \r {txt}"
    window.sortie.setText(retour)

class MainWindow(QMainWindow):
    global power
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Le serveur de tchat")
        self.resize(350, 350)
        layout = QGridLayout()
        
        self.stacklayout = QStackedLayout()

        label = QLabel("Serveur")
        layout.addWidget(label,0,0)

        self.ip = QLineEdit()
        self.ip.setText("0.0.0.0")
        layout.addWidget(self.ip,0,1)

        label = QLabel("Port")
        layout.addWidget(label,1,0)

        self.port = QLineEdit()
        self.port.setText("4200")
        layout.addWidget(self.port,1,1)

        label = QLabel("Nombre de clients maximum")
        layout.addWidget(label,2,0)

        self.nb_client_max = QLineEdit()
        self.nb_client_max.setText("5")
        layout.addWidget(self.nb_client_max,2,1)

        self.btn = QPushButton("Démarrage du serveur")
        if power:
            self.btn.pressed.connect(self.stop)
        else:
            self.btn.pressed.connect(self.start)
        layout.addWidget(self.btn,3,0,1,2)

        self.sortie = QLineEdit()
        self.sortie.setReadOnly(True)
        self.sortie.dragEnabled()
        self.sortie.setTextMargins(0,100,0,100)
        layout.addWidget(self.sortie,4,0,3,2)
        
        self.exit = QPushButton("Quitter")
        self.exit.pressed.connect(exit)
        layout.addWidget(self.exit,9,0,1,2)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def start(self):
        try:
            ip = self.ip.text()
            port = int(self.port.text())
            nb_client_max = int(self.nb_client_max.text())

            self.btn.setText("Arrêt du serveur")
            self.exit.pressed.connect(self.stop)
            t = threading.Thread(target=session, args=(ip,port,nb_client_max))
            t.start()
            
            power = True

        except ValueError:
            self.show_error("Valeur incorrect : caractère incompatible")

    def stop(self):
        try:
            shutdown_event.set()

            self.btn.setText("Démarrage du serveur")
            
            power = False

        except ValueError:
            self.show_error("Valeur incorrect : caractère incompatible")
    
    def show_error(self, message):
        msg = QMessageBox(self)
        msg.setWindowTitle("Erreur")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

def session(ip,port,nb_client_max):
    global shutdown_event
    server_socket = socket.socket()
    try:
        server_socket.bind((ip, port))
    except OSError:
        print(f"\033[31mLe port {port} est déjà ouvert!\033[0m")
        server_socket.close()
        return
    server_socket.listen(nb_client_max)
    print("Serveur démarré et en attente de connexions...")

    while not shutdown_event.is_set():
        conn, address = server_socket.accept()
        print(f"\033[93mConnexion acceptée pour {address}\033[0m")
        clients.append(conn)
        t = threading.Thread(target=newclient, args=(conn, address))
        t.start()

def broadcast(message, sender_conn, address=None):
    for client in clients:
        if client != sender_conn:
            try:
                if address != None:
                    message=f"Message reçu de {address} : {message}"
                client.send(message.encode())
            except BrokenPipeError:
                print("Impossible d'envoyer à un client déconnecté")

def newclient(conn, address):
    reply = "ack"
    conn.send(reply.encode())
    while True:
        try:
            message = conn.recv(1024).decode()
            if not message:
                break
        except (ConnectionResetError, ConnectionAbortedError):
            print(f"\033[31mLa connexion avec {address} a été perdue.\033[0m")
            break
        except UnicodeDecodeError:
            reply = "err"
            conn.send(reply.encode())
            continue

        print(f"Message reçu de {address} : \033[92m{message}\033[0m")

        if message == "bye":
            print(f"\033[93mFermeture de la connexion avec {address}\033[0m")
            conn.send("bye".encode())
            break
        elif message == "arret":
            print("\033[93mArrêt du serveur\033[0m")
            conn.send("bye".encode())
            broadcast("arret", conn)
            shutdown_event.set()
            break
        else:
            broadcast(message, conn, address)
            conn.send("ack".encode())

    conn.close()
    clients.remove(conn)

shutdown_event = threading.Event()
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()