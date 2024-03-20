from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from cryptography.fernet import Fernet
import random
import array
import os.path
import pymysql
import copy


# PATH = '/Users/Shared/CredentialsVault.txt'  #Mac
PATH = 'C:\\CredentialsVault.txt'  #Windows
# PATH = 'CredentialsVault.txt'  #Android
USERNAME = None
PASSWORD = None
HOST = None
DB = None
CURSOR = None
KEY = None
ALLRECORDS = []

def databaseConnect(username, password, host, database):
    global DB, CURSOR
    try:
        DB = pymysql.connect(
            host =host,
            user =username,
            passwd =password,
            database = database
        )

        CURSOR = DB.cursor()
        
        return True
    except Exception as e:
        popUp('Error', str(e))
        return False
    
def fetch_all():
    global CURSOR,DB

    ALLRECORDS.clear()
    CURSOR = DB.cursor()
    CURSOR.execute("SELECT * FROM Vault")
    data = CURSOR.fetchall()
    for i in data:
        ALLRECORDS.append(i)
    return ALLRECORDS

def insert_new_record(name, email, password):

    if(len(ALLRECORDS) != 0):
        id = ALLRECORDS[-1][0] + 1
    else:
        id = 0
    e_password = encrypt_password(KEY, password)

    sql = "INSERT INTO Vault (_id, Name, Email, Password) VALUES (%s, %s, %s, %s)"
    val = (id, name, email, e_password)
   
    CURSOR.execute(sql, val)
    DB.commit()

    fetch_all()

def find_one(id):
    
    CURSOR.execute(f"SELECT * FROM Vault where _id = {id}")
    return CURSOR.fetchall()

def update_one(id, password):
    CURSOR.execute(f"UPDATE Vault SET Password = '{password}' WHERE _id = {id}")
    DB.commit()

def delete_one(id):
    CURSOR.execute(f"DELETE FROM Vault where _id = {id}")
    return DB.commit()

def encrypt_password(key, password):
    f = Fernet(key)
    token = f.encrypt(str.encode(password))

    return token

def decrypt_password(key, password):
    f = Fernet(key)
    return f.decrypt(password.encode()).decode()

class LoginWindow(Screen):
    key = ObjectProperty(None)

    def validate(self):
        global USERNAME, PASSWORD, KEY
        KEY = self.key.text.encode()

        try:
            Fernet(KEY)

            if(os.path.isfile(PATH)):

                file = open(PATH, "r").read().split(';')
                USERNAME = decrypt_password(KEY, file[0])
                PASSWORD = decrypt_password(KEY, file[1])
                HOST = decrypt_password(KEY, file[2])
                DB = decrypt_password(KEY, file[3])

                databaseConnect(USERNAME, PASSWORD, HOST, DB)
                fetch_all()

                if(len(ALLRECORDS) != 0):
                    try:
                        decrypt_password(KEY, ALLRECORDS[0][-1])
                        self.key.text = ''
                        self.manager.current = 'mainwindow'
                    except Exception as e:
                        popUp('Invalid Form', 'Wrong Key')
                else:
                    self.key.text = ''
                    self.manager.current = 'mainwindow'
            else:
                popUp('Invalid Form', 'First save details correctly!')

        except Exception as e:
            popUp('Invalid Form', 'Wrong Key Given')

class KeyWindow(Screen):
    key = StringProperty()
    
    def generate(self):

        self.key = "Copy your key somewhere safe. Your key is : " + Fernet.generate_key().decode()

    def reset(self):

        self.key = ''

class PasswordWindow(Screen):

    key = StringProperty()
    
    def generate(self):
        self.key = generate_password()

    def reset(self):
        self.key = ''

