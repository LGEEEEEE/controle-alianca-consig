import os
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from dotenv import load_dotenv # Nova importação
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user # Novas importações
from werkzeug.security import check_password_hash # Nova importação

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///local_test.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- CONFIGURAÇÃO DO FLASK-LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redireciona para a rota 'login' se o usuário não estiver logado
login_manager.login_message = "Por favor, faça o login para acessar esta página."
login_manager.login_message_category = "info"

# --- MODELO DO BANCO DE DADOS (Registros) ---
class Registro(db.Model):
    # ... (seu modelo de Registro continua igualzinho)
    __tablename__ = 'registros'
    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(150), nullable=False)
    # ... (resto dos campos)
    cpf = db.Column(db.String(14), nullable=False)
    valor_quitado = db.Column(db.Float, nullable=False)
    data_quitacao = db.Column(db.String(10), nullable=False)
    supervisor = db.Column(db.String(100), nullable=False)
    vendedor = db.Column(db.String(100), nullable=False)
    investidor = db.Column(db.String(100), nullable=False)
    percentual_investidor = db.Column(db.Integer, nullable=False)
    percentual_comissao = db.Column(db.Integer, nullable=False)
    produto = db.Column(db.String(100), nullable=False)
    investidor_fora = db.Column(db.Boolean, default=False, nullable=False)
    liquido_empresa = db.Column(db.Float, nullable=False)
    criado_em = db.Column(db.DateTime(timezone=True), server_default=func.now())

# --- MODELO DE USUÁRIO (em memória, sem banco de dados) ---
# Como só temos um usuário, não precisamos de uma tabela para ele.
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Cria nosso único usuário a partir das variáveis de ambiente
admin_user = User(
    id='1', 
    username=os.environ.get('ADMIN_USERNAME'), 
    password_hash=os.environ.get('ADMIN_PASSWORD_HASH')
)

@login_manager.user_loader
def load_user(user_id):
    # O Flask-Login usa isso para recarregar o objeto do usuário a partir do ID armazenado na sessão
    if user_id == '1':
        return admin_user
    return None

with app.app_context():
    db.create_all()

# --- ROTAS DE AUTENTICAÇÃO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == admin_user.username and admin_user.check_password(password):
            login_user(admin_user, remember=True)
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect(url_for('login'))

# --- ROTAS DA APLICAÇÃO (AGORA PROTEGIDAS) ---
@app.route('/', methods=('GET', 'POST'))
@login_required # <-- Adicionamos o protetor aqui!
def index():
    # ... (o código da sua rota 'index' continua o mesmo)
    if request.method == 'POST':
        # ... (lógica de cálculo e inserção)
        valor_quitado = float(request.form['valor_quitado'])
        percentual_investidor = int(request.form['percentual_investidor'])
        percentual_comissao = int(request.form['percentual_comissao'])
        investidor_fora = 'investidor_fora' in request.form
        custo_investidor = valor_quitado * (percentual_investidor / 100)
        base_calculo_comissao = valor_quitado - custo_investidor
        valor_comissao = base_calculo_comissao * (percentual_comissao / 100)
        custo_investidor_fora = valor_quitado * 0.045 if investidor_fora else 0
        liquido_empresa = valor_quitado - custo_investidor - valor_comissao - custo_investidor_fora
        novo_registro = Registro(nome_cliente=request.form['nome_cliente'], cpf=request.form['cpf'], valor_quitado=valor_quitado, data_quitacao=request.form['data_quitacao'], supervisor=request.form['supervisor'], vendedor=request.form['vendedor'], investidor=request.form['investidor'], percentual_investidor=percentual_investidor, percentual_comissao=percentual_comissao, produto=request.form['produto'], investidor_fora=investidor_fora, liquido_empresa=liquido_empresa)
        db.session.add(novo_registro)
        db.session.commit()
        return redirect(url_for('registros'))
    return render_template('index.html')

@app.route('/registros')
@login_required # <-- E aqui também!
def registros():
    registros_db = Registro.query.order_by(Registro.criado_em.desc()).all()
    return render_template('registros.html', registros=registros_db)