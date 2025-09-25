import os
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy.sql import func
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

load_dotenv()
app = Flask(__name__)

# --- CONFIGURAÇÕES ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///local_test.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, faça o login para acessar esta página."
login_manager.login_message_category = "info"

# --- MODELO DO BANCO DE DADOS (com os novos campos) ---
class Registro(db.Model):
    __tablename__ = 'registros'
    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    valor_quitado = db.Column(db.Float, nullable=False)
    data_quitacao = db.Column(db.String(10), nullable=False)
    supervisor = db.Column(db.String(100), nullable=False)
    vendedor = db.Column(db.String(100), nullable=False)
    investidor = db.Column(db.String(100), nullable=False)
    percentual_investidor = db.Column(db.Integer, nullable=False)
    percentual_comissao = db.Column(db.Integer, nullable=False)
    # --- CAMPOS ANTIGOS/INFORMATIVOS ---
    investidor_fora = db.Column(db.Boolean, default=False, nullable=False)
    criado_em = db.Column(db.DateTime(timezone=True), server_default=func.now())
    # --- NOVOS CAMPOS PARA O CÁLCULO ---
    valor_contrato = db.Column(db.Float, nullable=True) # Valor da receita
    custo_produto = db.Column(db.Float, nullable=True)  # Custo do produto (antigo campo 'produto')
    # --- CAMPO CALCULADO ---
    liquido_empresa = db.Column(db.Float, nullable=False)

# --- MODELO DE USUÁRIO (em memória) ---
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

admin_user = User(id='1', username=os.environ.get('ADMIN_USERNAME'), password_hash=os.environ.get('ADMIN_PASSWORD_HASH'))

@login_manager.user_loader
def load_user(user_id):
    if user_id == '1': return admin_user
    return None

with app.app_context():
    db.create_all()

# --- ROTAS DE AUTENTICAÇÃO (sem alteração) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
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

# --- ROTAS DA APLICAÇÃO ---
@app.route('/', methods=('GET', 'POST'))
@login_required
def index():
    if request.method == 'POST':
        # --- NOVA LÓGICA DE CÁLCULO ---
        valor_contrato = float(request.form.get('valor_contrato', 0))
        custo_produto = float(request.form.get('custo_produto', 0))
        percentual_comissao = int(request.form.get('percentual_comissao', 0))
        
        valor_comissao = valor_contrato * (percentual_comissao / 100)
        liquido_empresa = valor_contrato - valor_comissao - custo_produto
        # --- FIM DA NOVA LÓGICA ---

        novo_registro = Registro(
            # --- Novos campos ---
            valor_contrato=valor_contrato,
            custo_produto=custo_produto,
            liquido_empresa=liquido_empresa,
            # --- Campos antigos (agora informativos) ---
            nome_cliente=request.form['nome_cliente'],
            cpf=request.form['cpf'],
            valor_quitado=float(request.form.get('valor_quitado', 0)),
            data_quitacao=request.form['data_quitacao'],
            supervisor=request.form['supervisor'],
            vendedor=request.form['vendedor'],
            investidor=request.form['investidor'],
            percentual_investidor=int(request.form.get('percentual_investidor', 0)),
            percentual_comissao=percentual_comissao,
            investidor_fora='investidor_fora' in request.form
        )
        db.session.add(novo_registro)
        db.session.commit()
        return redirect(url_for('registros'))
    return render_template('index.html')

@app.route('/registros')
@login_required
def registros():
    search_query = request.args.get('q')
    base_query = Registro.query
    if search_query:
        search_pattern = f"%{search_query}%"
        registros_db = base_query.filter(
            or_(
                Registro.nome_cliente.ilike(search_pattern),
                Registro.cpf.ilike(search_pattern),
                Registro.vendedor.ilike(search_pattern),
                Registro.supervisor.ilike(search_pattern),
                Registro.investidor.ilike(search_pattern)
            )
        ).order_by(Registro.criado_em.desc()).all()
    else:
        registros_db = base_query.order_by(Registro.criado_em.desc()).all()
    return render_template('registros.html', registros=registros_db, search_query=search_query)