class CredentialsWindow(Screen):

    host = ObjectProperty(None)
    db = ObjectProperty(None)
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    key = ObjectProperty(None)

    def validate(self):

        host = self.host.text
        db = self.db.text
        username = self.username.text
        password = self.password.text
        key = self.key.text.encode()

        if(databaseConnect(username, password, host, db)):

            f = open(PATH, "w")
            f.write(encrypt_password(key, username).decode() + ';' + encrypt_password(key, password).decode() + ';' + encrypt_password(key, host).decode() + ';' + encrypt_password(key, db).decode())
            f.close()

            try:
                CURSOR.execute("""CREATE TABLE Vault (
                            _id INT(8) NOT NULL,
                            Name VARCHAR(255) NOT NULL,
                            Email VARCHAR(255),
                            Password VARCHAR(255)
                            )""")
            except pymysql.connect.Error as err:
                pass
            
            self.reset()
            self.manager.current = 'loginwindow'
        else:
            popUp('Invalid Form', 'Wrong Database Credentials')

    def reset(self):
        self.host.text = ''
        self.db.text = ''
        self.username.text = ''
        self.password.text = ''
        self.key.text = ''


class MainWindow(Screen):
    pass

class ListWindow(Screen):
    passwords = ObjectProperty(None)

    def on_enter(self):
        finalString  = 'ID|Name|Email\n\n'
        records = copy.deepcopy(ALLRECORDS)
        records.sort(key = lambda x: x[1].lower())
        for i in records:
            finalString = finalString + str(i[0]) + ' ' + i[1] + ' ' + i[2] + '\n\n'
        finalString = finalString + '\n\nTotal Passwords: ' + str(len(records))
        self.passwords.text = finalString

class ViewWindow(Screen):
    idnumber = ObjectProperty(None)
    passwordname = ObjectProperty(None)
    email = ObjectProperty(None)
    password = ObjectProperty(None)

    def get_details(self):
        try:
            record = find_one(self.idnumber.text)
            self.idnumber.text = str(record[0][0])
            self.passwordname.text = record[0][1]
            self.email.text = record[0][2]
            self.password.text = decrypt_password(KEY, record[0][-1])
        except Exception as e:
            popUp("Error", str(e))
        

    def reset(self):
        self.idnumber.text = ''
        self.passwordname.text = ''
        self.email.text = ''
        self.password.text = ''


class AddWindow(Screen):

    passwordname = ObjectProperty(None)
    email = ObjectProperty(None)
    password = ObjectProperty(None)

    def store(self):
        insert_new_record(self.passwordname.text, self.email.text, self.password.text)
        self.reset()
        popUp('Success', 'Your password successfully added')


    def reset(self):
        self.passwordname.text = ''
        self.email.text = ''
        self.password.text = ''

class DeleteWindow(Screen):
   idnumber = ObjectProperty(None)

   def delete(self):
       
        try:
            delete_one(self.idnumber.text)
            popUp('Success', "Deleted ID "+ self.idnumber.text)
            self.reset()
            fetch_all()

        except Exception as e:
            popUp("Error", str(e))
            
   def reset(self):
       self.idnumber.text = ''

class UpdateWindow(Screen):
    idnumber = ObjectProperty(None)
    password = ObjectProperty(None)
    
    def update(self):
        
        try:
            e_password = encrypt_password(KEY, self.password.text).decode()
            update_one(self.idnumber.text, e_password)

            popUp('Success', "Updated ID "+ self.idnumber.text)
            self.reset()
            fetch_all()

        except Exception as e:
            popUp("Error", str(e))
    
    def reset(self):
       self.idnumber.text = ''
       self.password.text = ''

class WindowManager(ScreenManager):
    pass

kv = Builder.load_string('''WindowManager:
    LoginWindow:
    KeyWindow:
    PasswordWindow:
    CredentialsWindow:
    MainWindow:
    ListWindow:
    ViewWindow:
    AddWindow:
    DeleteWindow:
    UpdateWindow:

<LoginWindow>:
    name: 'loginwindow'
    key: key

    BoxLayout:
        size: root.width, root.height
        orientation: 'vertical'
        spacing: 50
        padding: 50

        BoxLayout:
            Label:
                text: 'Password Manager'
                font_size: 52

        BoxLayout:
            size_hint: (1,0.22)
            Label:
                size_hint: (0.1,1)
                text: 'Key: '
                font_size: 32

            TextInput:
                id: key 
                multiline: False
                password: True
        
        BoxLayout:
            size_hint: (0.3,0.3)
            pos_hint: {'center_x': 0.5}
            
            Button:
                text: 'Login'
                font_size: 32
                on_release:
                    root.validate()
                    root.manager.transition.direction = 'left'
        BoxLayout:
            spacing: 100
            Button:
                size_hint: (0.3,0.3)
                text: 'Edit Details'
                font_size: 32
                on_release:
                    app.root.current = 'credentialswindow'
                    root.manager.transition.direction = 'right'
            Button:
                text: 'Get new Key'
                size_hint: (0.3,0.3)
                font_size: 32
                on_release:
                    app.root.current = 'keywindow'
                    root.manager.transition.direction = 'down'

<KeyWindow>:
    name: 'keywindow'

    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height
        spacing: 50
        padding: 50


        BoxLayout:
            Label:
                text: 'Generate new Key'
                font_size: 52
                         
        BoxLayout:
            size_hint: (1,0.22)
            Label:
                size_hint: (0.1,1)
                text: 'Key: '
                font_size: 32

            TextInput:
                text: root.key
                font_size: 32
        
        BoxLayout:
            spacing: 100
                
            Button:
                text: 'Back'
                size_hint: (0.3,0.3)
                font_size: 32
                on_release:
                    root.reset()
                    app.root.current = 'loginwindow'
                    root.manager.transition.direction = 'up'
                         
            Button:
                text: 'Generate'
                size_hint: (0.3,0.3)
                font_size: 32
                on_release:
                    root.generate()

<PasswordWindow>:
    name: 'passwordwindow'

    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height
        spacing: 50
        padding: 50

        BoxLayout:
            Label:
                text: 'Generate Strong Password'
                font_size: 52

        BoxLayout:
            size_hint: (1,0.22)
            Label:
                size_hint: (0.2,1)
                text: 'Password: '
                font_size: 32
                         
            TextInput:
                text: root.key
                font_size: 32
        
        BoxLayout:    
            spacing: 100
            Button:
                size_hint: (0.3,0.3)
                text: 'Back'
                font_size: 32
                on_release:
                    root.reset()
                    app.root.current = 'mainwindow'
                    root.manager.transition.direction = 'right'

            Button:
                size_hint: (0.3,0.3)
                text: 'Generate'
                font_size: 32
                on_release:
                    root.generate()
        
<CredentialsWindow>:
    name: 'credentialswindow'
    host : host
    db : db
    username : username
    password : password
    key: key

    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height
        spacing: 50
        padding: 50

        BoxLayout:
            Label:
                text: 'Credentials'
                font_size: 52

        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Host: '
                font_size: 32

            TextInput:
                id: host
                multiline: False
                         
        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'DB: '
                font_size: 32

            TextInput:
                id: db
                multiline: False
                         
        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Username: '
                font_size: 32

            TextInput:
                id: username
                multiline: False

        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Password: '
                font_size: 32

            TextInput:
                id: password
                multiline: False
                password: True

        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Key: '
                font_size: 32

            TextInput:
                id: key
                multiline: False
                password: True
        
        BoxLayout:
            spacing: 100
            Button:
                text: 'Back'
                size_hint: (0.7,0.7)
                font_size: 32
                on_release:
                    root.reset()
                    app.root.current = 'loginwindow'
                    root.manager.transition.direction = 'left'
            Button:
                text: 'Save'
                size_hint: (0.7,0.7)
                font_size: 32
                on_release:
                    root.validate()
                    root.manager.transition.direction = 'left'

<MainWindow>:
    name: 'mainwindow'

    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height
        padding: 50

        Label:
            text: 'Dashboard'
            font_size: 52
        
        BoxLayout:
            spacing: 100
            Button:
                text: 'Add'
                size_hint: (0.3,0.3)
                font_size: 32
                on_release:
                    app.root.current = 'addwindow'
                    root.manager.transition.direction = 'left'
            Button:
                text: 'List'
                size_hint: (0.3,0.3)
                font_size: 32
                on_release:
                    app.root.current = 'listwindow'
                    root.manager.transition.direction = 'left'
        BoxLayout:
        BoxLayout:
            size_hint: (0.3,0.3)
            pos_hint: {'center_x': 0.5}
            Button:
                text: 'Generate Password'
                font_size: 32
                on_release:
                    app.root.current = 'passwordwindow'
                    root.manager.transition.direction = 'left'

<ListWindow>:
    name: 'listwindow'
    passwords: passwords

    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height
        spacing: 50
        padding: 50

        BoxLayout:
            padding: (0,0,0,-500)
            TextInput:
                id: passwords
                font_size: 32

        BoxLayout:
        BoxLayout:
        BoxLayout:
            size_hint: (0.3,0.3)
            pos_hint: {'center_x': 0.5}
            Button:
                text: 'View'
                font_size: 32
                on_release:
                    app.root.current = 'viewwindow'
                    root.manager.transition.direction = 'left'

        BoxLayout:
            spacing: 75
            Button:
                text: 'Back'
                font_size: 32
                size_hint: (0.3,0.3)
                on_release:
                    app.root.current = 'mainwindow'
                    root.manager.transition.direction = 'right'
            Button:
                text: 'Update'
                size_hint: (0.3,0.3)
                font_size: 32
                on_release:
                    app.root.current = 'updatewindow'
                    root.manager.transition.direction = 'left'
            Button:
                text: 'Delete'
                size_hint: (0.3,0.3)
                font_size: 32
                on_release:
                    app.root.current = 'deletewindow'
                    root.manager.transition.direction = 'left'

<ViewWindow>:
    name: 'viewwindow'
    idnumber: idnumber
    passwordname: passwordname
    email: email
    password: password

    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height
        spacing: 50
        padding: 50

        BoxLayout:
            Label:
                text: 'View Password'
                font_size: 52
        
        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Enter ID: '
                font_size: 32
                         
            TextInput:
                id: idnumber
                multiline: False

        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Name: '
                font_size: 32

            TextInput:
                id: passwordname
                multiline: False

        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Email: '
                font_size: 32

            TextInput:
                id: email
                multiline: False

        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Password: '
                font_size: 32

            TextInput:
                id: password
                multiline: False

        BoxLayout:
            spacing: 100
            Button:
                text: 'Back'
                font_size: 32
                size_hint: (0.7,.7)
                on_release:
                    root.reset()
                    app.root.current = 'listwindow'
                    root.manager.transition.direction = 'right'
            Button:
                text: 'Get'
                size_hint: (0.7,0.7)
                font_size: 32
                on_release:
                    root.get_details()
        

<AddWindow>:
    name: 'addwindow'
    passwordname: passwordname
    email: email
    password: password

    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height
        spacing: 50
        padding: 50

        BoxLayout:
            Label:
                text: 'Add new password'
                font_size: 52

        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Name: '
                font_size: 32

            TextInput:
                id: passwordname
                multiline: False
        
        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Email: '
                font_size: 32

            TextInput:
                id: email
                multiline: False

        BoxLayout:
            size_hint: (1,0.56)
            Label:
                size_hint: (0.2,1)
                text: 'Password: '
                font_size: 32

            TextInput:
                id: password
                multiline: False
                password: True
        
        BoxLayout:
            spacing: 100
            Button:
                text: 'Back'
                size_hint: (0.5,0.5)
                font_size: 32
                on_release:
                    app.root.current = 'mainwindow'
                    root.manager.transition.direction = 'right'
            Button:
                text: 'Save'
                font_size: 32
                size_hint: (0.5,0.5)
                on_release:
                    root.store()
                    root.manager.transition.direction = 'right'
            
            

<DeleteWindow>:
    name: 'deletewindow'
    idnumber: idnumber

    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height
        spacing: 50
        padding: 50

        BoxLayout:
            Label:
                text: 'Delete Password'
                font_size: 52
                         
        BoxLayout:
            size_hint: (1,0.26)
            Label:
                size_hint: (0.15,1)
                text: 'Enter ID: '
                font_size: 32

            TextInput:
                id: idnumber
                multiline: False
        
        BoxLayout:
            spacing: 100
            Button:
                text: 'Back'
                font_size: 32
                size_hint: (0.7,.2)
                on_release:
                    root.reset()
                    app.root.current = 'listwindow'
                    root.manager.transition.direction = 'right'         
            Button:
                text: 'Delete'
                size_hint: (0.7,.2)
                font_size: 32
                on_release:
                    root.delete()
        
<UpdateWindow>:
    name: 'updatewindow'
    idnumber: idnumber
    password: password

    BoxLayout:
        orientation: 'vertical'
        size: root.width, root.height
        spacing: 50
        padding: 50

        BoxLayout:
            Label:
                text: 'Update Password'
                font_size: 52

        BoxLayout:
            size_hint: (1,0.26)
            Label:
                size_hint: (0.2,1)
                text: 'Enter ID: '
                font_size: 32

            TextInput:
                id: idnumber
                multiline: False

        BoxLayout:
            size_hint: (1,0.26)
            Label:
                size_hint: (0.2,1)
                text: 'Password: '
                font_size: 32

            TextInput:
                id: password
                multiline: False
                password: True
        
        
        
        BoxLayout:
            spacing: 100
            Button:
                text: 'Back'
                font_size: 32
                size_hint: (0.7,.2)
                on_release:
                    root.reset()
                    app.root.current = 'listwindow'
                    root.manager.transition.direction = 'right' 
            Button:
                text: 'Update'
                font_size: 32
                size_hint: (0.7,.2)
                on_release:
                    root.update()''')

def popUp(heading, message):
    pop = Popup(title=heading,
                  content=Label(text=message),
                  size_hint=(None, None), size=(400, 400))

    pop.open()

class VaultApp(App):
    def build(self):
        return kv
    

def generate_password():
    MAX_LEN = 14

    DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] 
    LOCASE_CHARACTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 
                        'i', 'j', 'k', 'm', 'n', 'o', 'p', 'q', 
                        'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 
                        'z'] 

    UPCASE_CHARACTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 
                        'I', 'J', 'K', 'M', 'N', 'O', 'P', 'Q', 
                        'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 
                        'Z'] 

    SYMBOLS = ['@', '#', '$', '%', '=', ':', '?', '.', '/', '|', '~', '>', 
            '*', '(', ')', '<'] 

    COMBINED_LIST = DIGITS + UPCASE_CHARACTERS + LOCASE_CHARACTERS + SYMBOLS 

    rand_digit = random.choice(DIGITS) 
    rand_upper = random.choice(UPCASE_CHARACTERS) 
    rand_lower = random.choice(LOCASE_CHARACTERS) 
    rand_symbol = random.choice(SYMBOLS) 

    temp_pass = rand_digit + rand_upper + rand_lower + rand_symbol 

    for x in range(MAX_LEN - 4): 
        temp_pass = temp_pass + random.choice(COMBINED_LIST) 
        temp_pass_list = array.array('u', temp_pass) 
        random.shuffle(temp_pass_list) 
        
    password = "" 
    for x in temp_pass_list: 
            password = password + x 
            
    return password

if __name__ == '__main__':
    VaultApp().run()
